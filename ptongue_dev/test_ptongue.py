
from contextlib import contextmanager
import os
from tempfile import TemporaryFile

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


@contextmanager
def NetLDI(guest_mode=True):
    start_args = ['-g'] if guest_mode else []
    start_netldi = Executable('startnetldi')
    stop_args = []
    stop_netldi = Executable('stopnetldi')

    def check_output_contains(expected_phrase):
        return True if len([line for line in out if line.contains(expected_phrase)]) > 0 else False

    with TemporaryFile(mode='w+') as out:
        with open(os.devnull, 'w') as DEVNULL:
            start_netldi.check_call(start_args, stdout=out, stderr=DEVNULL)
            started = check_output_contains('has been started')
            started_elsewhere = check_output_contains('is already running')
    try:
        yield
    finally:
        if started and not started_elsewhere:
            stop_netldi.check_call(stop_args)


def test_login_captive_os_user():
    with NetLDI():
        session = Session('DataCurator', 'swordfish')
        assert session.is_logged_in

        session.log_out()
        assert not session.is_logged_in


def test_login_os_user():
    session = Session('DataCurator', 'swordfish', host_username='vagrant', host_password='vagrant')
    assert session.is_logged_in

    session.log_out()
    assert not session.is_logged_in


def test_resolve_string_symbol():
    session = Session('DataCurator', 'swordfish')
    try:
        nil = session.resolve_symbol('nil') 
        assert isinstance(nil, GemObject)
        assert nil.oop == 20
    finally:
        session.log_out()

     
def test_resolve_symbol_object():
    session = Session('DataCurator', 'swordfish')
    try:
        nil_symbol = session.new_symbol('nil')
        assert isinstance(nil_symbol, GemObject)
        nil = session.resolve_symbol(nil_symbol) 
        assert isinstance(nil, GemObject)
        assert nil.oop == 20
    finally:
        session.log_out()


def test_basic_perform_returns_value():
    session = Session('DataCurator', 'swordfish')
    try:
        date_class = session.resolve_symbol('Date')
        return_object = date_class.perform('yourself')
        assert date_class.oop == returned_object.oop
    finally:
        session.log_out()
    

def test_transactions():
    pass


