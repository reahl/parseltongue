from libc.stdlib cimport *
from libc.string cimport memcpy

ctypedef void* GciSession
ctypedef long unsigned int OopType
ctypedef unsigned char ByteType
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
cdef extern from "gcits.hf":
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

    cdef cppclass GciTsObjInfo:
        OopType         objId
        OopType         objClass               # OOP of the class of the obj 
        long long       objSize              # obj's total size, in bytes or OOPs
        int             namedSize;                # num of named inst vars in the obj
        unsigned short  objectSecurityPolicyId  # previously named segmentId
        unsigned short  _bits;
        unsigned short  access;                  # 0 no auth, 1 read allowed, 2 write allowed
        inline unsigned char isInvariant()
        inline unsigned char isIndexable()
        inline unsigned char isPartial()
        inline unsigned char isOverlayed()
        inline GciByteSwizEType byteSwizKind() const
        inline unsigned char objImpl()

    GciSession GciTsLogin(
        const char *StoneNameNrs,
        const char *HostUserId, 
        const char *HostPassword, bint hostPwIsEncrypted,
        const char *GemServiceNrs,
        const char *gemstoneUsername, const char *gemstonePassword,
        unsigned int loginFlags, 
        int haltOnErrNum, GciErrSType *err);
    bint GciTsLogout(GciSession sess, GciErrSType *err)
    bint GciTsAbort(GciSession sess, GciErrSType *err)
    bint GciTsBegin(GciSession sess, GciErrSType *err)
    bint GciTsCommit(GciSession sess, GciErrSType *err)
    int GciTsSessionIsRemote(GciSession sess)
    OopType OOP_NIL
    OopType OOP_ILLEGAL
    OopType GciTsPerform(
        GciSession sess,
        OopType receiver,
        OopType aSymbol,
        const char* selectorStr,
        const OopType *args, 
        int numArgs,
        int flags,
        unsigned short environmentId,
        GciErrSType *err)
    OopType GciTsResolveSymbol(GciSession sess, const char* str, 
        OopType symbolList, GciErrSType *err)
    OopType GciTsResolveSymbolObj(GciSession sess, 
		OopType str, OopType symbolList, GciErrSType *err)


#======================================================================================================================
cdef class PyGciErrSType:
    cdef GciErrSType c_error
    def __cinit__(self):
        self.c_error.init()

    @property
    def category(self):
        return GemObject(self.c_error.category)   

    @property
    def context(self):
        return GemObject(self.c_error.context)

    @property
    def exception_obj(self):
        return GemObject(self.c_error.exceptionObj)

    @property
    def args(self):
        args = [GemObject(self.c_error.args[0])]
        for i in xrange(1, self.c_error.argCount):
            args.append(GemObject(self.c_error.args[i]))
        return args

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
        return self.c_error.reason

    @property
    def message(self):
        return self.c_error.message

    # def set_error(self, int errNum, str msg):
    #     self.c_error.setError(errNum, msg.encode('utf-8'))

    # def set_fatal_error(self, int errNum, str msg):
    #     self.c_error.setFatalError(errNum, msg.encode('utf-8'))



class InvalidSession(Exception):
   pass

#======================================================================================================================
class GemstoneError(Exception):
    def __init__(self, message, reason, exception):
        self.message = message
        self.reason = reason
        self.exception = exception

    def __str__(self):
        return '{}: {}, {}'.format(self.exception, self.message, self.reason)

cdef make_GemstoneError(Session session, GciErrSType e):
    return GemstoneError(e.message.decode('utf-8'), e.reason.decode('utf-8'), GemObject(session, e.exceptionObj))


#======================================================================================================================
cdef char* to_c_bytes(py_string):
    py_bytes = py_string.encode('utf-8')
    return py_bytes

cdef class GemObject:
    cdef OopType oop
    cdef Session session
    def __cinit__(self, Session session, OopType oop):
        self.session = session
        self.oop = oop

    def perform(self, selector, *args):
        cdef GciErrSType error
        cdef OopType selector_oop = selector.oop if isinstance(selector, GemObject) else OOP_ILLEGAL
        cdef char* selector_str = to_c_bytes(selector) if isinstance(selector, str) else NULL

        cdef OopType* cargs = <OopType *>malloc(len(args) * sizeof(OopType))
        for i in xrange(len(args)):
            cargs[i] = args[i].oop

        flags = 1
        environment_id = 0

        cdef OopType return_oop = GciTsPerform(self.session.c_session,
                                            self.oop,
                                            selector_oop,
                                            selector_str,
                                            cargs, 
                                            len(args),
                                            flags,
                                            environment_id,
                                            &error)
        free(cargs)
        if return_oop == OOP_ILLEGAL:
           raise make_GemstoneError(self.session, error)
        return GemObject(self.session, return_oop)

    def __str__(self):
        return '<%s object with oop %s>' % (self.__class__, self.oop)


#======================================================================================================================
cdef class Session:
    cdef GciSession c_session
    def __cinit__(self, str username, str password, str stone_name='gs64stone',
                  str host_username=None, str host_password='',
                  str netldi_task='gemnetobject'):
        cdef GciErrSType error

        cdef char* c_host_username = NULL
        if host_username:
            c_host_username = to_c_bytes(host_username)

        self.c_session = GciTsLogin(stone_name.encode('utf-8'),
                            c_host_username,
                            host_password.encode('utf-8'),
                            0,
                            netldi_task.encode('utf-8'),
                            username.encode('utf-8'),
                            password.encode('utf-8'),
                            0, 0, &error)
        if self.c_session == NULL:
            raise make_GemstoneError(self, error)

    def abort(self):
        cdef GciErrSType error
        if not GciTsAbort(self.c_session, &error):
           raise make_GemstoneError(self, error)

    def begin(self):
        cdef GciErrSType error
        if not GciTsBegin(self.c_session, &error):
           raise make_GemstoneError(self, error)

    def commit(self):
        cdef GciErrSType error
        if not GciTsCommit(self.c_session, &error):
           raise make_GemstoneError(self, error)

    @property
    def is_remote(self):
        cdef int remote = GciTsSessionIsRemote(self.c_session)
        if remote == -1:
           raise InvalidSession()
        return <bint>remote

    @property
    def is_logged_in(self):
        cdef int remote = GciTsSessionIsRemote(self.c_session)
        return remote != -1

    def resolve_symbol(self, symbol, GemObject symbol_list=None):
        cdef GciErrSType error
        cdef OopType return_oop
        if isinstance(symbol, str):
            return_oop = GciTsResolveSymbol(self.c_session, symbol.encode('utf-8'), 
                                            symbol_list.oop if symbol_list else OOP_NIL, &error)
        elif isinstance(symbol, GemObject):
            return_oop = GciTsResolveSymbolObj(self.c_session, symbol.oop, symbol_list, &error)
        else:
            assert None, 'I am unhappy'
        if return_oop == OOP_ILLEGAL:
            raise make_GemstoneError(self, error)
        return GemObject(self, return_oop)
           
    def log_out(self):
        cdef GciErrSType error
        if not GciTsLogout(self.c_session, &error):
           raise make_GemstoneError(self, error)

#======================================================================================================================
