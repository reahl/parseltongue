
from contextlib import contextmanager
import os
import warnings

import pytest

from ptongue.gemproxy import GemObject, GemstoneError, NotSupported, InvalidSession, GemstoneApiError, GemstoneWarning
from ptongue.gemproxyrpc import RPCSession
from ptongue.gemproxylinked import LinkedSession
from ptongue.gemstonecontrol import GemstoneInstallation, GemstoneService, NetLDI, Stone

#======================================================================================================================

class InvalidLinkedSession(LinkedSession):
    @property
    def is_current_session(self):
        return True

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
def rpc_session(guestmode_netldi):
    rpc_session = RPCSession('DataCurator', 'swordfish')
    try:
       rpc_session.begin()
       yield rpc_session
    finally:
       rpc_session.abort()
       rpc_session.log_out()


@pytest.fixture
def linked_session(stone_fixture):
    linked_session = LinkedSession('DataCurator', 'swordfish')
    try:
       linked_session.begin()
       yield linked_session
    finally:
       linked_session.abort()
       linked_session.log_out()


@pytest.fixture
def oop_true(rpc_session):
    yield rpc_session.resolve_symbol('true').oop


@pytest.fixture
def invalid_rpc_session(guestmode_netldi):
    rpc_session = RPCSession('DataCurator', 'swordfish')
    rpc_session.log_out()
    yield rpc_session


@pytest.fixture
def invalid_linked_session(stone_fixture):
    invalid_linked_session = InvalidLinkedSession('DataCurator', 'swordfish')
    invalid_linked_session.log_out()
    yield invalid_linked_session

    
#======================================================================================================================

    
#--[ logging in and out ]------------------------------------------------------------

def test_rpc_session_login_captive_os_user(guestmode_netldi):
    session = RPCSession('DataCurator', 'swordfish')
    try:
        assert session.is_logged_in
    finally:
        session.log_out()
        assert not session.is_logged_in

    with expected(GemstoneError, test='the userId/password combination is invalid or expired'):
        RPCSession('DataCurator', 'wrong_password')

    with expected(GemstoneError, test='argument is not a valid GciSession pointer'):
        session.log_out()


def test_rpc_session_login_os_user(stone_fixture):
    with running_netldi(guest_mode=False):
        
        with expected(GemstoneError, test=lambda e: e.number == 4147):
            RPCSession('DataCurator', 'swordfish', host_username='vagrant', host_password='wrongvagrant')
            
        session = RPCSession('DataCurator', 'swordfish', host_username='vagrant', host_password='vagrant')
        try:
            assert session.is_logged_in
            assert session.is_remote
        finally:
            session.log_out()
            assert not session.is_logged_in


def test_linked_session_login(stone_fixture):
    linked_session = LinkedSession('DataCurator', 'swordfish')
    try:
        assert linked_session.is_logged_in
        assert not linked_session.is_remote 
        assert linked_session.is_current_session
    finally:
        linked_session.log_out()
        assert not linked_session.is_logged_in
        assert not linked_session.is_current_session

    with expected(GemstoneError, test='the userId/password combination is invalid or expired'):
        LinkedSession('DataCurator', 'wrong_password')

    with expected(GemstoneApiError, test='Expected session to be the current session.'):
        linked_session.log_out()


@pytest.mark.parametrize('session_class',[
    RPCSession,
    InvalidLinkedSession,
    ])
def test_gemstone_session_password_encryption(guestmode_netldi, session_class):
    password = 'swordfish'
    session = session_class('DataCurator', password)
    try:
        assert not password.encode('utf-8') in session.encrypt_password(password)
    finally:
        session.log_out()


def test_rpc_session_is_remote_exception(invalid_rpc_session):
    with expected(InvalidSession):
        invalid_rpc_session.is_remote


def test_lined_session_is_remote_exception(invalid_linked_session):
    with expected(GemstoneError, test='The given session ID is invalid.'):
        invalid_linked_session.is_remote


#--[ singleton linked session ]------------------------------------------------------------

def test_linked_singleton_error(linked_session):
    assert linked_session.is_logged_in
    with expected(GemstoneApiError, test='There is an active linked session. Can not create another session.'):
        LinkedSession('DataCurator', 'swordfish')


