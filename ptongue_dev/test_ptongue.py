
from contextlib import contextmanager

import pytest

from ptongue.gemproxy import Session, GemObject, GemstoneError, NotYetImplemented
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


@pytest.fixture
def oop_true(session):
    yield session.resolve_symbol('true').oop


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


def test_translating_floats_to_python(session):
    number = session.execute('^123.123').to_py
    assert number == 123.123


def test_translating_nil_to_python(session):
    nil_py = session.resolve_symbol('nil').to_py
    assert nil_py is None


def test_translating_unicode_strings_to_python(session):
    unicode_string = 'šamas'
    string = session.execute("((Unicode16 new) add:( Character codePoint: 0353); yourself), 'amas'")
    assert string.to_py == unicode_string


@pytest.mark.parametrize('multiplier, plus',[
    (1, 0),
    (2, 0),
    (1, 1),
    (0, 0)
    ])
def test_translating_strings_to_python(session, multiplier, plus):
    unicode_string = 'a' * (session.initial_fetch_size * multiplier + plus)
    string = session.execute("'{}'".format(unicode_string))
    assert string.to_py == unicode_string


def test_translating_py_none_to_gem_nil(session, oop_true):
    converted_none = session.from_py(None)
    assert converted_none.gemstone_class().perform('name').to_py == 'UndefinedObject'
    assert session.execute('self == nil', context=converted_none).oop == oop_true


def test_translating_py_bool_to_gem_boolean(session, oop_true):
    converted_true = session.from_py(True)
    converted_false = session.from_py(False)
    # converted_true_class = converted_true.gemstone_class().perform('name')
    # converted_false_class = converted_false.gemstone_class().perform('name')
    # assert session.execute("self asString == 'Boolean'", context=converted_true_class).oop == oop_true    
    # assert session.execute("self asString == 'Boolean'", context=converted_false_class).oop == oop_true
    assert converted_true.gemstone_class().perform('name').to_py == 'Boolean'
    assert converted_false.gemstone_class().perform('name').to_py == 'Boolean'
    assert session.execute('self == true', context=converted_true).oop == oop_true
    assert session.execute('self == false', context=converted_false).oop == oop_true


def test_translating_py_int_to_gem_small_integers(session, oop_true):
    py_zero = 0
    py_positive_int = 123
    converted_zero = session.from_py(py_zero)
    converted_positive_int = session.from_py(py_positive_int)
    converted_negative_int = session.from_py(-py_positive_int)
    # converted_zero_class = converted_zero.gemstone_class().perform('name')
    # converted_positive_int_class = converted_positive_int.gemstone_class().perform('name')
    # converted_negative_int_class = converted_negative_int.gemstone_class().perform('name')
    # assert session.execute("self asString == 'SmallInteger'", context=converted_zero_class).oop == oop_true
    # assert session.execute("self asString == 'SmallInteger'", context=converted_positive_int_class).oop == oop_true    
    # assert session.execute("self asString == 'SmallInteger'", context=converted_negative_int_class).oop == oop_true
    assert converted_zero.gemstone_class().perform('name').to_py == 'SmallInteger'
    assert converted_positive_int.gemstone_class().perform('name').to_py == 'SmallInteger'
    assert converted_negative_int.gemstone_class().perform('name').to_py == 'SmallInteger'
    # assert converted_positive_int.to_py == py_positive_int
    # assert converted_negative_int.to_py == -py_positive_int
    assert session.execute('self == {}'.format(py_zero), context=converted_zero).oop == oop_true
    assert session.execute('self == {}'.format(py_positive_int), context=converted_positive_int).oop == oop_true
    assert session.execute('self == {}'.format(-py_positive_int), context=converted_negative_int).oop == oop_true


def test_translating_py_int_to_gem_large_integers(session, oop_true):
    py_positive_int = int('9' * session.initial_fetch_size)
    converted_positive_int = session.from_py(py_positive_int)
    converted_negative_int = session.from_py(-py_positive_int)
    assert converted_positive_int.gemstone_class().perform('name').to_py == 'LargeInteger'
    assert converted_negative_int.gemstone_class().perform('name').to_py == 'LargeInteger'
    assert converted_positive_int.to_py == py_positive_int
    assert converted_negative_int.to_py == -py_positive_int
    # assert session.execute('self == {}'.format(py_positive_int), context=converted_positive_int).oop == oop_true
    # assert session.execute('self == {}'.format(-py_positive_int), context=converted_negative_int).oop == oop_true


def test_translating_py_float_to_gem_small_double(session):
    py_positive_float = 123.123
    converted_positive_float = session.from_py(py_positive_float)
    converted_negative_float = session.from_py(-py_positive_float)
    assert converted_positive_float.gemstone_class().perform('name').to_py == 'SmallDouble'
    assert converted_negative_float.gemstone_class().perform('name').to_py == 'SmallDouble'
    assert converted_positive_float.to_py == py_positive_float
    assert converted_negative_float.to_py == -py_positive_float
    # assert session.execute('self == {}'.format(py_positive_float), context=converted_positive_float).oop == oop_true
    # assert session.execute('self == {}'.format(-py_positive_float), context=converted_negative_float).oop == oop_true


def test_translating_py_float_to_gem_float(session):
    py_positive_float = float(('9' * 40) + '.' + ('9' * 40))
    converted_positive_float = session.from_py(py_positive_float)
    converted_negative_float = session.from_py(-py_positive_float)
    assert converted_positive_float.gemstone_class().perform('name').to_py == 'Float'
    assert converted_negative_float.gemstone_class().perform('name').to_py == 'Float'
    assert converted_positive_float.to_py == py_positive_float
    assert converted_negative_float.to_py == -py_positive_float


def test_translating_python_string_to_gemstone(session):
    py_str = 'šamas'
    converted_str = session.from_py(py_str)
    assert converted_str.gemstone_class().perform('name').to_py == 'Unicode16'
    assert converted_str.to_py == py_str


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





