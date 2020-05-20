from libc.stdlib cimport *
from libc.string cimport memcpy
from contextlib import contextmanager
from atexit import register
import warnings

from gemproxy cimport *
from gemproxy import GemstoneWarning

#======================================================================================================================
cdef extern from "gci.hf":
    void GciInitAppName(const char *applicationName, bint logWarnings)
    void GciSetNet(const char StoneName[], const char HostUserId[], const char HostPassword[], const char GemService[])
    bint GciInit()
    void GciShutdown()
    void GciUnload()
    char* GciEncrypt(const char* password, char outBuff[], unsigned int outBuffSize)
    bint GciLoginEx(const char gemstoneUsername[], const char gemstonePassword[], unsigned int loginFlags, int haltOnErrNum)
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
    OopType GciNewUtf8String(const char* utf8data, bint convertToUnicode)
    OopType GciFltToOop(double aReal)
    void GciReleaseOops(const OopType theOops[], int numOops)

#======================================================================================================================
cdef bint is_gembuilder_initialised = False
current_linked_session = None

#======================================================================================================================
cdef gembuilder_init(GemstoneSession session):
    cdef GciErrSType error
    if not GciInit() and GciErr(&error):
        raise make_GemstoneError(session, error)
    is_gembuilder_initialised = True

@register
def gembuilder_dealoc():
    cdef GciErrSType error
    GciShutdown();
    if GciErr(&error):
        raise make_GemstoneError(None, error)

def get_current_linked_session():
    global current_linked_session
    return current_linked_session

