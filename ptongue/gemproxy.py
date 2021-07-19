
from weakref import WeakValueDictionary
import functools
import warnings


from ptongue.gemstone import *


#======================================================================================================================
well_known_class_names = { 
    OOP_CLASS_SMALL_INTEGER.value: 'small_integer',
    OOP_CLASS_LargeInteger.value: 'large_integer',
    OOP_CLASS_SMALL_DOUBLE.value: 'float',
    OOP_CLASS_Float.value: 'float',
    OOP_CLASS_STRING.value: 'string',
    OOP_CLASS_SYMBOL.value: 'string',
    OOP_CLASS_DoubleByteString.value: 'string',
    OOP_CLASS_DoubleByteSymbol.value: 'string',
    OOP_CLASS_QuadByteString.value: 'string',
    OOP_CLASS_QuadByteSymbol.value: 'string',
    OOP_CLASS_CHARACTER.value: 'string',
    OOP_CLASS_Utf8.value: 'string',
    OOP_CLASS_Unicode7.value: 'string',
    OOP_CLASS_Unicode16.value: 'string',
    OOP_CLASS_Unicode32.value: 'string'
 }

well_known_instances = {
    OOP_TRUE.value: True,
    OOP_FALSE.value: False,
    OOP_NIL.value: None
}

well_known_python_instances = {
    True: OOP_TRUE.value,
    False: OOP_FALSE.value,
    None: OOP_NIL.value
}

implemented_python_types = {
    'NoneType': "boolean_or_none",
    'bool': "boolean_or_none",
    'str': "string",
    'int': "integer",
    'float': "float"
}

#======================================================================================================================
def make_GemstoneError(session, c_error):
    error = GemstoneError(session)
    error.set_error(c_error)
    return error

def compute_small_integer_oop(py_int):
    if py_int <= MAX_SMALL_INT and py_int >= MIN_SMALL_INT:
        return (py_int << OOP_NUM_TAG_BITS) | OOP_TAG_SMALLINT
    else:
        raise OverflowError()

def to_c_bytes(py_string):
    return py_string.encode('utf-8')
    
#======================================================================================================================
class GemstoneError(Exception):
    """Represents an exception that happened in a Gem.

    This class is not a GemProxy, like other Gem objects becausgeme it
    has to be a Python Exception to worj with Python exception
    handling.

    """
    def __init__(self, sess):
        self.c_error = GciErrSType()
        self.session = sess

    def set_error(self, c_error):
        self.c_error = c_error

    @property
    def category(self):
        obj = self.session.get_or_create_gem_object(self.c_error.category) if self.c_error.category else None
        return None if obj.isNil().to_py else obj

    @property
    def context(self):
        obj = self.session.get_or_create_gem_object(self.c_error.context) if self.c_error.context else None
        return None if obj.isNil().to_py else obj

    @property
    def exception_obj(self):
        obj = self.session.get_or_create_gem_object(self.c_error.exceptionObj) if self.c_error.exceptionObj else None
        return None if obj.isNil().to_py else obj

    @property
    def args(self):
        return [self.session.get_or_create_gem_object(a) for a in self.c_error.args[:self.c_error.argCount]] if self.c_error.argCount else None

    @property
    def number(self):
        return self.c_error.number

    @property
    def arg_count(self):
        return self.c_error.argCount

    @property
    def is_fatal(self):
        return bool(self.c_error.fatal)

    @property
    def reason(self):
        return self.c_error.reason.decode('utf-8')

    @property
    def message(self):
        return self.c_error.message.decode('utf-8')

    def __str__(self):
        try:
            return self.exception_obj.asString().to_py
        except:
            return self.message

    def __repr__(self):
        try:
            return self.exception_obj.printString().to_py
        except:
            return self.message
    
    
class InvalidSession(Exception):
    """Indicates a problem with the current Session."""
    pass

class NotSupported(Exception):
    """Thrown when an attempt is made to do something that is not
       supported. For example, if you try to transfer a type of Python object
       to Gemstone which cannot be transferred.
    """
    pass

class GemstoneApiError(Exception):
    """Thrown when problems are detected while communicating via the underlying C API."""
    pass

class GemstoneWarning(Warning):
    """Represents a warning condition related to this API."""
    pass

