
from contextlib import contextmanager

import pytest

from ptongue.gemproxy import Session, GemObject, GemstoneError, NotYetImplemented, InvalidSession, GemstoneApiError
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


@pytest.fixture
def invalid_session(guestmode_netldi):
    session = Session('DataCurator', 'swordfish')
    session.log_out()
    yield session


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
    py_int = int('9' * session.initial_fetch_size)
    converted_positive_int = session.execute('^{}'.format(py_int))
    converted_negative_int = session.execute('^-{}'.format(py_int))
    assert py_int == converted_positive_int.to_py
    assert -py_int == converted_negative_int.to_py


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
    assert session.execute('self class == Boolean', context=converted_true).oop == oop_true
    assert session.execute('self class == Boolean', context=converted_false).oop == oop_true
    assert session.execute('self == true', context=converted_true).oop == oop_true
    assert session.execute('self == false', context=converted_false).oop == oop_true


def test_translating_py_int_to_gem_small_integers(session, oop_true):
    py_zero = 0
    py_positive_int = 123
    converted_zero = session.from_py(py_zero)
    converted_positive_int = session.from_py(py_positive_int)
    converted_negative_int = session.from_py(-py_positive_int)
    assert session.execute('self class == SmallInteger', context=converted_zero).oop == oop_true
    assert session.execute('self class == SmallInteger', context=converted_positive_int).oop == oop_true    
    assert session.execute('self class == SmallInteger', context=converted_negative_int).oop == oop_true
    assert session.execute('self == {}'.format(py_zero), context=converted_zero).oop == oop_true
    assert session.execute('self == {}'.format(py_positive_int), context=converted_positive_int).oop == oop_true
    assert session.execute('self == {}'.format(-py_positive_int), context=converted_negative_int).oop == oop_true


def test_translating_py_int_to_gem_large_integers(session, oop_true):
    py_positive_int = int('9' * session.initial_fetch_size)
    converted_positive_int = session.from_py(py_positive_int)
    converted_negative_int = session.from_py(-py_positive_int)
    assert session.execute('self class == LargeInteger', context=converted_positive_int).oop == oop_true
    assert session.execute('self class == LargeInteger', context=converted_negative_int).oop == oop_true
    assert session.execute('self = {}'.format(py_positive_int), context=converted_positive_int).oop == oop_true
    assert session.execute('self = {}'.format(-py_positive_int), context=converted_negative_int).oop == oop_true


def test_translating_py_float_to_gem_small_double(session, oop_true):
    py_positive_float = 123.123
    converted_positive_float = session.from_py(py_positive_float)
    converted_negative_float = session.from_py(-py_positive_float)
    assert session.execute('self class == SmallDouble', context=converted_positive_float).oop == oop_true
    assert session.execute('self class == SmallDouble', context=converted_negative_float).oop == oop_true
    assert session.execute('self = {}'.format(py_positive_float), context=converted_positive_float).oop == oop_true
    assert session.execute('self = {}'.format(-py_positive_float), context=converted_negative_float).oop == oop_true


def test_translating_py_float_to_gem_float(session, oop_true):
    py_positive_float_string = ('9' * 40) + '.' + ('9' * 40)
    py_positive_float = float(py_positive_float_string)
    converted_positive_float = session.from_py(py_positive_float)
    converted_negative_float = session.from_py(-py_positive_float)
    assert session.execute('self class == Float', context=converted_positive_float).oop == oop_true
    assert session.execute('self class == Float', context=converted_negative_float).oop == oop_true
    assert session.execute('self = {}'.format(py_positive_float_string), context=converted_positive_float).oop == oop_true
    assert session.execute('self = -{}'.format(py_positive_float_string), context=converted_negative_float).oop == oop_true


def test_translating_python_string_to_gemstone(session, oop_true):
    py_str = 'šamas'
    converted_str = session.from_py(py_str)
    assert session.execute('self class == Unicode16', context=converted_str).oop == oop_true
    assert session.execute("self = (((Unicode16 new) add:( Character codePoint: 0353); yourself), 'amas')", context=converted_str).oop == oop_true


def test_session_init_exception(guestmode_netldi):
    try:
        broken_session = Session('DataCurator', 'wrong_password')
        assert False, 'expected an exception'
    except GemstoneError:
        pass


