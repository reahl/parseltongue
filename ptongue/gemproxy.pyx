from gemproxy cimport int32, int64, OopType, GciErrSType
from weakref import WeakValueDictionary
import functools
import warnings

#======================================================================================================================
cdef extern from "gcioop.ht":
    OopType OOP_FALSE
    OopType OOP_TRUE
    uint64_t OOP_TAG_SMALLINT
    uint64_t OOP_NUM_TAG_BITS
    int64 MIN_SMALL_INT
    int64 MAX_SMALL_INT

cdef extern from "gci.hf":
    bint GCI_OOP_IS_SMALL_INT(OopType oop)

#======================================================================================================================
well_known_class_names = { 
    OOP_CLASS_SMALL_INTEGER: 'small_integer',
    OOP_CLASS_LargeInteger: 'large_integer',
    OOP_CLASS_SMALL_DOUBLE: 'float',
    OOP_CLASS_Float: 'float',
    OOP_CLASS_STRING: 'string',
    OOP_CLASS_SYMBOL: 'string',
    OOP_CLASS_DoubleByteString: 'string',
    OOP_CLASS_DoubleByteSymbol: 'string',
    OOP_CLASS_QuadByteString: 'string',
    OOP_CLASS_QuadByteSymbol: 'string',
    OOP_CLASS_CHARACTER: 'string',
    OOP_CLASS_Utf8: 'string',
    OOP_CLASS_Unicode7: 'string',
    OOP_CLASS_Unicode16: 'string',
    OOP_CLASS_Unicode32: 'string'
 }

well_known_instances = {
    OOP_TRUE: True,
    OOP_FALSE: False,
    OOP_NIL: None
}

well_known_python_instances = {
    True: OOP_TRUE,
    False: OOP_FALSE,
    None: OOP_NIL
}

implemented_python_types = {
    'NoneType': "boolean_or_none",
    'bool': "boolean_or_none",
    'str': "string",
    'int': "integer",
    'float': "float"
}

#======================================================================================================================
cdef GemstoneError make_GemstoneError(session, GciErrSType c_error):
    error = GemstoneError(session)
    error.set_error(c_error)
    return error

cdef OopType compute_small_integer_oop(int64 py_int):
    cdef OopType return_oop
    if py_int <= MAX_SMALL_INT and py_int >= MIN_SMALL_INT:
        return <OopType>(((<int64>py_int) << OOP_NUM_TAG_BITS) | OOP_TAG_SMALLINT)
    else:
        raise OverflowError

cdef char* to_c_bytes(object py_string):
    return py_string.encode('utf-8')
    
#======================================================================================================================
cdef class GemstoneError(Exception):
    def __cinit__(self, sess):
        self.c_error.init()
        self.session = sess

    cdef void set_error(self, GciErrSType error):
        self.c_error = error

    @property
    def category(self):
        return self.session.get_or_create_gem_object(self.c_error.category) if self.c_error.category else None

    @property
    def context(self):
        return self.session.get_or_create_gem_object(self.c_error.context) if self.c_error.context else None

    @property
    def exception_obj(self):
        return self.session.get_or_create_gem_object(self.c_error.exceptionObj) if self.c_error.exceptionObj else None

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
        return <bint>self.c_error.fatal

    @property
    def reason(self):
        return self.c_error.reason.decode('utf-8')

    @property
    def message(self):
        return self.c_error.message.decode('utf-8')

    def __str__(self):
        return ('{}: {}, {}'.format(self.exception_obj, self.message, self.reason)).replace('\\n', '')

cdef class InvalidSession(Exception):
    pass

cdef class NotSupported(Exception):
    pass

cdef class GemstoneApiError(Exception):
    pass

class GemstoneWarning(Warning):
    pass

#======================================================================================================================
cdef class GemObject:
    def __cinit__(self, GemstoneSession session, OopType oop):
        self.c_oop = oop
        self.session = session

    @property
    def oop(self):
        return self.c_oop

    @property
    def is_nil(self):
        return self.c_oop == OOP_NIL

    @property
    def is_symbol(self):
        return self.is_kind_of(self.session.get_or_create_gem_object(OOP_CLASS_SYMBOL))

    @property
    def to_py(self):
        try: 
            return well_known_instances[self.oop]
        except KeyError:
            try:
                gem_class_name = well_known_class_names[self.gemstone_class().oop]
            except KeyError:
                raise NotSupported()
            return getattr(self.session, 'object_{}_to_py'.format(gem_class_name))(self)

    def is_kind_of(self, GemObject a_class):
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

#======================================================================================================================
cdef class GemstoneSession:
    def __cinit__(self, *args, **kwargs):
        self.instances = WeakValueDictionary()
        self.initial_fetch_size = 200

    @property
    def initial_fetch_size(self):
        return self.initial_fetch_size

    def get_or_create_gem_object(self, OopType oop):
        try:
            return self.instances[oop]
        except KeyError:
            new_gem_object = GemObject(self, oop)
            self.instances[oop] = new_gem_object
            return new_gem_object

    def from_py(self, py_object):
        cdef OopType return_oop
        try:
            method_name = implemented_python_types[py_object.__class__.__name__]
            return_oop = getattr(self, 'py_to_{}_'.format(method_name))(py_object)
        except KeyError:
            raise NotSupported()
        return self.get_or_create_gem_object(return_oop)

    def py_to_boolean_or_none_(self, py_object):
        return well_known_python_instances[py_object]

    def py_to_integer_(self, py_int):
        cdef OopType return_oop = OOP_NIL
        try:
            return_oop = compute_small_integer_oop(py_int)
        except OverflowError:    
            return_oop = self.execute('^{}'.format(py_int)).oop
        return return_oop

    def object_small_integer_to_py(self, GemObject instance):
        cdef int64 return_value 
        if GCI_OOP_IS_SMALL_INT(instance.c_oop):
            return_value = <int64>instance.c_oop >> <int64>OOP_NUM_TAG_BITS
            return return_value
        else:
            raise GemstoneApiError('Expected oop to represent a Small Integer.')

    def object_large_integer_to_py(self, GemObject instance):
        string_result = self.object_latin1_to_py(self.object_perform(instance, 'asString'))
        return int(string_result)

#======================================================================================================================