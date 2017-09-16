
from contextlib import contextmanager
import os
from tempfile import TemporaryFile

import pytest

from ptongue import Session, GemObject
from reahl.component.shelltools import Executable


class Stone:
   def start(self):
       pass
   def stop(self):
       pass
   def is_started(self):
       return False

class NetLdi:
   def start(self, guest_mode=True):
       pass
   def stop(self):
       pass


class NetLDI():
    def __init__(self, guest_mode=True):
        self.start_args = ['-g'] if guest_mode else []
        self.start_netldi = Executable('startnetldi')
        self.stop_args = []
        self.stop_netldi = Executable('stopnetldi')

    def check_output_contains(self, out, expected_phrase):
        return True if len([line for line in out if line.contains(expected_phrase)]) > 0 else False

    def start(self):
        with TemporaryFile(mode='w+') as out:
            with open(os.devnull, 'w') as DEVNULL:
                self.start_netldi.check_call(self.start_args, stdout=out, stderr=DEVNULL)

    def stop(self):
        self.stop_netldi.check_call(self.stop_args)


@pytest.fixture(scope="session")
def netldi_guestmode_fixture():
    netldi = NetLDI(guest_mode=True)
    netldi.start()
    yield netldi
    netldi.stop()


def test_login_captive_os_user(netldi_guestmode_fixture):
    session = Session('DataCurator', 'swordfish')
    assert session.is_logged_in

    session.log_out()
    assert not session.is_logged_in


def test_login_os_user(netldi_guestmode_fixture):
    session = Session('DataCurator', 'swordfish', host_username='vagrant', host_password='vagrant')
    assert session.is_logged_in

    session.log_out()
    assert not session.is_logged_in


def test_resolve_string_symbol(netldi_guestmode_fixture):
    session = Session('DataCurator', 'swordfish')
    try:
        nil = session.resolve_symbol('nil') 
        assert isinstance(nil, GemObject)
        assert nil.oop == 20
    finally:
        session.log_out()

     
def test_resolve_symbol_object(netldi_guestmode_fixture):
    session = Session('DataCurator', 'swordfish')
    try:
        nil_symbol = session.new_symbol('nil')
        assert isinstance(nil_symbol, GemObject)
        nil = session.resolve_symbol(nil_symbol) 
        assert isinstance(nil, GemObject)
        assert nil is GemObject
        assert nil.oop == 20
    finally:
        session.log_out()


def test_basic_perform_returns_value(netldi_guestmode_fixture):
    session = Session('DataCurator', 'swordfish')
    try:
        date_class = session.resolve_symbol('Date')
        returned_object = date_class.perform('yourself')
        assert date_class.oop == returned_object.oop
    finally:
        session.log_out()
    

def test_transactions():
    pass


