from libc.stdlib cimport *
from libc.stdint cimport int32_t, int64_t, uint64_t
from libc.string cimport memcpy
from weakref import WeakValueDictionary

ctypedef void* GciSession
ctypedef unsigned char ByteType

ctypedef uint64_t OopType
ctypedef int32_t int32
ctypedef int64_t int64

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
        int64       objSize              # obj's total size, in bytes or OOPs
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
    int GciTsIsKindOf(GciSession sess, OopType obj, OopType aClass, GciErrSType *err)
    OopType GciTsFetchClass(GciSession sess, OopType obj, GciErrSType *err)
    OopType GciTsExecute(GciSession sess,
        const char* sourceStr, OopType sourceOop,
        OopType contextObject, OopType symbolList,
        int flags, unsigned short environmentId,  GciErrSType *err)
    bint GciTsOopToI64(GciSession sess, OopType oop, int64 *result, GciErrSType *err)
    bint GciTsOopToDouble(GciSession sess, OopType oop, double *result, GciErrSType *err)
    int64 GciTsFetchUtf8(GciSession sess,OopType obj, ByteType *dest, int64 destSize, 
        int64 *requiredSize, GciErrSType *err )
    int64 GciTsFetchBytes(GciSession sess, OopType theObject, int64 startIndex, ByteType *dest, 
        int64 numBytes, GciErrSType *err)
    OopType GciTsDoubleToOop(GciSession sess, double aDouble, GciErrSType *err)
    OopType GciTsI64ToOop(GciSession sess, int64 arg, GciErrSType *err)
    OopType GciTsNewUtf8String(GciSession sess, const char* utf8data, 
        bint convertToUnicode, GciErrSType *err)
    OopType GCI_I32_TO_OOP(int64 arg)
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

    @property
    def to_py(self):
        value = None
        try: 
            return well_known_instances[self.oop]
        except KeyError:
            gem_class = self.gemstone_class()
            try:
                gem_class_name = well_known_class_names[gem_class.oop]
            except KeyError:
                raise NotYetImplemented()
            return getattr(self, '_{}_to_py'.format(gem_class_name))()

    def _small_integer_to_py(self):
        cdef int64 return_value 
        if GCI_OOP_IS_SMALL_INT(self.c_oop):
            return_value = <int64>self.c_oop >> <int64>OOP_NUM_TAG_BITS
            return return_value
        else:
            raise GemstoneApiError('Expected oop to represent a Small Integer.')

    def _large_integer_to_py(self):
        string_result = self.perform('asString')._latin1_to_py()
        return int(string_result)

    def _float_to_py(self):
        cdef GciErrSType error
        cdef double result = 0
        if not GciTsOopToDouble(self.session.c_session, self.c_oop, &result, &error):
            make_GemstoneError(self.session, error)
        return result

    def _string_to_py(self):
        cdef GciErrSType error
        cdef int64 max_bytes
        cdef ByteType *c_string
        cdef int64 required_size = self.session.initial_fetch_size
        cdef int64 bytes_returned
        cdef bytes py_bytes
        cdef int64 tries = 0

        while required_size > max_bytes:
            tries = tries + 1
            if tries > 2:
                raise GemstoneApiError('Expected GciTsFetchUtf8 to fetch all bytes on a second call.')
            max_bytes = required_size
            c_string = <ByteType *>malloc((max_bytes + 1) *sizeof(ByteType))
            try:
                bytes_returned = GciTsFetchUtf8(self.session.c_session,
                         self.c_oop, c_string, max_bytes, &required_size, &error)

                if bytes_returned == -1:
                    raise make_GemstoneError(self.session, error)

                c_string[bytes_returned] = '\0'
                py_bytes = c_string
            finally:
                free (c_string)

        return py_bytes.decode('utf-8')

    def _latin1_to_py(self):
        cdef int64 start_index = 1
        cdef int64 num_bytes  = self.session.initial_fetch_size
        cdef int64 bytes_returned = num_bytes
        cdef GciErrSType error
        cdef bytes py_bytes = b''
        cdef ByteType* dest
        while bytes_returned == num_bytes:
            if start_index > 5000000:
                raise GemstoneApiError('GciTsFetchBytes exceeded the size limit of strings.')
            dest = <ByteType *>malloc(num_bytes * sizeof(ByteType))
            try:
                bytes_returned = GciTsFetchBytes(self.session.c_session, self.oop, start_index,
                                                        dest, num_bytes, &error);
                if bytes_returned == -1:
                    make_GemstoneError(self.session, error)

                dest[bytes_returned] = b'\0'
                py_bytes = py_bytes + dest
                start_index = start_index + num_bytes
            finally:
                free(dest)
        return py_bytes.decode('latin-1')

    def gemstone_class(self):
        cdef GciErrSType error
        cdef OopType return_oop = GciTsFetchClass(self.session.c_session, self.c_oop, &error)
        if return_oop == OOP_ILLEGAL:
           raise make_GemstoneError(self.session, error)
        return self.session.get_or_create_gem_object(return_oop)

    def is_kind_of(self, GemObject a_class):
        cdef GciErrSType error
        cdef int is_kind_of_result = GciTsIsKindOf(self.session.c_session, self.c_oop, a_class.c_oop, &error)
        if is_kind_of_result == -1:
            raise make_GemstoneError(self.session, error)
        return <bint>is_kind_of_result

    def perform(self, selector, *args):
        cdef GciErrSType error
        cdef OopType selector_oop = selector.c_oop if isinstance(selector, GemObject) else OOP_ILLEGAL
        cdef char* selector_str = to_c_bytes(selector) if isinstance(selector, str) else NULL

        cdef OopType* cargs = <OopType *>malloc(len(args) * sizeof(OopType))
        for i in xrange(len(args)):
            cargs[i] = args[i].oop

        flags = 1
        environment_id = 0

        cdef OopType return_oop = GciTsPerform(self.session.c_session,
                                            self.c_oop,
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
        return self.session.get_or_create_gem_object(return_oop)

    def __str__(self):
        return '<%s object with oop %s>' % (self.__class__, self.c_oop)

#======================================================================================================================
cdef class Session:
    cdef GciSession c_session
    cdef object instances
    cdef short initial_fetch_size
    def __cinit__(self, str username, str password, str stone_name='gs64stone',
                  str host_username=None, str host_password='',
                  str netldi_task='gemnetobject'):
        self.initial_fetch_size = 200
        cdef GciErrSType error
        cdef char* c_host_username = NULL
        if host_username:
            c_host_username = to_c_bytes(host_username)

        self.instances = WeakValueDictionary()
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

    def from_py(self, py_object):
        cdef OopType return_oop
        try:
            method_name = implemented_python_types[py_object.__class__.__name__]
            return_oop = getattr(self, 'py_to_{}_'.format(method_name))(py_object)
        except KeyError:
            raise NotYetImplemented()
        return self.get_or_create_gem_object(return_oop)

    def py_to_boolean_or_none_(self, py_object):
        well_known_python_instances[py_object]

    def py_to_string_(self, str py_str):
        cdef GciErrSType error
        cdef OopType return_oop
        return_oop = GciTsNewUtf8String(self.c_session, py_str.encode('utf-8'), 0, &error)
        if return_oop == OOP_ILLEGAL:
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
        return_oop = GciTsDoubleToOop(self.c_session, py_float, &error)
        if return_oop == OOP_ILLEGAL:
            raise make_GemstoneError(self, error)
        return return_oop

    def execute(self, str source_str, GemObject context=None, GemObject symbol_list=None):
        cdef GciErrSType error
        cdef char *c_source_str = NULL
        if source_str:
            c_source_str = to_c_bytes(source_str)
        cdef OopType return_oop = GciTsExecute(self.c_session, c_source_str, OOP_CLASS_Utf8,
                                            context.oop if context else OOP_NIL, 
                                            symbol_list.oop if symbol_list else OOP_NIL,
                                            0, 0,  &error)
        if return_oop == OOP_ILLEGAL:
            raise make_GemstoneError(self, error)
        return self.get_or_create_gem_object(return_oop)

    def new_symbol(self, str py_string):
        cdef GciErrSType error
        cdef char *c_string = to_c_bytes(py_string)
        cdef OopType return_oop = GciTsNewSymbol(self.c_session, c_string, &error)
        if return_oop == OOP_ILLEGAL:
            raise make_GemstoneError(self, error)
        return self.get_or_create_gem_object(return_oop)

    def resolve_symbol(self, symbol, GemObject symbol_list=None):
        cdef GciErrSType error
        cdef OopType return_oop = OOP_NIL
        if isinstance(symbol, str):
            return_oop = GciTsResolveSymbol(self.c_session, symbol.encode('utf-8'), 
                                            symbol_list.oop if symbol_list else OOP_NIL, &error)
        elif isinstance(symbol, GemObject):
            return_oop = GciTsResolveSymbolObj(self.c_session, symbol.oop, 
                                            symbol_list.oop if symbol_list else OOP_NIL, &error)
        else:
            assert None, 'I am unhappy'
        if return_oop == OOP_ILLEGAL:
            raise make_GemstoneError(self, error)
        return self.get_or_create_gem_object(return_oop)
           
    def log_out(self):
        cdef GciErrSType error
        if not GciTsLogout(self.c_session, &error):
            raise make_GemstoneError(self, error)

#======================================================================================================================
