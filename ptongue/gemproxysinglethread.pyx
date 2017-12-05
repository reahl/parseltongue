from libc.stdlib cimport *
from libc.stdint cimport int32_t, int64_t, uint64_t
from libc.string cimport memcpy
from weakref import WeakValueDictionary
from contextlib import contextmanager
from atexit import register

ctypedef uint64_t OopType
ctypedef int32_t int32
ctypedef int64_t int64

ctypedef bint BoolType
ctypedef void* GciSession
ctypedef unsigned char ByteType
ctypedef int32 GciSessionIdType

cdef enum:
    AUTH_NONE = 0 
    AUTH_READ = 1
    AUTH_WRITE = 2 
cdef enum:
    implem_mask    = 0x03
    indexable_mask = 0x04
    invariant_mask = 0x08
    partial_mask   = 0x10
    overlay_mask   = 0x20
    is_placeholder = 0x40 # object is place holder for unsatisfied forward reference
    swiz_kind_mask = 0x300
    swiz_kind_shift = 8
ctypedef enum GciByteSwizEType:
    # How to swizzle body of a byte format object for conversion
    # between big and little endian, used for large integers, DoubleByteString,
    # Float, QuadByteString , etc
    gci_byte_swiz_none = 0
    gci_byte_swiz_2_bytes = 1 
    gci_byte_swiz_4_bytes = 2
    gci_byte_swiz_8_bytes = 3

GCI_ERR_STR_SIZE      =  1024
GCI_ERR_reasonSize    =  GCI_ERR_STR_SIZE
GCI_MAX_ERR_ARGS      =  10

#======================================================================================================================

cdef extern from "gci.hf":
    GciSessionIdType GCI_INVALID_SESSION_ID
    OopType OOP_NO_CONTEXT
    OopType OOP_NIL
    OopType OOP_ILLEGAL
    OopType OOP_FALSE
    OopType OOP_TRUE
    OopType OOP_CLASS_INTEGER
    OopType OOP_CLASS_SMALL_INTEGER
    OopType OOP_CLASS_LargeInteger
    OopType OOP_CLASS_SMALL_DOUBLE 
    OopType OOP_CLASS_Float
    OopType OOP_CLASS_SYMBOL
    OopType OOP_CLASS_STRING
    OopType OOP_CLASS_DoubleByteString
    OopType OOP_CLASS_DoubleByteSymbol
    OopType OOP_CLASS_QuadByteString
    OopType OOP_CLASS_QuadByteSymbol
    OopType OOP_CLASS_CHARACTER
    OopType OOP_CLASS_Utf8
    OopType OOP_CLASS_Unicode7
    OopType OOP_CLASS_Unicode16
    OopType OOP_CLASS_Unicode32
    uint64_t OOP_TAG_SMALLINT
    uint64_t OOP_NUM_TAG_BITS
    int64 MIN_SMALL_INT
    int64 MAX_SMALL_INT

    cdef cppclass GciErrSType:
        OopType         category
        OopType         context
        OopType         exceptionObj
        OopType         args[]
        int             number
        int             argCount
        unsigned char   fatal
        char            message[]
        char            reason[]
        inline void init()
        void setError(int errNum, const char* msg)
        void setFatalError(int errNum, const char* msg)
    
    bint GciRtlLoad(bint useRpc, const char *path, char errBuf[], size_t errBufSize);
    void GciRtlUnload()
    bint GciRtlIsLoaded()
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

#======================================================================================================================
cdef bint is_init = False
cdef bint is_logged_in = False

#======================================================================================================================
cdef gembuilder_init():
    cdef GciErrSType error
    if not GciInit() and GciErr(&error):
        raise make_GemstoneError(None, error)
    is_init = True

@register
def gembuilder_dealoc():
    cdef GciErrSType error
    GciShutdown();
    if GciErr(&error):
        raise make_GemstoneError(None, error)

cdef make_GemstoneError(Session session, GciErrSType e):
    error = GemstoneError(session)
    error.set_error(e)
    return error

cdef compute_small_integer_oop(int64 py_int):
    cdef OopType return_oop
    if py_int <= MAX_SMALL_INT and py_int >= MIN_SMALL_INT:
        return <OopType>(((<int64>py_int) << OOP_NUM_TAG_BITS) | OOP_TAG_SMALLINT)
    else:
        raise OverflowError