#======================================================================================================================
cdef class LinkedSession(GemstoneSession):
    cdef GciSessionIdType c_session_id
    def __cinit__(self, str username, str password, str stone_name='gs64stone',
                  str host_username=None, str host_password=''):
        cdef GciErrSType error

        if not is_gembuilder_initialised:
            gembuilder_init(self)

        global current_linked_session
        if current_linked_session != None and current_linked_session.is_logged_in:
            raise GemstoneApiError('There is an active linked session. Can not create another session.')

        cdef char* c_host_username = NULL
        if host_username:
            c_host_username = to_c_bytes(host_username)

        cdef char* c_host_password = NULL
        if host_password:
            c_host_password = to_c_bytes(host_password)
        
        GciSetNet(stone_name.encode('utf-8'), c_host_username, c_host_password, ''.encode('utf-8'))
        
        clean_login = GciLoginEx(username.encode('utf-8'), self.encrypt_password(password), GCI_LOGIN_PW_ENCRYPTED | GCI_LOGIN_QUIET, 0)
        self.c_session_id = GciGetSessionId()
        if not clean_login:
            GciErr(&error)
            if self.c_session_id == GCI_INVALID_SESSION_ID:
                raise make_GemstoneError(self, error)
            else:
                warnings.warn(('{}: {}, {}'.format(error.exceptionObj, error.message, error.reason)).replace('\\n', ''),GemstoneWarning)

        current_linked_session = self

    def encrypt_password(self, str unencrypted_password):
        cdef char *out_buff
        cdef bytes encrypted_password
        cdef unsigned int out_buff_size = 0
        cdef char *encrypted_char = NULL
        while(encrypted_char == NULL):
            out_buff_size = out_buff_size + self.initial_fetch_size
            out_buff = <char *>malloc((out_buff_size) * sizeof(char))
            try:
                encrypted_char = GciEncrypt(unencrypted_password.encode('utf-8'), out_buff, out_buff_size)
                if encrypted_char != NULL:
                    encrypted_password = out_buff
            finally:
                free(out_buff)
        return encrypted_password

    def remove_dead_gemstone_objects(self):
        cdef GciErrSType error
        cdef object dead_oops = []
        cdef OopType *c_dead_oops
        unreferenced_gemstone_objects = [oop for oop in self.deallocated_unfreed_gemstone_objects if oop not in self.instances]
        dead_oops.extend(unreferenced_gemstone_objects)
        if dead_oops:
            c_dead_oops = <OopType *>malloc(len(dead_oops) * sizeof(OopType))
            try:
                for index in xrange(0, len(dead_oops)):
                    c_dead_oops[index] = dead_oops[index] 
                GciReleaseOops(c_dead_oops, len(dead_oops))
                if GciErr(&error):
                    raise make_GemstoneError(self, error)
            finally:
                free(c_dead_oops)
        self.deallocated_unfreed_gemstone_objects.clear()

    def abort(self):
        if not self.is_current_session:
            raise GemstoneApiError('Expected session to be the current session.')
        cdef GciErrSType error
        GciAbort()
        if GciErr(&error):
            raise make_GemstoneError(self, error)

    def begin(self):
        if not self.is_current_session:
            raise GemstoneApiError('Expected session to be the current session.')
        cdef GciErrSType error
        GciBegin()
        if GciErr(&error):
            raise make_GemstoneError(self, error)

    def commit(self):
        if not self.is_current_session:
            raise GemstoneApiError('Expected session to be the current session.')
        cdef GciErrSType error
        if not GciCommit() and GciErr(&error):
            raise make_GemstoneError(self, error)

    @property
    def is_remote(self):
        if not self.is_current_session:
            raise GemstoneApiError('Expected session to be the current session.')
        cdef GciErrSType error
        cdef bint session_is_remote = GciSessionIsRemote()
        if GciErr(&error):
            raise make_GemstoneError(self, error)
        return session_is_remote

    @property
    def is_logged_in(self):
        return (self.c_session_id == GciGetSessionId()) and (self.c_session_id != GCI_INVALID_SESSION_ID)

    @property
    def is_current_session(self):
        global current_linked_session
        return self is current_linked_session

    def py_to_string_(self, str py_str):
        if not self.is_current_session:
            raise GemstoneApiError('Expected session to be the current session.')
        cdef GciErrSType error
        cdef OopType return_oop
        return_oop = GciNewUtf8String(py_str.encode('utf-8'), True)
        if GciErr(&error):
            raise make_GemstoneError(self, error)
        return return_oop

    def py_to_float_(self, py_float):
        if not self.is_current_session:
            raise GemstoneApiError('Expected session to be the current session.')
        cdef GciErrSType error
        cdef OopType return_oop = OOP_NIL
        return_oop = GciFltToOop(py_float)
        if return_oop == OOP_NIL and GciErr(&error):
            raise make_GemstoneError(self, error)
        return return_oop

    def execute(self, source, GemObject context=None, GemObject symbol_list=None):
        if not self.is_current_session:
            raise GemstoneApiError('Expected session to be the current session.')
        cdef GciErrSType error
        cdef OopType return_oop 
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
        if not self.is_current_session:
            raise GemstoneApiError('Expected session to be the current session.')
        cdef GciErrSType error
        cdef OopType return_oop
        return_oop = GciNewSymbol(py_string.encode('utf-8'))
        if GciErr(&error):
            raise make_GemstoneError(self, error)
        return self.get_or_create_gem_object(return_oop)

    def resolve_symbol(self, symbol, GemObject symbol_list=None):
        if not self.is_current_session:
            raise GemstoneApiError('Expected session to be the current session.')
        cdef GciErrSType error
        cdef OopType return_oop = OOP_NIL
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
        if not self.is_current_session:
            raise GemstoneApiError('Expected session to be the current session.')
        cdef GciErrSType error
        GciLogout()
        if GciErr(&error):
            raise make_GemstoneError(self, error)
        self.c_session_id = GCI_INVALID_SESSION_ID
        global current_linked_session
        current_linked_session = None

    def object_is_kind_of(self, GemObject instance, GemObject a_class):
        if not self.is_current_session:
            raise GemstoneApiError('Expected session to be the current session.')
        cdef GciErrSType error
        cdef int is_kind_of_result
        is_kind_of_result = GciIsKindOf(instance.c_oop, a_class.c_oop)
        if is_kind_of_result == False and GciErr(&error):
            raise make_GemstoneError(self, error)
        return <bint>is_kind_of_result

    def object_gemstone_class(self, GemObject instance):
        if not self.is_current_session:
            raise GemstoneApiError('Expected session to be the current session.')
        cdef GciErrSType error
        cdef OopType return_oop = GciFetchClass(instance.c_oop)
        if return_oop == OOP_NIL and GciErr(&error):
           raise make_GemstoneError(self, error)
        return self.get_or_create_gem_object(return_oop)

    def object_float_to_py(self, GemObject instance):
        if not self.is_current_session:
            raise GemstoneApiError('Expected session to be the current session.')
        cdef GciErrSType error
        cdef double result = GciOopToFlt(instance.c_oop)
        if result != result and GciErr(&error):
            raise make_GemstoneError(self, error)
        return result

    def object_string_to_py(self, GemObject instance):
        if not self.is_current_session:
            raise GemstoneApiError('Expected session to be the current session.')
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
        if not self.is_current_session:
            raise GemstoneApiError('Expected session to be the current session.')
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
        if not self.is_current_session:
            raise GemstoneApiError('Expected session to be the current session.')
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
                return_oop = GciPerformSymDbg(instance.c_oop, selector.oop, cargs, len(args), 0)
        finally:
            free(cargs)
        if return_oop == OOP_NIL and GciErr(&error):
            raise make_GemstoneError(self, error)
        return self.get_or_create_gem_object(return_oop)

#======================================================================================================================
