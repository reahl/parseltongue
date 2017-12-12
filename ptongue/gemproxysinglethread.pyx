from libc.stdlib cimport *
from libc.string cimport memcpy
from contextlib import contextmanager
from atexit import register
import warnings

from gemproxy cimport *
from gemproxy import well_known_class_names, well_known_instances, well_known_python_instances, implemented_python_types

#======================================================================================================================
cdef extern from "gci.hf":
    void GciInitAppName(const char *applicationName, bint logWarnings)
    void GciSetNet(const char StoneName[], const char HostUserId[], const char HostPassword[], const char GemService[])
    bint GciInit()
    void GciShutdown()
    void GciUnload()
    bint GciLogin(const char gemstoneUsername[], const char gemstonePassword[])
    void GciLogout()
    bint GciErr(GciErrSType *errorReport)
    void GciClearStack(OopType aGsProcess)
    void GciBegin()
    void GciAbort()
    bint GciCommit()
    GciSessionIdType GciGetSessionId()
    void GciSetSessionId(GciSessionIdType sessionId)
    void GciReleaseOops(const OopType theOops[], int numOops)
    bint GciIsRemote()
    bint GciSessionIsRemote()
    bint GciIsKindOf(OopType anObj, OopType aClassHistory)
    OopType GciExecuteStrFromContext(const char source[], OopType contextObject, OopType symbolList)
    OopType GciExecuteFromContext(OopType source, OopType contextObject, OopType symbolList)
    OopType GciPerform(OopType receiver, const char selector[], const OopType args[], int numArgs)
    OopType GciPerformSymDbg(OopType receiver, OopType selector, const OopType args[], int numArgs, int flags)
    OopType GciNewSymbol(const char *cString)
    OopType GciResolveSymbol(const char *cString , OopType symbolList)
    OopType GciResolveSymbolObj(OopType aString, OopType symbolList)
    OopType GciFetchClass(OopType theObject)
    int64 GciFetchBytes_(OopType theObject, int64 startIndex, ByteType theBytes[], int64 numBytes)
    int64 GciFetchUtf8Bytes_(OopType aString, int64 startIndex, ByteType *buf, int64 bufSize, OopType *utf8String, int flags)
    double GciOopToFlt(OopType theObject)
    bint GCI_OOP_IS_SMALL_INT(OopType oop)
    OopType GciNewUtf8String(const char* utf8data, bint convertToUnicode)
    OopType GciFltToOop(double aReal)

#======================================================================================================================
cdef bint is_init = False
cdef LinkedSession current_linked_session = None

#======================================================================================================================
cdef gembuilder_init(GemstoneSession session):
    cdef GciErrSType error
    if not GciInit() and GciErr(&error):
        raise make_GemstoneError(session, error)
    is_init = True

@register
def gembuilder_dealoc():
    cdef GciErrSType error
    GciShutdown();
    if GciErr(&error):
        raise make_GemstoneError(None, error)

#======================================================================================================================
class GemstoneWarning(Warning):
    pass

