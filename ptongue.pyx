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
cdef extern from "gci.hf":
    bint GciOopToBool(OopType theObject)

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
    OopType OOP_CLASS_BOOLEAN
    OopType OOP_CLASS_Float
    OopType OOP_CLASS_SMALL_DOUBLE
    OopType OOP_CLASS_BYTE_ARRAY
    OopType OOP_CLASS_STRING
    OopType OOP_CLASS_Utf8
    OopType OOP_CLASS_DATE_TIME
    OopType OOP_CLASS_ARRAY
    OopType OOP_CLASS_SYMBOL
    OopType OOP_CLASS_SYMBOL_LIST
    OopType OOP_CLASS_IDENTITY_BAG
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
    OopType GciTsNewSymbol(GciSession sess, const char *cString,
        GciErrSType *err)
    OopType GciTsNewUtf8String(GciSession sess, const char* utf8data, 
        bint convertToUnicode, GciErrSType *err)
    long long GciTsFetchUtf8Bytes(GciSession sess, OopType aString, long long startIndex, ByteType *dest, 
        long long bufSize, OopType *utf8String, GciErrSType *err , int flags)
    long long GciTsFetchBytes(GciSession sess, OopType theObject, long long startIndex, ByteType *dest, 
        long long numBytes, GciErrSType *err)
    long long GciTsFetchChars(GciSession sess, OopType theObject, long long startIndex, char *cString, 
        long long maxSize, GciErrSType *err)
    OopType GciTsFetchClass(GciSession sess, OopType obj, GciErrSType *err)
    int GciTsIsKindOf(GciSession sess, OopType obj, OopType aClass, GciErrSType *err)
    int GciTsIsKindOfClass(GciSession sess, OopType obj, OopType aClass, GciErrSType *err)
    OopType GciTsDoubleToOop(GciSession sess, double aDouble, GciErrSType *err)
    bint GciTsOopToDouble(GciSession sess, OopType oop, double *result, GciErrSType *err)

#======================================================================================================================
TYPES = [(OOP_NIL, 'OOP_NIL'),
        (OOP_ILLEGAL, 'OOP_ILLEGAL'),
        (OOP_CLASS_BOOLEAN, 'OOP_CLASS_BOOLEAN'),
        (OOP_CLASS_Float, 'OOP_CLASS_FLOAT'),
        (OOP_CLASS_SMALL_DOUBLE, 'OOP_CLASS_SMALL_DOUBLE'),
        (OOP_CLASS_BYTE_ARRAY, 'OOP_CLASS_BYTE_ARRAY'),
        (OOP_CLASS_STRING, 'OOP_CLASS_STRING'),
        (OOP_CLASS_Utf8, 'OOP_CLASS_Utf8'),
        (OOP_CLASS_DATE_TIME, 'OOP_CLASS_DATE_TIME'),
        (OOP_CLASS_ARRAY, 'OOP_CLASS_ARRAY'),
        (OOP_CLASS_SYMBOL, 'OOP_CLASS_SYMBOL'),
        (OOP_CLASS_SYMBOL_LIST, 'OOP_CLASS_SYMBOL_LIST'),
        (OOP_CLASS_IDENTITY_BAG, 'OOP_CLASS_IDENTITY_BAG')]
#======================================================================================================================
#Option 1
cdef class PyGciErrSType:
    cdef GciErrSType c_error
    cdef Session session
    def __cinit__(self, sess):
        self.c_error.init()
        self.session = sess

    @property
    def category(self):
        return GemObject(self.c_error.category)   

    @property
    def context(self):
        return GemObject(self.c_error.context)

    @property
    def exception_obj(self):
        return GemObject(self.session, self.c_error.exceptionObj)

    @property
    def args(self):
        args = [GemObject(self.c_error.args[0])]
        for i in xrange(1, self.c_error.argCount):
            args.append(GemObject(self.session, self.c_error.args[i]))
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
        return self.c_error.reason.decode('utf-8')

    @property
    def message(self):
        return self.c_error.message.decode('utf-8')

    def __str__(self):
        return ('{}{}'.format(self.message, self.reason)).replace('\\n', '\n')

class InvalidSession(Exception):
    pass

class GemstoneError(Exception):
    def __init__(self, PyGciErrSType err):
        self.error = err

    def __str__(self):
        return self.error.__str__()
#======================================================================================================================
cdef char* to_c_bytes(py_string):
    return py_string.encode('utf-8')