#======================================================================================================================
class GemObject:
    """A Python object that represents a given object in a Gem.

       A GemObject object forwards method calls to its counterpart in the
       Gem. It returns other GemObject objects (and if the method takes
       arguments, those must also be GemObject objects)::
                
           today = date_class.today()
           assert isinstance(today, GemObject)
           assert today.is_kind_of(date_class)

       In Python, method names are spelt differently. Each ':' in a Smalltalk
       method symbol is replaced with a '_' in Python. When calling such a
       method, you must pass the correct number of arguments as Python
       positional arguments::

           user_globals.at_put(some_key, gem_number)

    """
    def __init__(self, session, oop):
        self.c_oop = oop
        self.session = session

    @property
    def oop(self):
        return self.c_oop

    @property
    def is_nil(self):
        return self.c_oop == OOP_NIL.value

    @property
    def is_symbol(self):
        return self.is_kind_of(self.session.get_or_create_gem_object(OOP_CLASS_SYMBOL.value))

    @property
    def to_py(self):
        """Transfers this GemObject to a Python object of appropriate type. This
           is only supported for basic types, such as unicode strings, various
           numbers and booleans.
        """
        return self.session.object_to_py(self)

    def is_kind_of(self, a_class):
        return self.session.object_is_kind_of(self, a_class)
    
    def gemstone_class(self):
        return self.session.object_gemstone_class(self)

    def __getattr__(self, name):
        return functools.partial(self.perform_mapped_selector, name)

    def perform_mapped_selector(self, selector, *args):
        smalltalk_selector = selector.replace('_', ':')
        if args or '_' in selector:
           smalltalk_selector += ':'
        expected_args = smalltalk_selector.count(':')
        if len(args) != expected_args:
            raise TypeError('%s() takes exactly %s arguments (%s given)' % (selector, expected_args, len(args)))
        selector_symbol = self.session.new_symbol(smalltalk_selector)
        return self.perform(selector_symbol, *args)

    def perform(self, selector, *args):
        return self.session.object_perform(self, selector, *args)

    def __str__(self):
        return '<%s object with oop %s>' % (self.__class__, self.c_oop)

    def __dealloc__(self):
        if self.session.is_logged_in:
            if len(self.session.deallocated_unfreed_gemstone_objects) > self.session.export_set_free_batch_size:
                self.session.remove_dead_gemstone_objects()
            self.session.deallocated_unfreed_gemstone_objects.add(self.c_oop)

#======================================================================================================================

class GemstoneSession:
    def __init__(self):
        self.instances = WeakValueDictionary()
        self.deallocated_unfreed_gemstone_objects = set()
        self.initial_fetch_size = 200
        self.export_set_free_batch_size = 1000

    def get_or_create_gem_object(self, oop):
        try:
            return self.instances[oop]
        except KeyError:
            new_gem_object = GemObject(self, oop)
            self.instances[oop] = new_gem_object
            return new_gem_object

    def from_py(self, py_object):
        try:
            method_name = implemented_python_types[py_object.__class__.__name__]
            return_oop = getattr(self, 'py_to_{}_'.format(method_name))(py_object)
        except KeyError:
            raise NotSupported()
        return self.get_or_create_gem_object(return_oop)

    def py_to_boolean_or_none_(self, py_object):
        return well_known_python_instances[py_object]

    def py_to_integer_(self, py_int):
        try:
            return_oop = compute_small_integer_oop(py_int)
        except OverflowError:    
            return_oop = self.execute('^{}'.format(py_int)).oop
        return return_oop

    def object_to_py(self, instance):
        try: 
            return well_known_instances[instance.oop]
        except KeyError:
            try:
                gem_class_name = well_known_class_names[instance.gemstone_class().oop]
            except KeyError:
                raise NotSupported()
            return getattr(self, 'object_{}_to_py'.format(gem_class_name))(instance)
    
    def object_small_integer_to_py(self, instance):
        if GCI_OOP_IS_SMALL_INT(instance.c_oop):
            return instance.c_oop >> OOP_NUM_TAG_BITS
        else:
            raise GemstoneApiError('Expected oop to represent a Small Integer.')

    def object_large_integer_to_py(self, instance):
        string_result = self.object_latin1_to_py(self.object_perform(instance, 'asString'))
        return int(string_result)

    
#======================================================================================================================
