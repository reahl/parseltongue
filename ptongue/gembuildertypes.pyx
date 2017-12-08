from gembuildertypes cimport int32, int64, OopType, GciErrSType, MAX_SMALL_INT, MIN_SMALL_INT, OOP_NUM_TAG_BITS, OOP_TAG_SMALLINT
from weakref import WeakValueDictionary

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
cdef object make_GemstoneError(session, GciErrSType c_error):
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

cdef class NotYetImplemented(Exception):
    pass

cdef class GemstoneApiError(Exception):
    pass

#======================================================================================================================
cdef class GemObject:
    pass

cdef class GemstoneSession:
    def __init__(self, *args, **kwargs):
        self.instances = WeakValueDictionary()