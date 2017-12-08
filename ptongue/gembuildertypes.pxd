from libc.stdint cimport int32_t, int64_t, uint64_t

ctypedef uint64_t OopType
ctypedef int32_t int32
ctypedef int64_t int64

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

cdef extern from "gcioop.ht":
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

cdef extern from "gci.hf":
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

    GciSessionIdType GCI_INVALID_SESSION_ID

#======================================================================================================================
cdef object make_GemstoneError(session, GciErrSType c_error)

cdef OopType compute_small_integer_oop(int64 py_int)

cdef char* to_c_bytes(object py_string)

#======================================================================================================================
cdef class GemstoneError(Exception):
    cdef GciErrSType c_error
    cdef object session
    cdef void set_error(self, GciErrSType error)

cdef class InvalidSession(Exception):
    pass

cdef class NotYetImplemented(Exception):
    pass

cdef class GemstoneApiError(Exception):
    pass

#======================================================================================================================
cdef class GemObject:
    cdef object __weakref__

cdef class GemstoneSession:
    cdef object instances