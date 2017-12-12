
from contextlib import contextmanager

import pytest

from ptongue.gemproxy import GemObject, GemstoneError, NotYetImplemented, InvalidSession, GemstoneApiError
from ptongue.gemproxymultithread import RPCSession as Session
from ptongue.gemstonecontrol import GemstoneService, NetLDI, Stone

#======================================================================================================================

class NoExceptionRaised(Exception):
    def __init__(self, expected):
        self.expected = expected
    def __str__(self):
        return '%s was expected' % self.expected

class NoException(Exception):
    pass

@contextmanager
def expected(exception, test=None):

    if test and not callable(test):
        test_regex = test
        def check_message(ex):
            assert test_regex in str(ex), \
                'Expected exception to match "%s", got "%s"' % (test_regex, str(ex))
        test = check_message

    if exception is NoException:
        yield
        return

    try:
        yield
    except exception as ex:
        if test:
            test(ex)
    else:
        raise NoExceptionRaised(exception)

#======================================================================================================================

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


#======================================================================================================================


#--[ logging in and out ]------------------------------------------------------------

def test_login_captive_os_user(guestmode_netldi):
    session = Session('DataCurator', 'swordfish')
    assert session.is_logged_in

    session.log_out()
    assert not session.is_logged_in

    with expected(GemstoneError, test='the userId/password combination is invalid or expired'):
        Session('DataCurator', 'wrong_password')

    with expected(GemstoneError, test='argument is not a valid GciSession pointer'):
        session.log_out()

        
def test_login_os_user(stone_fixture):
    with running_netldi(guest_mode=False):
        with expected(GemstoneError, test='Password validation failed for user vagrant'):
            Session('DataCurator', 'swordfish', host_username='vagrant', host_password='wrongvagrant')
            
        session = Session('DataCurator', 'swordfish', host_username='vagrant', host_password='vagrant')
        assert session.is_logged_in
        assert session.is_remote

        session.log_out()
        assert not session.is_logged_in

def test_session_is_remote_exception(invalid_session):
    with expected(InvalidSession):
        invalid_session.is_remote

        
#--[ getting a hold of objects and symbols ]------------------------------------------------------------
        
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

    py_string = 'a' * 2000
    with expected(GemstoneApiError):
        session.resolve_symbol(2)

    with expected(GemstoneError, test=''):
        session.resolve_symbol(py_string)

    py_string = 'a' * 2000
    with expected(GemstoneError, test='a ImproperOperation occurred (error 2402), Cannot create a Symbol'):
        session.new_symbol(py_string)

        
#--[ performing selectors and executing arbitrary code ]------------------------------------------------------------
        
def test_perform_returns_value(session):
    date_class = session.resolve_symbol('Date')
    returned_object = date_class.perform('yourself')
    assert date_class.oop == returned_object.oop


def test_perform_passing_args(session):
    some_symbol = session.new_symbol('some_symbol')
    gem_string = session.execute("'a string used as argument'")
    user_globals = session.resolve_symbol('UserGlobals')
    
    user_globals.perform('at:put:', some_symbol, gem_string)
    fetched_py_string = session.resolve_symbol('some_symbol')
    assert fetched_py_string.oop == gem_string.oop


def test_perform_with_gem_object(session):
    date_class = session.resolve_symbol('Date')
    as_string_symbol = session.new_symbol('asString')
    date_class.perform(as_string_symbol)

    as_string_unicode = session.execute("'asString'")
    with expected(GemstoneError, test='a ArgumentTypeError occurred (error 2094), for asString  expected a Symbol'):
        date_class.perform(as_string_unicode)

        
def test_perform_exception(session):
    date_class = session.resolve_symbol('Date')
    with expected(GemstoneError, test='a MessageNotUnderstood occurred (error 2010)'):
        date_class.perform('asFloat')

        
def test_execute(session):
    date_class = session.execute('Date')
    date_class_resolved = session.resolve_symbol('Date')
    assert date_class.oop == date_class_resolved.oop


def test_execute_with_gem_object(session):
    string_to_execute = session.execute("'Date'")
    date_class = session.execute(string_to_execute)
    date_class_resolved = session.resolve_symbol('Date')
    assert date_class.oop == date_class_resolved.oop
    
def test_execute_in_context(session):
    date_class = session.resolve_symbol('Date')
    returned = session.execute('^self yourself', context=date_class)
    assert returned.oop == date_class.oop