def test_linked_session_mismatch_error(stone_fixture):
    linked_session = LinkedSession('DataCurator', 'swordfish')  # so something is logged in globally
    try: 
        date_symbol = linked_session.resolve_symbol('Date')
        date_string = date_symbol.perform('asString')
        converted_float = linked_session.execute('123.123')
    finally:
        linked_session.log_out()

    with expected(GemstoneApiError, test='Expected session to be the current session.'):
        linked_session.abort()

    with expected(GemstoneApiError, test='Expected session to be the current session.'):
        linked_session.begin()

    with expected(GemstoneApiError, test='Expected session to be the current session.'):
        linked_session.commit()

    with expected(GemstoneApiError, test='Expected session to be the current session.'):
        linked_session.is_remote

    with expected(GemstoneApiError, test='Expected session to be the current session.'):
        linked_session.py_to_string_('String')

    with expected(GemstoneApiError, test='Expected session to be the current session.'):
        linked_session.py_to_float_(123.123)

    with expected(GemstoneApiError, test='Expected session to be the current session.'):
        linked_session.execute('2')

    with expected(GemstoneApiError, test='Expected session to be the current session.'):
        linked_session.new_symbol('newSymbol')

    with expected(GemstoneApiError, test='Expected session to be the current session.'):
        linked_session.resolve_symbol('Date')

    with expected(GemstoneApiError, test='Expected session to be the current session.'):
        linked_session.log_out()

    with expected(GemstoneApiError, test='Expected session to be the current session.'):
        linked_session.object_is_kind_of(date_symbol, date_symbol)

    with expected(GemstoneApiError, test='Expected session to be the current session.'):
        linked_session.object_gemstone_class(date_symbol)

    with expected(GemstoneApiError, test='Expected session to be the current session.'):
        linked_session.object_float_to_py(converted_float)

    with expected(GemstoneApiError, test='Expected session to be the current session.'):
        linked_session.object_string_to_py(date_string)

    with expected(GemstoneApiError, test='Expected session to be the current session.'):
        linked_session.object_latin1_to_py(date_string)

    with expected(GemstoneApiError, test='Expected session to be the current session.'):
        linked_session.object_perform(date_symbol, 'asString')

        
#--[ getting a hold of objects and symbols ]------------------------------------------------------------
        
def check_resolve_string_symbol(session):
    nil = session.resolve_symbol('nil') 
    assert isinstance(nil, GemObject)
    assert nil.oop == 20
    assert nil.is_nil


def test_rpc_session_resolve_string_symbol(rpc_session):
    check_resolve_string_symbol(rpc_session)


def test_linked_session_resolve_string_symbol(linked_session):
    check_resolve_string_symbol(linked_session)


def check_resolve_symbol_object(session):
    nil_symbol = session.new_symbol('nil')
    assert isinstance(nil_symbol, GemObject)
    assert nil_symbol.is_symbol

    nil = session.resolve_symbol(nil_symbol) 
    assert isinstance(nil, GemObject)
    assert nil.oop == 20

    with expected(GemstoneApiError):
        session.resolve_symbol(2)

    number = session.execute('2')
    with expected(GemstoneError, test='a ArgumentTypeError occurred (error 2242)'):
        session.resolve_symbol(number)

    py_string = 'a' * 2000
    with expected(GemstoneError, test='a ImproperOperation occurred (error 2402), Cannot create a Symbol'):
        session.new_symbol(py_string)


def test_rpc_session_resolve_symbol_object(rpc_session):
    check_resolve_symbol_object(rpc_session)


def test_linked_session_resolve_symbol_object(linked_session):
    check_resolve_symbol_object(linked_session)

        
#--[ performing selectors and executing arbitrary code ]------------------------------------------------------------
        
def check_perform_returns_value(session):
    date_class = session.resolve_symbol('Date')
    returned_object = date_class.perform('yourself')
    assert date_class.oop == returned_object.oop


def test_rpc_session_perform_returns_value(rpc_session):
    check_perform_returns_value(rpc_session)


def test_linked_session_perform_returns_value(linked_session):
    check_perform_returns_value(linked_session)


def check_perform_passing_args(session):
    some_symbol = session.new_symbol('some_symbol')
    gem_string = session.execute("'a string used as argument'")
    user_globals = session.resolve_symbol('UserGlobals')
    
    user_globals.perform('at:put:', some_symbol, gem_string)
    fetched_py_string = session.resolve_symbol('some_symbol')
    assert fetched_py_string.oop == gem_string.oop


def test_rpc_session_perform_passing_args(rpc_session):
    check_perform_passing_args(rpc_session)


def test_linked_session_perform_passing_args(linked_session):
    check_perform_passing_args(linked_session)