#======================================================================================================================
cdef class LinkedSession(GemstoneSession):
    cdef GciSessionIdType c_session_id
    def __cinit__(self, str username, str password):
        cdef GciErrSType error
        cdef char* c_host_username = NULL

        if not is_init:
            gembuilder_init(self)

        global current_linked_session
        if current_linked_session != None:
            raise GemstoneApiError('There is an active linked session. Can not create another session.')

        clean_login = GciLogin(username.encode('utf-8'), password.encode('utf-8'))
        self.c_session_id = GciGetSessionId()
        if not clean_login:
            GciErr(&error)
            if self.c_session_id == GCI_INVALID_SESSION_ID:
                raise make_GemstoneError(self, error)
            else:
                warnings.warn(('{}: {}, {}'.format(error.exceptionObj, error.message, error.reason)).replace('\\n', ''),GemstoneWarning)

        current_linked_session = self

    def abort(self):
        cdef GciErrSType error
        if not self.is_current_session:
            raise GemstoneApiError('Expected session to be the current session.')
        GciAbort()
        if GciErr(&error):
            raise make_GemstoneError(self, error)

    def begin(self):
        cdef GciErrSType error
        if not self.is_current_session:
            raise GemstoneApiError('Expected session to be the current session.')
        GciBegin()
        if GciErr(&error):
            raise make_GemstoneError(self, error)

    def commit(self):
        cdef GciErrSType error
        if not self.is_current_session:
            raise GemstoneApiError('Expected session to be the current session.')
        if not GciCommit() and GciErr(&error):
            raise make_GemstoneError(self, error)

    @property
    def is_remote(self):
        cdef GciErrSType error
        if not self.is_current_session:
            raise GemstoneApiError('Expected session to be the current session.')
        cdef bint session_is_remote = GciSessionIsRemote()
        if GciErr(&error):
            raise make_GemstoneError(self, error)
        return session_is_remote

    @property
    def is_logged_in(self):
        return self.c_session_id != GCI_INVALID_SESSION_ID

    @property
    def is_current_session(self):
        return self.c_session_id == GciGetSessionId()

    def from_py(self, py_object):
        cdef OopType return_oop
        try:
            method_name = implemented_python_types[py_object.__class__.__name__]
            return_oop = getattr(self, 'py_to_{}_'.format(method_name))(py_object)
        except KeyError:
            raise NotYetImplemented()
        return self.get_or_create_gem_object(return_oop)

    def py_to_boolean_or_none_(self, py_object):
        return well_known_python_instances[py_object]

    def py_to_string_(self, str py_str):
        cdef GciErrSType error
        cdef OopType return_oop
        return_oop = GciNewUtf8String(py_str.encode('utf-8'), True)
        if GciErr(&error):
            raise make_GemstoneError(self, error)
        return return_oop

    def py_to_integer_(self, py_int):
        cdef OopType return_oop = OOP_NIL
        try:
            return_oop = compute_small_integer_oop(py_int)
        except OverflowError:    
            return_oop = self.execute('^{}'.format(py_int)).oop
        return return_oop

    def py_to_float_(self, py_float):
        cdef GciErrSType error
        cdef OopType return_oop = OOP_NIL
        return_oop = GciFltToOop(py_float)
        if return_oop == OOP_NIL and GciErr(&error):
            raise make_GemstoneError(self, error)
        return return_oop

    def execute(self, source, GemObject context=None, GemObject symbol_list=None):
        cdef GciErrSType error
        cdef OopType return_oop 
        if not self.is_current_session:
            raise GemstoneApiError('Expected session to be the current session.')
        if isinstance(source, str):
            return_oop = GciExecuteStrFromContext(source.encode('utf-8'), context.oop if context else OOP_NO_CONTEXT, 
                                                           symbol_list.oop if symbol_list else OOP_NIL)
        elif isinstance(source, GemObject):
            return_oop = GciExecuteFromContext(source.oop, context.oop if context else OOP_NO_CONTEXT, 
                                                           symbol_list.oop if symbol_list else OOP_NIL)
        else:
            raise GemstoneApiError('Source is type {}.Expected source to be a str or GemObject'.format(source.__class__.__name__))
        if return_oop == OOP_NIL and GciErr(&error):
            raise make_GemstoneError(self, error)
        return self.get_or_create_gem_object(return_oop)

    def new_symbol(self, str py_string):
        cdef GciErrSType error
        cdef OopType return_oop
        if not self.is_current_session:
            raise GemstoneApiError('Expected session to be the current session.')
        return_oop = GciNewSymbol(py_string.encode('utf-8'))
        if GciErr(&error):
            raise make_GemstoneError(self, error)
        return self.get_or_create_gem_object(return_oop)

    def resolve_symbol(self, symbol, GemObject symbol_list=None):
        cdef GciErrSType error
        cdef OopType return_oop = OOP_NIL
        if not self.is_current_session:
            raise GemstoneApiError('Expected session to be the current session.')
        if isinstance(symbol, str):
            return_oop = GciResolveSymbol(symbol.encode('utf-8') , symbol_list.oop if symbol_list else OOP_NIL)
        elif isinstance(symbol, GemObject):
            return_oop = GciResolveSymbolObj(symbol.oop, symbol_list.oop if symbol_list else OOP_NIL)
        else:
            raise GemstoneApiError('Symbol is type {}.Expected symbol to be a str or GemObject'.format(symbol.__class__.__name__))
        if return_oop == OOP_ILLEGAL and GciErr(&error):
            raise make_GemstoneError(self, error)
        return self.get_or_create_gem_object(return_oop)
        
    def log_out(self):
        cdef GciErrSType error
        if not self.is_current_session:
            raise GemstoneApiError('Expected session to be the current session.')
        GciLogout()
        if GciErr(&error):
            raise make_GemstoneError(self, error)
        self.c_session_id = GCI_INVALID_SESSION_ID
        global current_linked_session
        current_linked_session = None

    def object_is_kind_of(self, GemObject instance, GemObject a_class):
        cdef GciErrSType error
        cdef int is_kind_of_result
        if not self.is_current_session:
            raise GemstoneApiError('Expected session to be the current session.')
        is_kind_of_result = GciIsKindOf(instance.c_oop, a_class.c_oop)
        if is_kind_of_result == False and GciErr(&error):
            raise make_GemstoneError(self, error)
        return <bint>is_kind_of_result

    def object_gemstone_class(self, GemObject instance):
        cdef GciErrSType error
        cdef OopType return_oop = GciFetchClass(instance.c_oop)
        if return_oop == OOP_NIL and GciErr(&error):
           raise make_GemstoneError(self, error)
        return self.get_or_create_gem_object(return_oop)

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

    def object_float_to_py(self, GemObject instance):
        cdef GciErrSType error
        cdef double result = GciOopToFlt(instance.c_oop)
        if GciErr(&error): # result == PlusQuietNaN???  isnan(result)??
            raise make_GemstoneError(self, error)
        return result

    def object_string_to_py(self, GemObject instance):
        cdef int64 start_index = 1
        cdef int64 num_bytes  = self.initial_fetch_size
        cdef int64 bytes_returned = num_bytes
        cdef GciErrSType error
        cdef bytes py_bytes = b''
        cdef ByteType* dest
        cdef OopType utf8_string = OOP_NIL
        while bytes_returned == num_bytes:
            dest = <ByteType *>malloc((num_bytes + 1) * sizeof(ByteType))
            try:
                bytes_returned = GciFetchUtf8Bytes_(instance.oop, start_index, dest, num_bytes, &utf8_string, 0)
                if bytes_returned == 0 and GciErr(&error):
                    raise make_GemstoneError(self, error)

                dest[bytes_returned] = b'\0'
                py_bytes = py_bytes + dest
                start_index = start_index + num_bytes
            finally:
                free(dest)
        if utf8_string != OOP_NIL:
            GciReleaseOops(&utf8_string, 1)
            if GciErr(&error):
                raise make_GemstoneError(self, error)
        return py_bytes.decode('utf-8')

    def object_latin1_to_py(self, GemObject instance):
        cdef int64 start_index = 1
        cdef int64 num_bytes  = self.initial_fetch_size
        cdef int64 bytes_returned = num_bytes
        cdef GciErrSType error
        cdef bytes py_bytes = b''
        cdef ByteType* dest
        while bytes_returned == num_bytes:
            dest = <ByteType *>malloc((num_bytes + 1) * sizeof(ByteType))
            try:
                bytes_returned = GciFetchBytes_(instance.oop, start_index, dest, num_bytes)
                if bytes_returned == 0 and GciErr(&error):
                    raise make_GemstoneError(self, error)

                dest[bytes_returned] = b'\0'
                py_bytes = py_bytes + dest
                start_index = start_index + num_bytes
            finally:
                free(dest)
        return py_bytes.decode('latin-1')

    def object_perform(self, GemObject instance, selector, *args):
        if not isinstance(selector, (str, GemObject)):
            raise GemstoneApiError('Selector is type {}.Expected selector to be a str or GemObject'.format(selector.__class__.__name__))
        cdef GciErrSType error
        cdef OopType* cargs
        cdef OopType return_oop = OOP_NIL
        if not self.is_current_session:
            raise GemstoneApiError('Expected session to be the current session.')
        cargs = <OopType *>malloc(len(args) * sizeof(OopType))
        try:
            for i in xrange(len(args)):
                cargs[i] = args[i].oop
            if isinstance(selector, str):
                return_oop = GciPerform(instance.c_oop, selector.encode('utf-8'), cargs, len(args))
            else:
                return_oop = GciPerformSymDbg(instance.c_oop, selector.oop, cargs, len(args), False)
        finally:
            free(cargs)
        if return_oop == OOP_NIL and GciErr(&error):
            raise make_GemstoneError(self, error)
        return self.get_or_create_gem_object(return_oop)

#======================================================================================================================
