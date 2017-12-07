from gembuildertypes cimport int32, int64, OopType, GciErrSType, MAX_SMALL_INT, MIN_SMALL_INT, OOP_NUM_TAG_BITS, OOP_TAG_SMALLINT
from weakref import WeakValueDictionary
import warnings

# cdef object make_GemstoneError(session, GciErrSType c_error):
#     error = GemstoneError(session.get_or_create_gem_object(c_error.category) if c_error.category else None,
#         session.get_or_create_gem_object(c_error.context) if c_error.context else None,
#         session.get_or_create_gem_object(c_error.exceptionObj) if c_error.exceptionObj else None,
#         [session.get_or_create_gem_object(a) for a in c_error.args[:c_error.argCount]] if c_error.argCount else None,
#         c_error.number,
#         c_error.argCount,
#         c_error.fatal,
#         c_error.reason.decode('utf-8'),
#         c_error.message.decode('utf-8'))
#     return error

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
# cdef class GemstoneError(Exception):
#     def __cinit__(self, category, context, exception_obj, args, number, arg_count, fatal, reason, message):
#         self.category = category
#         self.context = context
#         self.exception_obj = exception_obj
#         self.args = args
#         self.number = number
#         self.arg_count = arg_count
#         self.fatal = fatal
#         self.reason = reason
#         self.message = message

#     def __str__(self):
#         return ('{}: {}, {}'.format(self.exception_obj, self.message, self.reason)).replace('\\n', '')

cdef class GemstoneError(Exception):
    # cdef GciErrSType c_error
    # cdef Session session
    def __cinit__(self, sess):
        self.c_error.init()
        self.session = sess

    cdef void set_error(self, GciErrSType error):
        self.c_error = error

    @property
    def category(self):
        return self.session.get_or_create_gem_object(self.c_error.category)   

    @property
    def context(self):
        return self.session.get_or_create_gem_object(self.c_error.context)

    @property
    def exception_obj(self):
        return self.session.get_or_create_gem_object(self.c_error.exceptionObj)

    @property
    def args(self):
        return [self.session.get_or_create_gem_object(a) for a in self.c_error.args[:self.c_error.argCount]]

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

class InvalidSession(Exception):
    pass

class NotYetImplemented(Exception):
    pass

class GemstoneApiError(Exception):
    pass

class GemstoneWarning(Warning):
    pass
#======================================================================================================================
cdef class GemObject:
    # cdef object __weakref__
    pass

cdef class GemstoneSession:
    # cdef object instances
    def __init__(self, *args, **kwargs):
        self.instances = WeakValueDictionary()