def check_perform_with_gem_object(session):
    date_class = session.resolve_symbol('Date')
    as_string_symbol = session.new_symbol('asString')
    date_class.perform(as_string_symbol)

    as_string_unicode = session.execute("'asString'")
    with expected(GemstoneError, test='a ArgumentTypeError occurred (error 2094), for asString  expected a Symbol'):
        date_class.perform(as_string_unicode)


def test_rpc_session_perform_with_gem_object(rpc_session):
    check_perform_with_gem_object(rpc_session)

        
def test_linked_session_perform_with_gem_object(linked_session):
    check_perform_with_gem_object(linked_session)

        
def check_perform_exception(session):
    date_class = session.resolve_symbol('Date')
    with expected(GemstoneError, test='a MessageNotUnderstood occurred (error 2010)'):
        date_class.perform('asFloat')


def test_rpc_session_perform_exception(rpc_session):
    check_perform_exception(rpc_session)


def test_linked_session_perform_exception(linked_session):
    check_perform_exception(linked_session)

        
def check_execute(session):
    date_class = session.execute('Date')
    date_class_resolved = session.resolve_symbol('Date')
    assert date_class.oop == date_class_resolved.oop


def test_rpc_session_execute(rpc_session):
    check_execute(rpc_session)


def test_linked_session_execute(linked_session):
    check_execute(linked_session)


def check_execute_with_gem_object(session):
    string_to_execute = session.execute("'Date'")
    date_class = session.execute(string_to_execute)
    date_class_resolved = session.resolve_symbol('Date')
    assert date_class.oop == date_class_resolved.oop


def test_rpc_session_execute_with_gem_object(rpc_session):
    check_execute_with_gem_object(rpc_session)


def test_linked_session_execute_with_gem_object(linked_session):
    check_execute_with_gem_object(linked_session)

    
def check_execute_in_context(session):
    date_class = session.resolve_symbol('Date')
    returned = session.execute('^self yourself', context=date_class)
    assert returned.oop == date_class.oop


def test_rpc_session_execute_in_context(rpc_session):
    check_execute_in_context(rpc_session)


def test_linked_session_execute_in_context(linked_session):
    check_execute_in_context(linked_session)


def check_session_execute_exception(session):
    with expected(GemstoneError, test='a CompileError occurred (error 1001), undefined symbol'):
        session.execute('invalid smalltalk code')


def test_rpc_session_execute_exception(rpc_session):
    check_session_execute_exception(rpc_session)


def test_linked_session_execute_exception(linked_session):
    check_session_execute_exception(linked_session)

        
#--[ transaction handling ]------------------------------------------------------------

def check_transactions(session):
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


def test_rpc_session_transactions(rpc_session):
    check_transactions(rpc_session)

       
def test_linked_session_transactions(linked_session):
    check_transactions(linked_session)

       
def check_session_transactional_exceptions(invalid_session, error_message):
    with expected(GemstoneError, test=error_message):
        invalid_session.abort()

    with expected(GemstoneError, test=error_message):
        invalid_session.begin()

    with expected(GemstoneError, test=error_message):
        invalid_session.commit()


def test_rpc_session_transactional_exceptions(invalid_rpc_session):
    check_session_transactional_exceptions(invalid_rpc_session, 'argument is not a valid GciSession pointer')


def test_linked_session_transactional_exceptions(invalid_linked_session):
    check_session_transactional_exceptions(invalid_linked_session, 'The given session ID is invalid.')


#--[ miscellaneous ]------------------------------------------------------------
        
def check_identity_of_objects_stay_same(session):
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

    
def test_rpc_session_identity_of_objects_stay_same(rpc_session):
    check_identity_of_objects_stay_same(rpc_session)


def test_linked_session_identity_of_objects_stay_same(linked_session):
    check_identity_of_objects_stay_same(linked_session)


def check_identity_of_objects_not_guaranteed_if_not_referenced(session):
    """If a GemObject is not referenced by Python anymore, there is no need to
       ensure its (python) identity stays the same. 

       In order to ensure identity we have to keep a reference to each object that is
       referenced from Python. This would result in unnecessary memory usage, and a
       memory leak over time in a long-running process. To prevent this, we cull these
       unreferenced objects and thus also cannot (unnecessarily so) keep maintaining
       its original (python) identity."""

    obj_id = id(session.resolve_symbol('Date'))
    # python object ids are their memory addresses and can be re-used; here we use some memory to make it unlikely 
    # that the recent object's address will be free in the following code.
    large_object_to_prevent_python_from_reusing_obj_id = '123'*200000000
    assert id(session.resolve_symbol('Date')) != obj_id