cdef class GemObject:
    cdef PyGciErrSType error
    cdef OopType oop
    cdef Session session
    def __cinit__(self, Session session, OopType oop=OOP_NIL):
        self.session = session
        self.error = PyGciErrSType(session)
        self.oop = oop

    @property
    def oop(self):
        return self.oop

    @property
    def is_nil(self):
        return self.oop == OOP_NIL

    @property
    def is_symbol(self):
        return 'OOP_CLASS_SYMBOL' in self.oop_type()

    def oop_type(self):
        self.error.c_error.init()
        cdef int is_type_of
        oop_types = []
        for type_oop in TYPES:
            is_type_of = GciTsIsKindOf(self.session.c_session, self.oop, type_oop[0], &(self.error.c_error))
            if is_type_of:
                oop_types.append(type_oop[1])
            elif is_type_of == -1:
                raise GemstoneError(self.error)
        return oop_types

    @property
    def to_py(self):
        self.error.c_error.init()
        oop_types = self.oop_type()
        if 'OOP_CLASS_BOOLEAN' in oop_types:
            return True #GciOopToBool(self.oop)
        elif any(True for x in ['OOP_CLASS_STRING', 'OOP_CLASS_Utf8'] if x in oop_types) :
            return self.fetch_chars(1, 1024)
        elif any(True for x in ['OOP_CLASS_SMALL_DOUBLE', 'OOP_CLASS_FLOAT'] if x in oop_types):
            return self.oop_to_double()
        elif any(True for x in ['OOP_CLASS_ARRAY', 'OOP_CLASS_BYTE_ARRAY'] if x in oop_types):
            return self.fetch_bytes(1, 1024)

    cdef fetch_bytes(self, long long start_index, long long num_bytes):# return num of bytes fetched??
        cdef ByteType* dest = <ByteType *>malloc(num_bytes * sizeof(ByteType))
        cdef long long bytes_returned = GciTsFetchBytes(self.session.c_session, self.oop, start_index, dest, num_bytes,
                                    &(self.error.c_error));
        if bytes_returned == -1:
            raise GemstoneError(self.error)
        args = [dest[0]]
        for i in xrange(1, bytes_returned):
            args.append(dest[i])
        free(dest)
        return args

    cdef fetch_chars(self, long long start_index, long long max_size):
        cdef char *c_string = <char *>malloc(max_size * sizeof(char))
        cdef long long bytes_returned = GciTsFetchChars(self.session.c_session, self.oop, start_index, c_string, max_size,
                                                        &(self.error.c_error))
        if bytes_returned == -1:
            raise GemstoneError(self.error)
        py_string = c_string.decode('utf-8')
        free (c_string)
        return py_string

    cdef oop_to_double(self):
        cdef double result = 0
        if not GciTsOopToDouble(self.session.c_session, self.oop, &result, &(self.error.c_error)):
            raise GemstoneError(self.error)
        return result

    def perform(self, selector, *args):
        self.error.c_error.init()
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
                                            &(self.error.c_error))
        free(cargs)
        if return_oop == OOP_ILLEGAL:
           raise GemstoneError(self.error)
        return GemObject(self.session, return_oop)

    def __str__(self):
        return '<%s object with oop %s>' % (self.__class__, self.oop)


#======================================================================================================================
cdef class Session:
    cdef GciSession c_session
    cdef PyGciErrSType error
    def __cinit__(self, str username, str password, str stone_name='gs64stone',
                  str host_username=None, str host_password='',
                  str netldi_task='gemnetobject'):
        self.error = PyGciErrSType(self)
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
                            0, 0, &(self.error.c_error))
        if self.c_session == NULL:
            raise GemstoneError(self.error)

    def abort(self):
        self.error.c_error.init()
        if not GciTsAbort(self.c_session, &(self.error.c_error)):
            raise GemstoneError(self.error)

    def begin(self):
        self.error.c_error.init()
        if not GciTsBegin(self.c_session, &(self.error.c_error)):
            raise GemstoneError(self.error)

    def commit(self):
        self.error.c_error.init()
        if not GciTsCommit(self.c_session, &(self.error.c_error)):
            raise GemstoneError(self.error)

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

    def py_object_to_oop(self, py_object):
        self.error.c_error.init()
        cdef OopType return_oop = OOP_NIL
        if isinstance(py_object, str):
            return_oop = GciTsNewUtf8String(self.c_session, py_object.encode('utf-8'), 0, &(self.error.c_error))
        elif isinstance(py_object, (int, long, float)):
            return_oop = GciTsDoubleToOop(self.c_session, py_object, &(self.error.c_error))
        if return_oop == OOP_ILLEGAL:
            raise GemstoneError(self.error)
        return GemObject(self, return_oop)

    def new_symbol(self, str py_string):
        self.error.c_error.init()
        cdef char *c_string = to_c_bytes(py_string)
        cdef OopType return_oop = GciTsNewSymbol(self.c_session, c_string, &(self.error.c_error))
        if return_oop == OOP_ILLEGAL:
            raise GemstoneError(self.error)
        return GemObject(self, return_oop)

    def resolve_symbol(self, symbol, GemObject symbol_list=None):
        self.error.c_error.init()
        cdef OopType return_oop = OOP_NIL
        if isinstance(symbol, str):
            return_oop = GciTsResolveSymbol(self.c_session, symbol.encode('utf-8'), 
                                            symbol_list.oop if symbol_list else OOP_NIL, &(self.error.c_error))
        elif isinstance(symbol, GemObject):
            return_oop = GciTsResolveSymbolObj(self.c_session, symbol.oop, 
                                            symbol_list.oop if symbol_list else OOP_NIL, &(self.error.c_error))
        else:
            assert None, 'I am unhappy'
        if return_oop == OOP_ILLEGAL:
            raise GemstoneError(self.error)
        return GemObject(self, return_oop)
           
    def log_out(self):
        self.error.c_error.init()
        if not GciTsLogout(self.c_session, &(self.error.c_error)):
            raise GemstoneError(self.error)

#======================================================================================================================