cdef char* to_c_bytes(py_string):
    return py_string.encode('utf-8')

#======================================================================================================================
cdef class GemstoneError(Exception):
    cdef GciErrSType c_error
    cdef Session session
    def __cinit__(self, sess):
        self.c_error.init()
        self.session = sess

    cdef set_error(self, GciErrSType error):
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
    def fatal(self):
        return self.c_error.fatal

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

#======================================================================================================================
cdef class GemObject:
    cdef OopType c_oop
    cdef Session session
    cdef object __weakref__
    def __cinit__(self, Session session, OopType oop):
        self.session = session
        self.c_oop = oop

    @property
    def oop(self):
        return self.c_oop

    @property
    def is_nil(self):
        return self.c_oop == OOP_NIL

    @property
    def is_symbol(self):
        return self.is_kind_of(self.session.get_or_create_gem_object(OOP_CLASS_SYMBOL))

    def is_kind_of(self, GemObject a_class):
        cdef GciErrSType error
        cdef int is_kind_of_result
        if not self.session.is_current_session:
            raise GemstoneApiError('Expected session to be the current session.')
        is_kind_of_result = GciIsKindOf(self.c_oop, a_class.c_oop)
        if is_kind_of_result == False and GciErr(&error):
            raise make_GemstoneError(self.session, error)
        return <bint>is_kind_of_result

    def perform(self, selector, *args):
        assert isinstance(selector, (str, GemObject)), 'Selector is type {}.Expected selector to be a str or GemObject'.format(selector.__class__.__name__)
        cdef GciErrSType error
        cdef OopType* cargs
        cdef OopType return_oop = OOP_NIL
        if not self.session.is_current_session:
            raise GemstoneApiError('Expected session to be the current session.')
        cargs = <OopType *>malloc(len(args) * sizeof(OopType))
        try:
            for i in xrange(len(args)):
                cargs[i] = args[i].oop
            if isinstance(selector, str):
                return_oop = GciPerform(self.c_oop, selector.encode('utf-8'), cargs, len(args))
            else:
                return_oop = GciPerformSymDbg(self.c_oop, selector, cargs, len(args), False)
        finally:
            free(cargs)
        if return_oop == OOP_NIL and GciErr(&error):  #TODO: check this logic: how do we know an error ocurred? should we always call this to check?
            raise make_GemstoneError(self, error)
        return self.session.get_or_create_gem_object(return_oop)

    def __str__(self):
        return '<%s object with oop %s>' % (self.__class__, self.c_oop)

#======================================================================================================================
cdef class Session:
    cdef GciSessionIdType c_session_id
    cdef object instances
    cdef int32 initial_fetch_size
    def __cinit__(self, str username, str password):
        self.initial_fetch_size = 200
        cdef GciErrSType error
        cdef char* c_host_username = NULL

        if not is_init:
            gembuilder_init()

        self.instances = WeakValueDictionary()

        global is_logged_in
        if is_logged_in:
            raise GemstoneApiError('There is an active linked session. Can not create another session.')

        is_logged_in = True

        if GciErr(&error):
            raise make_GemstoneError(self, error)

        clean_login = GciLogin(username.encode('utf-8'), password.encode('utf-8'))
        self.c_session_id = GciGetSessionId()
        if not clean_login:
            GciErr(&error)
            if self.c_session_id == GCI_INVALID_SESSION_ID:
                raise make_GemstoneError(self, error)
            else:
                raise GemstoneApiError('Something went wrong with the login.')

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
        if not self.is_current_session:
            raise GemstoneApiError('Expected session to be the current session.')
        return GciSessionIsRemote()

    @property
    def is_logged_in(self):
        global is_logged_in
        return is_logged_in

    @property
    def initial_fetch_size(self):
        return self.initial_fetch_size

    def get_or_create_gem_object(self, oop):
        try:
            return self.instances[oop]
        except KeyError:
            new_gem_object = GemObject(self, oop)
            self.instances[oop] = new_gem_object
            return new_gem_object

    @property
    def is_current_session(self):
        return self.c_session_id == GciGetSessionId()

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
        if return_oop == OOP_NIL and GciErr(&error):  #TODO: check this logic: how do we know an error ocurred? should we always call this to check?
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
        global is_logged_in
        is_logged_in = False

#======================================================================================================================