def test_rpc_session_identity_of_objects_not_guaranteed_if_not_referenced(rpc_session):
    check_identity_of_objects_not_guaranteed_if_not_referenced(rpc_session)


def test_linked_session_identity_of_objects_not_guaranteed_if_not_referenced(linked_session):
    check_identity_of_objects_not_guaranteed_if_not_referenced(linked_session)

def check_session_remove_unreferenced_gemstone_objects_from_gemstone_set(session, oop_true):
    """GemStone holds GemObjects that are returned to Python-side in an "export set" to ensure
       that they are not garbage collected when they're not referenced from inside GemStone while
       still being referenced from Python. Hence, GemStone needs to be informed when Python
       no longer references such objects so it can clean them from its export set. 
       This is done in batches for performance reasons.
    """
    date = session.resolve_symbol('Date')
    date_oop = date.oop
    assert session.execute('System testIf: Date isInHiddenSet: 39').oop == oop_true
    del(date)
    # Fetch enough objects from GemStone to trigger a batch, and stop referencing them from Python:
    for index in range(session.export_set_free_batch_size):
        converted_index = session.execute('{}'.format(index))
        del(converted_index)
    assert not session.execute('System testIf: Date isInHiddenSet: 39').oop == oop_true


def test_linked_session_remove_unreferenced_gemstone_objects_from_gemstone_set(linked_session, oop_true):
    check_session_remove_unreferenced_gemstone_objects_from_gemstone_set(linked_session, oop_true)


def test_rpc_session_remove_unreferenced_gemstone_objects_from_gemstone_set(rpc_session, oop_true):
    check_session_remove_unreferenced_gemstone_objects_from_gemstone_set(rpc_session, oop_true)

    
def check_raising_of_gemstone_exceptions(session, oop_true):
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


def test_rpc_session_raising_of_gemstone_exceptions(rpc_session, oop_true):
    check_raising_of_gemstone_exceptions(rpc_session, oop_true)


def test_linked_session_raising_of_gemstone_exceptions(linked_session, oop_true):
    check_raising_of_gemstone_exceptions(linked_session, oop_true)

    
#--[ special methods ]------------------------------------------------------------
        
def check_gemstone_class(session, oop_true):
    today = session.execute('Date today')

    date_class = today.gemstone_class()
    assert session.execute('self == Date', context=date_class).oop == oop_true

        
#--[ translating: unicode strings ]------------------------------------------------------------

def test_rpc_session_gemstone_class(rpc_session, oop_true):
    check_gemstone_class(rpc_session, oop_true)


def test_linked_session_gemstone_class(linked_session, oop_true):
    check_gemstone_class(linked_session, oop_true)


@pytest.mark.parametrize('session_class, expected_error_message',[
    (RPCSession, 'argument is not a valid GciSession pointer'),
    (InvalidLinkedSession, 'The given session ID is invalid.'),
    ])
def test_gemstone_class_exception(guestmode_netldi, session_class, expected_error_message):
    session = session_class('DataCurator', 'swordfish')
    try:
        today = session.execute('Date today')
    finally:
        session.log_out()

    with expected(GemstoneError, test=expected_error_message):
        today.gemstone_class()

        
def check_is_kind_of(session, oop_true):
    boolean = session.resolve_symbol('Boolean')
    true = session.execute('true')
    assert true.is_kind_of(boolean)

    not_a_class = session.execute('2')
    with expected(GemstoneError, test='a ArgumentTypeError occurred (error 2094)'):
        true.is_kind_of(not_a_class)


def test_rpc_session_is_kind_of(rpc_session, oop_true):
    check_is_kind_of(rpc_session, oop_true)


def test_linked_session_is_kind_of(linked_session, oop_true):
    check_is_kind_of(linked_session, oop_true)

        
#--[ translating: truthy values ]------------------------------------------------------------
        
def check_tranlating_truthy_objects_to_python(session, gem_value, expected_py_value):
    converted_value = session.resolve_symbol(gem_value).to_py
    assert converted_value is expected_py_value


@pytest.mark.parametrize('gem_value, expected_py_value',[
    ('true', True),
    ('false', False),
    ('nil', None)
    ])
def test_rpc_session_tranlating_truthy_objects_to_python(rpc_session, gem_value, expected_py_value):
    check_tranlating_truthy_objects_to_python(rpc_session, gem_value, expected_py_value)