def test_session_abort_exception(invalid_session):
    try:
        invalid_session.abort()
        assert False, 'expected an exception'
    except GemstoneError:
        pass


def test_session_begin_exception(invalid_session):
    try:
        invalid_session.begin()
        assert False, 'expected an exception'
    except GemstoneError:
        pass


def test_session_commit_exception(invalid_session):
    try:
        invalid_session.commit()
        assert False, 'expected an exception'
    except GemstoneError:
        pass


def test_session_is_remote_exception(invalid_session):
    try:
        broken_py_bool = invalid_session.is_remote
        assert False, 'expected an exception'
    except InvalidSession:
        pass


def test_session_from_py_exception(session):
    try:
        py_not_implemented_type = []
        converted_not_implemented_type = session.from_py(py_not_implemented_type)
        assert False, 'expected an exception'
    except NotYetImplemented:
        pass


def test_session_py_to_string_exception(invalid_session):
    try:
        broken_object = invalid_session.py_to_string_('2')
        assert False, 'expected an exception'
    except GemstoneError:
        pass


def test_session_py_to_float_exception(invalid_session):
    try:
        py_float = float('9' * 40 + '.' + '99')
        broken_object = invalid_session.py_to_float_(py_float)
        assert False, 'expected an exception'
    except GemstoneError:
        pass


def test_session_execute_exception(session):
    try:
        broken_object = session.execute('hallo')
        assert False, 'expected an exception'
    except GemstoneError:
        pass


def test_session_new_symbol_exception(session):
    try:
        py_string = 'a' * 2000
        broken_symbol = session.new_symbol(py_string)
        assert False, 'expected an exception'
    except GemstoneError:
        pass


def test_session_resolve_symbol_exception(session):
    try:
        broken_symbol = session.resolve_symbol(2)
        assert False, 'expected an exception'
    except AssertionError:
        pass

    try:
        py_string = 'a' * 2000
        broken_symbol = session.resolve_symbol(py_string)
        assert False, 'expected an exception'
    except GemstoneError:
        pass


def test_session_log_out_exception(invalid_session):
    try:
        invalid_session.log_out()
        assert False, 'expected an exception'
    except GemstoneError:
        pass


def test_gem_object_to_py_exception(session):
    try:
        date_symbol = session.resolve_symbol('Date')
        py_not_implemented = date_symbol.to_py
        assert False, 'expected an exception'
    except NotYetImplemented:
        pass


def test_gem_object_small_integer_to_py_exception(session):
    try:
        date_symbol = session.resolve_symbol('Date')
        broken_py_int = date_symbol._small_integer_to_py()
        assert False, 'expected an exception'
    except GemstoneApiError:
        pass


def test_gem_object_float_to_py_exception(session):
    try:
        date_symbol = session.resolve_symbol('Date')
        broken_py_float = date_symbol._float_to_py()
        assert False, 'expected an exception'
    except GemstoneError:
        pass


def test_gem_object_string_to_py_exception(session):
    try:
        date_symbol = session.resolve_symbol('Date')
        broken_py_str = date_symbol._string_to_py()
        assert False, 'expected an exception'
    except GemstoneError:
        pass


# def test_gem_object_latin1_to_py_exception(guestmode_netldi):
#     try:
#         session = Session('DataCurator', 'swordfish')
#         date_symbol = session.resolve_symbol('Date')
#         session.log_out()
#         broken_py_str = date_symbol._latin1_to_py()
#         print(py_str)
#         assert False, 'expected an exception'
#     except GemstoneError:
#         pass


def test_gem_object_gemstone_class_exception(guestmode_netldi):
    try:
        session = Session('DataCurator', 'swordfish')
        date_symbol = session.resolve_symbol('Date')
        session.log_out()
        broken_class = date_symbol.gemstone_class()
        assert False, 'expected an exception'
    except GemstoneError:
        pass


def test_gem_object_is_kind_of_exception(session):
    try:
        date_symbol = session.resolve_symbol('Date')
        converted_number = session.execute('2')
        broken_py_bool = date_symbol.is_kind_of(converted_number)
        assert False, 'expected an exception'
    except GemstoneError:
        pass


def test_gem_object_perform_exception(session):
    try:
        date_symbol = session.resolve_symbol('Date')
        broken_object = date_symbol.perform('asFloat')
        assert False, 'expected an exception'
    except GemstoneError:
        pass


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