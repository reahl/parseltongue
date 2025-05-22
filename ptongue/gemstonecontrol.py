# Copyright (C) 2025 Reahl Software Services (Pty) Ltd
# 
# This file is part of parseltongue.
#
# parseltongue is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# parseltongue is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with parseltongue.  If not, see <https://www.gnu.org/licenses/>.
"""
GemStone server process control
===============================

This module provides classes for managing GemStone/S 64 Bit database server 
processes and installations. It includes functionality to start and stop 
the Stone repository monitor and NetLDI network service, as well as to 
configure the environment for GemStone operations.

The programmatic control offered here is useful for automated testing,
application deployment, and system administration tasks.
"""
import os
import re
from tempfile import TemporaryFile
from contextlib import contextmanager

from reahl.component.shelltools import Executable

class GemstoneInstallation(object):
    """
    Represents a GemStone installation on the filesystem.
    
    This class provides utilities for working with a specific GemStone
    installation, including environment setup and version information.
    
    :param install_directory: Path to the GemStone installation directory
    :param version: Version of the GemStone installation
    """
    @classmethod
    def from_install_directory(cls, gemstone):
        """
        Create a GemstoneInstallation instance from an installation directory path.
        
        Parses the version from the directory name and creates a new installation
        instance with the appropriate parameters.
        
        :param gemstone: Path to the GemStone installation directory
        :return: A new GemstoneInstallation instance
        :raises AssertionError: If the version cannot be parsed from the directory path
        """
        version_match = re.match('/opt/gemstone/GemStone64Bit(\d+\.\d+\.\d+)-x86_64.Linux', gemstone)
        assert version_match, 'Cannot parse a gemstone version from "%s"' % gemstone
        version = version_match.group(1)
        return GemstoneInstallation(os.environ['GEMSTONE'], version)
        
    def __init__(self, install_directory, version):
        self.install_directory = install_directory
        self.version = version

    @property
    def environ(self):
        """
        Get environment variables needed for the GemStone installation.
        
        :return: Dictionary of environment variables with PATH and GEMSTONE set
        """
        return {'PATH': os.path.join(self.install_directory, 'bin'),
                'GEMSTONE': self.install_directory}
    
    @contextmanager
    def environment_setup(self):
        """
        Context manager for temporarily setting GemStone environment variables.
        
        Sets up the environment with the correct PATH and GEMSTONE variables for
        running GemStone commands, then restores the original environment when done.
        
        Usage:
            with gemstone_installation.environment_setup():
                # Run GemStone commands here
        """
        path = os.environ['PATH']
        gemstone = os.environ.get('GEMSTONE', None)
        os.environ['PATH'] = os.pathsep.join([self.environ['PATH'], path])
        os.environ['GEMSTONE'] = self.install_directory
        yield
        os.environ['PATH'] = path
        if gemstone:
            os.environ['GEMSTONE'] = gemstone
        else:
            del os.environ['GEMSTONE']

            
class GemstoneService(object):
    """
    Manages a GemStone service process.
    
    Provides functionality to start, stop, and monitor GemStone services
    such as Stone, NetLDI, and other server processes.
    
    :param service_name: Name of the service (e.g., 'stone', 'netldi')
    :param start_command: Command to start the service
    :param stop_command: Command to stop the service
    :param start_args: Arguments for the start command
    :param stop_args: Arguments for the stop command
    :param start_output_check: String to verify in output when starting
    :param stop_output_check: String to verify in output when stopping
    :param gemstone_installation: GemstoneInstallation instance or None to use default

    """
    def __init__(self, service_name, start_command, stop_command, start_args=[], stop_args=[],
                 start_output_check='', stop_output_check='',
                 gemstone_installation=None):
        self.gemstone_installation = gemstone_installation or GemstoneInstallation.from_install_directory(os.environ['GEMSTONE'])
        self.service_name = service_name
        self.start_args = start_args
        self.start_executable = Executable(start_command)
        self.stop_args = stop_args
        self.stop_executable = Executable(stop_command)
        self.start_output_check = start_output_check
        self.stop_output_check = stop_output_check

    def check_output_contains(self, temp_output_file, expected_phrase):
        temp_output_file.seek(0)
        output_lines = [line for line in temp_output_file]
        return True if len([line for line in output_lines if expected_phrase in line]) > 0 else False

    def start(self):
        """
        Start the GemStone service.
        
        Sets up the GemStone environment, executes the start command with
        appropriate arguments, and verifies the output contains expected messages.
        
        :raises AssertionError: If service is already running or start fails
        """
        with self.gemstone_installation.environment_setup(), TemporaryFile(mode='w+') as out, open(os.devnull, 'w') as DEVNULL:
            self.start_executable.check_call(self.start_args, stdout=out, stderr=DEVNULL)
            assert not self.check_output_contains(out, 'already running'), 'Another instance of %s is already running, and shouldn\'t be' % self.service_name
            assert self.check_output_contains(out, self.start_output_check)

    def stop(self):
        """
        Stop the GemStone service.
        
        Sets up the GemStone environment, executes the stop command with
        appropriate arguments, and verifies the output contains expected messages.
        
        :raises AssertionError: If stop fails or expected output is not found
        """
        with self.gemstone_installation.environment_setup(), TemporaryFile(mode='w+') as out, open(os.devnull, 'w') as DEVNULL:
            self.stop_executable.check_call(self.stop_args, stdout=out, stderr=DEVNULL)
            assert self.check_output_contains(out, self.stop_output_check)


class NetLDI(GemstoneService):
    """
    Manages a GemStone NetLDI (Network Long Distance Information) service.
  
    The NetLDI service is responsible for starting GemStone Gem processes
    on behalf of client applications.
    
    :param guest_mode: If True, start NetLDI with guest mode enabled (-g flag)
    :param gemstone_installation: GemstoneInstallation instance or None to use default
    """
    def __init__(self, guest_mode=True, gemstone_installation=None):
        start_args = ['-g'] if guest_mode else []
        super(NetLDI, self).__init__('netLDI',
                                     'startnetldi', 'stopnetldi',
                                     start_args=start_args,
                                     start_output_check='GemStone server \'gs64ldi\' has been started, process ',
                                     stop_output_check='GemStone server \'gs64ldi\' has been stopped.',
                                     gemstone_installation=gemstone_installation
                                     )


class Stone(GemstoneService):
    """
    Manages a GemStone Stone (repository monitor) service.
   
    The Stone process is the main database server that manages the repository
    and coordinates access to the database.

    Creates a Stone service for the default stone 'gs64stone' using
    standard DataCurator credentials.
    
    :param gemstone_installation: GemstoneInstallation instance or None to use default
    """
    def __init__(self, gemstone_installation=None):
        stone_name = 'gs64stone'
        username = 'DataCurator'
        password = 'swordfish'
        super(Stone, self).__init__('stone',
                                    'startstone', 'stopstone',
                                    start_args=[stone_name], stop_args=[stone_name, username, password],
                                    start_output_check='GemStone server gs64stone has been started, process ',
                                    stop_output_check='Stone repository monitor \'gs64stone\' has been stopped.',
                                    gemstone_installation=gemstone_installation
                                    )