@pytest.mark.parametrize('gem_value, expected_py_value',[
    ('true', True),
    ('false', False),
    ('nil', None)
    ])
def test_linked_session_tranlating_truthy_objects_to_python(linked_session, gem_value, expected_py_value):
    check_tranlating_truthy_objects_to_python(linked_session, gem_value, expected_py_value)


def check_translating_truthy_objects_to_gemstone(session, oop_true, py_value, expected_gemstone_class, expected_gemstone_value):
    converted_value = session.from_py(py_value)
    assert session.execute('self class == {}'.format(expected_gemstone_class), context=converted_value).oop == oop_true
    assert session.execute('self == {}'.format(expected_gemstone_value), context=converted_value).oop == oop_true

@pytest.mark.parametrize('py_value, expected_gemstone_class, expected_gemstone_value', [
    (None, 'UndefinedObject', 'nil'),
    (True, 'Boolean', 'true'),
    (False, 'Boolean', 'false')
])
def test_rpc_session_translating_truthy_objects_to_gemstone(rpc_session, oop_true, py_value, expected_gemstone_class, expected_gemstone_value):
    check_translating_truthy_objects_to_gemstone(rpc_session, oop_true, py_value, expected_gemstone_class, expected_gemstone_value)


@pytest.mark.parametrize('py_value, expected_gemstone_class, expected_gemstone_value', [
    (None, 'UndefinedObject', 'nil'),
    (True, 'Boolean', 'true'),
    (False, 'Boolean', 'false')
])
def test_linked_session_translating_truthy_objects_to_gemstone(linked_session, oop_true, py_value, expected_gemstone_class, expected_gemstone_value):
    check_translating_truthy_objects_to_gemstone(linked_session, oop_true, py_value, expected_gemstone_class, expected_gemstone_value)

    
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
def check_translating_numbers_to_python(session, gemstone_value_string, expected_py_value):
    gemstone_value = session.execute(gemstone_value_string.format(expected_py_value))
    assert gemstone_value.to_py == expected_py_value


@pytest.mark.parametrize('gemstone_value_string, expected_py_value', NUMBER_SCENARIOS)
def test_rpc_session_translating_numbers_to_python(rpc_session, gemstone_value_string, expected_py_value):
    check_translating_numbers_to_python(rpc_session, gemstone_value_string, expected_py_value)


@pytest.mark.parametrize('gemstone_value_string, expected_py_value', NUMBER_SCENARIOS)
def test_linked_session_translating_numbers_to_python(linked_session, gemstone_value_string, expected_py_value):
    check_translating_numbers_to_python(linked_session, gemstone_value_string, expected_py_value)


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
def check_translating_number_objects_to_gemstone(session, oop_true, py_value, expected_gemstone_class, gemstone_comparison):
    converted_none = session.from_py(py_value)
    assert session.execute('self class == {}'.format(expected_gemstone_class), context=converted_none).oop == oop_true
    assert session.execute(gemstone_comparison.format(py_value), context=converted_none).oop == oop_true


@pytest.mark.parametrize('py_value, expected_gemstone_class, gemstone_comparison', NUMBER_SCENARIOS)
def test_rpc_session_translating_number_objects_to_gemstone(rpc_session, oop_true, py_value, expected_gemstone_class, gemstone_comparison):
    check_translating_number_objects_to_gemstone(rpc_session, oop_true, py_value, expected_gemstone_class, gemstone_comparison)


@pytest.mark.parametrize('py_value, expected_gemstone_class, gemstone_comparison', NUMBER_SCENARIOS)
def test_linked_session_translating_number_objects_to_gemstone(linked_session, oop_true, py_value, expected_gemstone_class, gemstone_comparison):
    check_translating_number_objects_to_gemstone(linked_session, oop_true, py_value, expected_gemstone_class, gemstone_comparison)


def check_from_py_float_exception(invalid_session, error_message):
    py_float = float('9' * 40 + '.' + '99')
    with expected(GemstoneError, test=error_message):
        invalid_session.from_py(py_float)


def test_rpc_session_from_py_float_exception(invalid_rpc_session):
    check_from_py_float_exception(invalid_rpc_session, 'argument is not a valid GciSession pointer')


def test_linked_session_from_py_float_exception(invalid_linked_session):
    check_from_py_float_exception(invalid_linked_session, 'The given session ID is invalid.')

        
#--[ translating: unicode strings ]------------------------------------------------------------
    