def test_session_execute_exception(session):
    with expected(GemstoneError, test='a CompileError occurred (error 1001), undefined symbol'):
        session.execute('invalid smalltalk code')

        
#--[ transaction handling ]------------------------------------------------------------

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

       
def test_session_transactional_exceptions(invalid_session):
    with expected(GemstoneError, test='argument is not a valid GciSession pointer'):
        invalid_session.abort()

    with expected(GemstoneError, test='argument is not a valid GciSession pointer'):
        invalid_session.begin()

    with expected(GemstoneError, test='argument is not a valid GciSession pointer'):
        invalid_session.commit()


#--[ miscellaneous ]------------------------------------------------------------
        
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

    
def test_raising_of_gemstone_exceptions(session, oop_true):
    rt_err_generic_error = 2318
    def check_error_details(e):
        assert session.execute('self class == SymbolDictionary', context=e.category).oop == oop_true
        assert session.execute('self class == GsProcess', context=e.context).oop == oop_true
        assert session.execute('self class == UserDefinedError', context=e.exception_obj).oop == oop_true
        assert session.execute('self class == UndefinedObject', context=e.args[0]).oop == oop_true
        assert e.number == rt_err_generic_error
        assert e.arg_count == 1
        assert e.is_fatal == False
        assert e.reason == ''
        assert e.message == 'a UserDefinedError occurred (error 2318), reason:halt, breaking intentionally'

    with expected(GemstoneError, test=check_error_details):
        session.execute("System error: 'breaking intentionally'")

        
#--[ special methods ]------------------------------------------------------------

def test_gemstone_class(session, oop_true):
    today = session.execute('Date today')

    date_class = today.gemstone_class()
    assert session.execute('self == Date', context=date_class).oop == oop_true

    
def test_gemstone_class_exception(guestmode_netldi):
    session = Session('DataCurator', 'swordfish')
    today = session.execute('Date today')
    session.log_out()
    
    with expected(GemstoneError, test='argument is not a valid GciSession pointer'):
        today.gemstone_class()
        
        
def test_is_kind_of(session, oop_true):
    boolean = session.resolve_symbol('Boolean')
    true = session.execute('true')
    assert true.is_kind_of(boolean)

    not_a_class = session.execute('2')
    with expected(GemstoneError, test='a ArgumentTypeError occurred (error 2094)'):
        true.is_kind_of(not_a_class)

        
#--[ translating: truthy values ]------------------------------------------------------------
        
@pytest.mark.parametrize('gem_value, expected_py_value',[
    ('true', True),
    ('false', False),
    ('nil', None)
    ])
def test_tranlating_truthy_objects_to_python(session, gem_value, expected_py_value):
    converted_value = session.resolve_symbol(gem_value).to_py
    assert converted_value is expected_py_value

@pytest.mark.parametrize('py_value, expected_gemstone_class, expected_gemstone_value', [
    (None, 'UndefinedObject', 'nil'),
    (True, 'Boolean', 'true'),
    (False, 'Boolean', 'false')
])
def test_translating_truthy_objects_to_gemstone(session, oop_true, py_value, expected_gemstone_class, expected_gemstone_value):
    converted_value = session.from_py(py_value)
    assert session.execute('self class == {}'.format(expected_gemstone_class), context=converted_value).oop == oop_true
    assert session.execute('self == {}'.format(expected_gemstone_value), context=converted_value).oop == oop_true

    
#--[ translating: numbers ]------------------------------------------------------------
    
INITIAL_FETCH_SIZE = 200 # TODO: when we can begine using our new Fixture stuff, this hard-code should
                         #       be replaced with session.initial_fetch_size
NUMBER_SCENARIOS = [
    ('{}', 0),
    ('{}', 123),
    ('{}', -123),
    
    ('{}', int('9' * INITIAL_FETCH_SIZE)),
    ('{}', -int('9' * INITIAL_FETCH_SIZE)),

    ('{}', 123.123),
    ('{}', -123.123),

    ('^{:f}', float(('9' * 40) + '.' + ('9' * 40))),
    ('^{:f}', -float(('9' * 40) + '.' + ('9' * 40))),
]
@pytest.mark.parametrize('gemstone_value_string, expected_py_value', NUMBER_SCENARIOS)
def test_translating_numbers_to_python(session, gemstone_value_string, expected_py_value):
    gemstone_value = session.execute(gemstone_value_string.format(expected_py_value))
    assert gemstone_value.to_py == expected_py_value

