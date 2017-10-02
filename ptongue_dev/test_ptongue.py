
from contextlib import contextmanager

import pytest

from ptongue.gemproxy import Session, GemObject, GemstoneError
from ptongue.gemstonecontrol import GemstoneService, NetLDI, Stone

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
       session.begin()
       yield session
    finally:
       session.abort()
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


def test_execute(session):
    date_class = session.execute('^Date yourself')
    date_class_resolved = session.resolve_symbol('Date')
    assert date_class.oop == date_class_resolved.oop


def test_execute_in_context(session):
    date_class_resolved = session.resolve_symbol('Date')
    date_class = session.execute('^self yourself', context=date_class_resolved)
    assert date_class.oop == date_class_resolved.oop


def test_identity_of_objects_stay_same(session):
    # when returning GemObjects from perform
    date_class = session.resolve_symbol('Date')
    returned_object = date_class.perform('yourself')
    assert date_class is returned_object

    # when resolving the same thing twice
    another_date_class = session.resolve_symbol('Date')
    assert date_class is another_date_class

    # when creating the same symbol
    my_symbol = session.new_symbol('my_symbol')
    my_symbol_again = session.new_symbol('my_symbol')
    assert my_symbol is my_symbol_again


def test_translating_booleans_to_python(session):
    true = session.resolve_symbol('true').to_py
    assert true is True
    false = session.resolve_symbol('false').to_py
    assert false is False


def test_translating_integers_to_python(session):
    number = session.execute('^123').to_py
    assert number is 123


def test_translating_nil_to_python(session):
    nil_py = session.resolve_symbol('nil').to_py
    assert nil_py is None


def test_transactions(session):
    some_object = session.resolve_symbol('Date')
    my_symbol = session.new_symbol('my_symbol')
    user_globals = session.resolve_symbol('UserGlobals')

    user_globals.perform('at:put:', my_symbol, some_object) 
    assert user_globals.perform('includesKey:', my_symbol).to_py
    session.abort()
    assert not user_globals.perform('includesKey:', my_symbol).to_py

    try:
       user_globals.perform('at:put:', my_symbol, some_object) 
       assert user_globals.perform('includesKey:', my_symbol).to_py
       session.commit()
       session.abort()
       assert user_globals.perform('includesKey:', my_symbol).to_py
    finally:
       user_globals.perform('removeKey:', my_symbol) 
       session.commit()





