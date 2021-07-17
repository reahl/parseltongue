import ctypes
import typing

FALSE = 0
TRUE = 1

#--------------------------------------------------[ gcioop.ht ]---
OOP_TAG_SPECIAL_MASK = 0x6
OOP_TAG_SMALLINT =     0x2

#--------------------------------------------------[ gcicmn.ht ]---
uintptr_t = ctypes.c_uint
def GCI_OOP_IS_SMALL_INT(oop):
    return (uintptr_t(oop) & OOP_TAG_SPECIAL_MASK) == OOP_TAG_SMALLINT


#--------------------------------------------------[ gci.ht ]---
OopType = ctypes.c_int64
ByteType = ctypes.c_ubyte
BoolType = ctypes.c_int

int32 = ctypes.c_int32
int64 = ctypes.c_int64

GciSessionIdType = ctypes.c_int
GCI_INVALID_SESSION_ID = GciSessionIdType(0)


GCI_ERR_STR_SIZE      =  1024
GCI_ERR_reasonSize    =  GCI_ERR_STR_SIZE
GCI_MAX_ERR_ARGS      =  10


class GciErrSType(ctypes.Structure):
    _fields_ = [
        ('category', OopType),
        ('context', OopType),
        ('exceptionObj', OopType),
        ('args', OopType * GCI_MAX_ERR_ARGS),
        ('number', ctypes.c_int),
        ('argCount', ctypes.c_int),
        ('fatal', ctypes.c_ubyte),
        ('message', ctypes.c_char * (GCI_ERR_STR_SIZE + 1)),
        ('reason', ctypes.c_char * (GCI_ERR_reasonSize + 1))
    ]
    def __init__(self):
        super().__init__()
        self.category = OOP_NIL
        self.exceptionObj = OOP_NIL
        self.number = 0
        self.context = OOP_NIL
        self.argCount = 0
        self.fatal = FALSE
        self.message = b'\0'
        self.reason = b'\0'
        self.args[0] = OOP_ILLEGAL

#enum GciByteSwizEType
gci_byte_swiz_none = 0
gci_byte_swiz_2_bytes = 1
gci_byte_swiz_4_bytes = 2
gci_byte_swiz_8_bytes = 3   


# Flags for GciLoginEx
GCI_LOGIN_PW_ENCRYPTED = 1
GCI_LOGIN_IS_SUBORDINATE = 2
GCI_LOGIN_FULL_COMPRESSION_ENABLED = 4
GCI_LOGIN_ERRS_USE_REF_SET = 8
GCI_LOGIN_QUIET = 0x10
GCI_CLIENT_DOES_SESSION_INIT = 0x20
GCI_TS_CLIENT = 0x40
GCI_LOGIN_ALL_FLAGS = 0x7F 



#--------------------------------------------------[ gcioc.ht ]---
GC_IMPLEMENTATION_MASK       = 0x03
GC_INDEXABLE_MASK            = 0x04
GC_INVARIANT_MASK            = 0x08


#--------------------------------------------------[ gcits.hf ]---

AUTH_NONE = 0 
AUTH_READ = 1
AUTH_WRITE = 2 
    
implem_mask    = GC_IMPLEMENTATION_MASK, # 0x03
indexable_mask = GC_INDEXABLE_MASK,      # 0x04
invariant_mask = GC_INVARIANT_MASK,      # 0x08
partial_mask   = 0x10
overlay_mask   = 0x20
is_placeholder = 0x40 
swiz_kind_mask = 0x300
swiz_kind_shift = 8



#--------------------------------------------------[ gcoop.ht ]---
OOP_ILLEGAL =             0x01
OOP_NO_CONTEXT =          OOP_ILLEGAL
OOP_NIL =                 0x14
OOP_CLASS_INTEGER =       70145
OOP_CLASS_SMALL_INTEGER = 74241
OOP_CLASS_LargeInteger =  136193
OOP_CLASS_SMALL_DOUBLE =  121345
OOP_CLASS_Float =         135937
OOP_CLASS_SYMBOL =        110849
OOP_CLASS_STRING =        74753
OOP_CLASS_DoubleByteString = 143873
OOP_CLASS_DoubleByteSymbol = 144129
OOP_CLASS_QuadByteString = 144385
OOP_CLASS_QuadByteSymbol = 144641
OOP_CLASS_CHARACTER =      68353
OOP_CLASS_Utf8 =           154113
OOP_CLASS_Unicode7 =       154369
OOP_CLASS_Unicode16 =      154625
OOP_CLASS_Unicode32 =      154881



OOP_FALSE =            0x0C
OOP_TRUE =             0x10C
OOP_ASCII_NUL =        0x1C
OOP_FIRST_JIS_CHAR =   0x24