NUMBER_SCENARIOS = [
    (0, 'SmallInteger', 'self == {}'),
    (123, 'SmallInteger', 'self == {}'),
    (-123, 'SmallInteger', 'self == {}'),
    
    (int('9' * INITIAL_FETCH_SIZE), 'LargeInteger', 'self = {}'),
    (-int('9' * INITIAL_FETCH_SIZE), 'LargeInteger', 'self = {}'),

    (123.123, 'SmallDouble', 'self = {}'),
    (-123.123, 'SmallDouble', 'self = {}'),

    (float(('9' * 40) + '.' + ('9' * 40)), 'Float', 'self = {:f}'),
    (-float(('9' * 40) + '.' + ('9' * 40)), 'Float', 'self = {:f}')
]
@pytest.mark.parametrize('py_value, expected_gemstone_class, gemstone_comparison', NUMBER_SCENARIOS)
def test_translating_number_objects_to_gemstone(session, oop_true, py_value, expected_gemstone_class, gemstone_comparison):
    converted_none = session.from_py(py_value)
    assert session.execute('self class == {}'.format(expected_gemstone_class), context=converted_none).oop == oop_true
    assert session.execute(gemstone_comparison.format(py_value), context=converted_none).oop == oop_true

def test_from_py_float_exception(invalid_session):
    py_float = float('9' * 40 + '.' + '99')
    with expected(GemstoneError, test='argument is not a valid GciSession pointer'):
        invalid_session.from_py(py_float)


        
#--[ translating: unicode strings ]------------------------------------------------------------

    
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
def test_translating_different_lengths_of_strings_to_python(session, multiplier, plus):
    unicode_string = 'a' * (session.initial_fetch_size * multiplier + plus)
    string = session.execute("'{}'".format(unicode_string))
    assert string.to_py == unicode_string


def test_translating_python_string_to_gemstone(session, oop_true):
    py_str = 'šamas'
    converted_str = session.from_py(py_str)
    assert session.execute('self class == Unicode16', context=converted_str).oop == oop_true
    assert session.execute("self = (((Unicode16 new) add:( Character codePoint: 0353); yourself), 'amas')", context=converted_str).oop == oop_true

    
def test_translating_python_string_exception(invalid_session):
    with expected(GemstoneError, test='argument is not a valid GciSession pointer'):
        invalid_session.from_py('2')

        
#--[ translating: misc errors ]------------------------------------------------------------
        
def test_translating_unsupported_object_types(session):
    py_not_implemented_type = []
    with expected(NotYetImplemented):
        session.from_py(py_not_implemented_type)

    date_symbol = session.resolve_symbol('Date')
    with expected(NotYetImplemented):
        date_symbol.to_py

        
def test_exceptions_when_translating_wrong_gemstone_type(session):
    date_symbol = session.resolve_symbol('Date')

    with expected(GemstoneApiError):
        session.object_small_integer_to_py(date_symbol)

    with expected(GemstoneError, test='class 802049 invalid for OopToDouble'):
        session.object_float_to_py(date_symbol)

    with expected(GemstoneError, test='a ArgumentError occurred (error 2718)'):
        session.object_string_to_py(date_symbol)

    with expected(GemstoneError, test='a ArgumentTypeError occurred (error 2103)'):
        session.object_latin1_to_py(date_symbol)


#--[ pythonic method names ]------------------------------------------------------------

def test_mapping_method_names(session):
    user_globals = session.resolve_symbol('UserGlobals')
    some_key = session.new_symbol('akey')

    user_globals.at_put(some_key, session.from_py(123))
    assert user_globals.at(some_key).to_py == 123
    assert user_globals.yourself() is user_globals

    with expected(GemstoneError, test='a SymbolDictionary does not understand  #\'methodthatdoesnotexist\''):
        user_globals.methodthatdoesnotexist()

    with expected(TypeError, test='at_put() takes exactly 2 arguments (0 given)'):
        user_globals.at_put()

    with expected(TypeError, test='at_put() takes exactly 2 arguments (1 given)'):
        user_globals.at_put(some_key)

    with expected(GemstoneError, test='a SymbolDictionary does not understand  #\'at\''):
        user_globals.at()
        



