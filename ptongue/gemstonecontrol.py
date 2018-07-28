import os
import re
from tempfile import TemporaryFile
from contextlib import contextmanager

from reahl.component.shelltools import Executable

class GemstoneInstallation(object):
    @classmethod
    def from_install_directory(cls, gemstone):
        version_match = re.match('/opt/gemstone/GemStone64Bit(\d+\.\d+\.\d+)-x86_64.Linux', gemstone)
        assert version_match, 'Cannot parse a gemstone version from "%s"' % gemstone
        version = version_match.group(1)
        return GemstoneInstallation(os.environ['GEMSTONE'], version)
        
    def __init__(self, install_directory, version):
        self.install_directory = install_directory
        self.version = version

    @property
    def environ(self):
        return {'PATH': os.path.join(self.install_directory, 'bin'),
                'GEMSTONE': self.install_directory}
    
    @contextmanager
    def environment_setup(self):
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
        with self.gemstone_installation.environment_setup(), TemporaryFile(mode='w+') as out, open(os.devnull, 'w') as DEVNULL:
            self.start_executable.check_call(self.start_args, stdout=out, stderr=DEVNULL)
            assert not self.check_output_contains(out, 'already running'), 'Another instance of %s is already running, and shouldn\'t be' % self.service_name
            assert self.check_output_contains(out, self.start_output_check)

    def stop(self):
        with self.gemstone_installation.environment_setup(), TemporaryFile(mode='w+') as out, open(os.devnull, 'w') as DEVNULL:
            self.stop_executable.check_call(self.stop_args, stdout=out, stderr=DEVNULL)
            assert self.check_output_contains(out, self.stop_output_check)


class NetLDI(GemstoneService):
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