def check_translating_unicode_strings_to_python(session):
    unicode_string = 'šamas'
    string = session.execute("((Unicode16 new) add:( Character codePoint: 0353); yourself), 'amas'")
    assert string.to_py == unicode_string


def test_rpc_session_translating_unicode_strings_to_python(rpc_session):
    check_translating_unicode_strings_to_python(rpc_session)


def test_linked_session_translating_unicode_strings_to_python(linked_session):
    check_translating_unicode_strings_to_python(linked_session)


def check_translating_different_lengths_of_strings_to_python(session, multiplier, plus):
    unicode_string = 'a' * (session.initial_fetch_size * multiplier + plus)
    string = session.execute("'{}'".format(unicode_string))
    assert string.to_py == unicode_string

@pytest.mark.parametrize('multiplier, plus',[
    (1, 0),
    (2, 0),
    (1, 1),
    (0, 0)
    ])
def test_rpc_session_translating_different_lengths_of_strings_to_python(rpc_session, multiplier, plus):
    check_translating_different_lengths_of_strings_to_python(rpc_session, multiplier, plus)

@pytest.mark.parametrize('multiplier, plus',[
    (1, 0),
    (2, 0),
    (1, 1),
    (0, 0)
    ])
def test_linked_session_translating_different_lengths_of_strings_to_python(linked_session, multiplier, plus):
    check_translating_different_lengths_of_strings_to_python(linked_session, multiplier, plus)


def check_translating_python_string_to_gemstone(session, oop_true):
    py_str = 'šamas'
    converted_str = session.from_py(py_str)
    assert session.execute('self class == Unicode16', context=converted_str).oop == oop_true
    assert session.execute("self = (((Unicode16 new) add:( Character codePoint: 0353); yourself), 'amas')", context=converted_str).oop == oop_true


def test_rpc_session_translating_python_string_to_gemstone(rpc_session, oop_true):
    check_translating_python_string_to_gemstone(rpc_session, oop_true)


def test_linked_session_translating_python_string_to_gemstone(linked_session, oop_true):
    check_translating_python_string_to_gemstone(linked_session, oop_true)

    
def check_translating_python_string_exception(invalid_session, error_message):
    with expected(GemstoneError, test=error_message):
        invalid_session.from_py('2')


def test_rpc_session_translating_python_string_exception(invalid_rpc_session):
    check_translating_python_string_exception(invalid_rpc_session, 'argument is not a valid GciSession pointer')


def test_linked_session_translating_python_string_exception(invalid_linked_session):
    check_translating_python_string_exception(invalid_linked_session, 'The given session ID is invalid.')

        
#--[ translating: misc errors ]------------------------------------------------------------
        
def check_translating_unsupported_object_types(session):
    py_not_implemented_type = []
    with expected(NotSupported):
        session.from_py(py_not_implemented_type)

    date_symbol = session.resolve_symbol('Date')
    with expected(NotSupported):
        date_symbol.to_py


def test_rpc_session_translating_unsupported_object_types(rpc_session):
    check_translating_unsupported_object_types(rpc_session)


def test_linked_session_translating_unsupported_object_types(linked_session):
    check_translating_unsupported_object_types(linked_session)

        
def check_exceptions_when_translating_wrong_gemstone_type(session, float_error_message):
    date_symbol = session.resolve_symbol('Date')

    with expected(GemstoneApiError):
        session.object_small_integer_to_py(date_symbol)

    with expected(GemstoneError, test=float_error_message):
        session.object_float_to_py(date_symbol)

    with expected(GemstoneError, test='a ArgumentError occurred (error 2718)'):
        session.object_string_to_py(date_symbol)

    with expected(GemstoneError, test='a ArgumentTypeError occurred (error 2103)'):
        session.object_latin1_to_py(date_symbol)


def test_rpc_session_exceptions_when_translating_wrong_gemstone_type(rpc_session):
    check_exceptions_when_translating_wrong_gemstone_type(rpc_session, 'class 802049 invalid for OopToDouble')


def test_linked_session_exceptions_when_translating_wrong_gemstone_type(linked_session):
    check_exceptions_when_translating_wrong_gemstone_type(linked_session, 'The given object is not a float.')


#--[ pythonic niceties ]------------------------------------------------------------

def check_mapping_method_names(session):
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


def test_rpc_session_mapping_method_names(rpc_session):
    check_mapping_method_names(rpc_session)


def test_linked_session_mapping_method_names(linked_session):
    check_mapping_method_names(linked_session)

    
