
from contextlib import contextmanager
import os
from tempfile import TemporaryFile

import pytest

from ptongue import Session, GemObject, GemstoneError
from reahl.component.shelltools import Executable


class GemstoneService(object):
    def __init__(self, service_name, start_command, stop_command, start_args=[], stop_args=[],
                 start_output_check='', stop_output_check=''):
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
        with TemporaryFile(mode='w+') as out:
            with open(os.devnull, 'w') as DEVNULL:
                self.start_executable.check_call(self.start_args, stdout=out, stderr=DEVNULL)
                assert not self.check_output_contains(out, 'already running'), 'Another instance of %s is already running, and shouldn\'t be' % self.service_name
                assert self.check_output_contains(out, self.start_output_check)

    def stop(self):
        with TemporaryFile(mode='w+') as out:
            with open(os.devnull, 'w') as DEVNULL:
                self.stop_executable.check_call(self.stop_args, stdout=out, stderr=DEVNULL)
                assert self.check_output_contains(out, self.stop_output_check)


class NetLDI(GemstoneService):
    def __init__(self, guest_mode=True):
        start_args = ['-g'] if guest_mode else []
        super(NetLDI, self).__init__('netLDI',
                                     'startnetldi', 'stopnetldi',
                                     start_args=start_args,
                                     start_output_check='GemStone server \'gs64ldi\' has been started, process ',
                                     stop_output_check='GemStone server \'gs64ldi\' has been stopped.',
                                     )


class Stone(GemstoneService):
    def __init__(self):
        stone_name = 'gs64stone'
        username = 'DataCurator'
        password = 'swordfish'
        super(Stone, self).__init__('stone',
                                    'startstone', 'stopstone',
                                    start_args=[stone_name], stop_args=[stone_name, username, password],
                                    start_output_check='GemStone server gs64stone has been started, process ',
                                    stop_output_check='Stone repository monitor \'gs64stone\' has been stopped.',
                                    )


@pytest.fixture(scope="module")
def stone_fixture():
    stone = Stone()
    stone.start()
    try:
       yield stone
    finally:
       stone.stop()

@contextmanager
def running_netldi(guest_mode=False):
    netldi = NetLDI(guest_mode=guest_mode)
    netldi.start()
    try:
       yield netldi
    finally:
       netldi.stop()

@pytest.fixture
def guestmode_netldi(stone_fixture):
    with running_netldi(guest_mode=True) as netldi:
       yield netldi

@pytest.fixture
def session(guestmode_netldi):
    session = Session('DataCurator', 'swordfish')
    try:
       yield session
    finally:
       session.log_out()


def test_login_captive_os_user(guestmode_netldi):
    session = Session('DataCurator', 'swordfish')
    assert session.is_logged_in

    session.log_out()
    assert not session.is_logged_in


def test_login_os_user(stone_fixture):
    with running_netldi(guest_mode=False):
        try:
            Session('DataCurator', 'swordfish', host_username='vagrant', host_password='wrongvagrant')
        except GemstoneError as e:
            # TODO: this can be done better : with expected() from reahl-tofu
            assert 'Password validation failed for user vagrant' in e.message
            
        session = Session('DataCurator', 'swordfish', host_username='vagrant', host_password='vagrant')
        assert session.is_logged_in

        session.log_out()
        assert not session.is_logged_in


def test_resolve_string_symbol(session):
    nil = session.resolve_symbol('nil') 
    assert isinstance(nil, GemObject)
    assert nil.oop == 20
    assert nil.is_nil


def test_resolve_symbol_object(session):
    nil_symbol = session.new_symbol('nil')
    assert isinstance(nil_symbol, GemObject)
    assert nil_symbol.is_symbol
    nil = session.resolve_symbol(nil_symbol) 
    assert isinstance(nil, GemObject)
    assert nil.oop == 20


def test_basic_perform_returns_value(session):
    date_class = session.resolve_symbol('Date')
    returned_object = date_class.perform('yourself')
    assert date_class.oop == returned_object.oop


def test_translating_booleans_to_python(session):
    true = session.resolve_symbol('true').to_py
    assert true is True
    false = session.resolve_symbol('false').to_py
    assert false is False


def test_transactions(session):
    some_object = session.resolve_symbol('Date')
    my_symbol = session.new_symbol('my_symbol')
    user_globals = session.resolve_symbol('UserGlobals')

    user_globals.perform('at:put:', my_symbol, some_object) 
    assert user_globals.perform('includesKey:', my_symbol).to_py
    session.abort()
    assert not user_globals.perform('includesKey:', my_symbol).to_py

    user_globals.perform('at:put:', my_symbol, some_object) 
    assert user_globals.perform('includesKey:', my_symbol).to_py
    session.commit()
    session.abort()
    assert user_globals.perform('includesKey:', my_symbol).to_py



