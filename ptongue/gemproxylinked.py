
from contextlib import contextmanager
from atexit import register
import warnings
from ctypes import cdll, CDLL, create_string_buffer

from ptongue.gemstone import *
from ptongue.gemproxy import GemstoneWarning, GemstoneSession, to_c_bytes, make_GemstoneError, GemstoneApiError, GemObject

#======================================================================================================================
# cdef extern from "gci.hf":
#     void GciInitAppName(const char *applicationName, bint logWarnings)
#     void GciSetNet(const char StoneName[], const char HostUserId[], const char HostPassword[], const char GemService[])
#     bint GciInit()
#     void GciShutdown()
#     void GciUnload()
#     char* GciEncrypt(const char* password, char outBuff[], unsigned int outBuffSize)
#     bint GciLoginEx(const char gemstoneUsername[], const char gemstonePassword[], unsigned int loginFlags, int haltOnErrNum)
#     void GciLogout()
#     bint GciErr(GciErrSType *errorReport)
#     void GciClearStack(OopType aGsProcess)
#     void GciBegin()
#     void GciAbort()
#     bint GciCommit()
#     GciSessionIdType GciGetSessionId()
#     void GciSetSessionId(GciSessionIdType sessionId)
#     void GciReleaseOops(const OopType theOops[], int numOops)
#     bint GciIsRemote()
#     bint GciSessionIsRemote()
#     bint GciIsKindOf(OopType anObj, OopType aClassHistory)
#     OopType GciExecuteStrFromContext(const char source[], OopType contextObject, OopType symbolList)
#     OopType GciExecuteFromContext(OopType source, OopType contextObject, OopType symbolList)
#     OopType GciPerform(OopType receiver, const char selector[], const OopType args[], int numArgs)
#     OopType GciPerformSymDbg(OopType receiver, OopType selector, const OopType args[], int numArgs, int flags)
#     OopType GciNewSymbol(const char *cString)
#     OopType GciResolveSymbol(const char *cString , OopType symbolList)
#     OopType GciResolveSymbolObj(OopType aString, OopType symbolList)
#     OopType GciFetchClass(OopType theObject)
#     int64 GciFetchBytes_(OopType theObject, int64 startIndex, ByteType theBytes[], int64 numBytes)
#     int64 GciFetchUtf8Bytes_(OopType aString, int64 startIndex, ByteType *buf, int64 bufSize, OopType *utf8String, int flags)
#     double GciOopToFlt(OopType theObject)
#     OopType GciNewUtf8String(const char* utf8data, bint convertToUnicode)
#     OopType GciFltToOop(double aReal)
#     void GciReleaseOops(const OopType theOops[], int numOops)


# cdef extern from "gcirtl.hf":
#     cdef cppclass GciRtlFnameBuf:
#         GciRtlFnameBuf() except +
#     BoolType GciRtlLoad(BoolType useRpc, const char *path, char errBuf[], size_t errBufSize)
#     BoolType GciRtlLoadA(BoolType useRpc, const char *path, char errBuf[], size_t errBufSize, GciRtlFnameBuf *vmLibPath)
#     BoolType GciRtlIsLoaded()
#     void GciRtlUnload()

#======================================================================================================================
is_gembuilder_initialised = False
current_linked_session = None
gcilnk = None

#======================================================================================================================
def gembuilder_dealoc():
    error = GciErrSType()
    gcilnk.GciShutdown();
    if gcilnk.GciErr(ctypes.byref(error)):
        raise make_GemstoneError(self, error)

def gembuilder_init(session):
    global gcilnk
    global is_gembuilder_initialised
    gcilnk_filename = "libgcilnk-3.6.1-64.so"
    cdll.LoadLibrary(gcilnk_filename)
    gcilnk = CDLL(gcilnk_filename)

    error = GciErrSType()
    if not gcilnk.GciInit() and gcilnk.GciErr(ctypes.byref(error)):
        raise make_GemstoneError(session, error)
    is_gembuilder_initialised = True
    register(gembuilder_dealoc)

def get_current_linked_session():
    global current_linked_session
    return current_linked_session

#======================================================================================================================
class LinkedSession(GemstoneSession):
    def __init__(self, username, password, stone_name='gs64stone',
                  host_username=None, host_password=''):
        super().__init__()
        error = GciErrSType()

        global is_gembuilder_initialised
        if not is_gembuilder_initialised:
            gembuilder_init(self)

        global current_linked_session
        if current_linked_session != None and current_linked_session.is_logged_in:
            raise GemstoneApiError('There is an active linked session. Can not create another session.')

        c_host_username = 0
        if host_username:
            c_host_username = to_c_bytes(host_username)

        c_host_password = 0
        if host_password:
            c_host_password = to_c_bytes(host_password)
        
        gcilnk.GciSetNet(stone_name.encode('utf-8'), c_host_username, c_host_password, ''.encode('utf-8'))
        
        clean_login = gcilnk.GciLoginEx(username.encode('utf-8'), self.encrypt_password(password), GCI_LOGIN_PW_ENCRYPTED | GCI_LOGIN_QUIET, 0)
        self.c_session_id = gcilnk.GciGetSessionId()
        if not clean_login:
            gcilnk.GciErr(ctypes.byref(error))
            if self.c_session_id == GCI_INVALID_SESSION_ID.value:
                raise make_GemstoneError(self, error)
            else:
                warnings.warn(('{}: {}, {}'.format(error.exceptionObj, error.message, error.reason)).replace('\\n', ''),GemstoneWarning)

        current_linked_session = self

    def __repr__(self):
        return '%s(%s)' % (self.__class__.__name__, self.c_session_id)
    
    def encrypt_password(self, unencrypted_password):
        out_buff_size = 0
        encrypted_char = 0
        while encrypted_char == 0:
            out_buff_size = out_buff_size + self.initial_fetch_size
            out_buff = ctypes.create_string_buffer(out_buff_size)
            encrypted_char = gcilnk.GciEncrypt(unencrypted_password.encode('utf-8'), out_buff, out_buff_size)
        return out_buff.value

    def remove_dead_gemstone_objects(self):
        error = GciErrSType()
        unreferenced_gemstone_objects = [oop for oop in self.deallocated_unfreed_gemstone_objects if oop not in self.instances]
        if unreferenced_gemstone_objects:
            c_dead_oops = (OopType * len(unreferenced_gemstone_objects))(*unreferenced_gemstone_objects)
            gcilnk.GciReleaseOops(c_dead_oops, len(dead_oops))
            if gcilnk.GciErr(ctypes.byref(error)):
                raise make_GemstoneError(self, error)
        self.deallocated_unfreed_gemstone_objects.clear()

    def abort(self):
        error = GciErrSType()
        if not self.is_current_session:
            raise GemstoneApiError('Expected session to be the current session.')
        gcilnk.GciAbort()
        if gcilnk.GciErr(ctypes.byref(error)):
            raise make_GemstoneError(self, error)

    def begin(self):
        error = GciErrSType()
        if not self.is_current_session:
            raise GemstoneApiError('Expected session to be the current session.')
        gcilnk.GciBegin()
        if gcilnk.GciErr(ctypes.byref(error)):
            raise make_GemstoneError(self, error)

    def commit(self):
        error = GciErrSType()
        if not self.is_current_session:
            raise GemstoneApiError('Expected session to be the current session.')
        if not gcilnk.GciCommit() and gcilnk.GciErr(ctypes.byref(error)):
            raise make_GemstoneError(self, error)

    @property
    def is_remote(self):
        error = GciErrSType()
        if not self.is_current_session:
            raise GemstoneApiError('Expected session to be the current session.')
        session_is_remote = gcilnk.GciSessionIsRemote()
        if gcilnk.GciErr(ctypes.byref(error)):
            raise make_GemstoneError(self, error)
        return bool(session_is_remote)

    @property
    def is_logged_in(self):
        return (self.c_session_id == gcilnk.GciGetSessionId()) and (self.c_session_id != GCI_INVALID_SESSION_ID)

    @property
    def is_current_session(self):
        global current_linked_session
        return self is current_linked_session

    def py_to_string_(self, py_str):
        error = GciErrSType()
        if not self.is_current_session:
            raise GemstoneApiError('Expected session to be the current session.')
        return_oop = gcilnk.GciNewUtf8String(py_str.encode('utf-8'), True)
        if gcilnk.GciErr(ctypes.byref(error)):
            raise make_GemstoneError(self, error)
        return return_oop

    def py_to_float_(self, py_float):
        if not self.is_current_session:
            raise GemstoneApiError('Expected session to be the current session.')
        error = GciErrSType()
        return_oop = gcilnk.GciFltToOop(py_float)
        if return_oop == OOP_NIL and gcilnk.GciErr(ctypes.byref(error)):
            raise make_GemstoneError(self, error)
        return return_oop

    def execute(self, source, context=None, symbol_list=None):
        if not self.is_current_session:
            raise GemstoneApiError('Expected session to be the current session.')
        error = GciErrSType()
        if isinstance(source, str):
            return_oop = gcilnk.GciExecuteStrFromContext(source.encode('utf-8'), context.oop if context else OOP_NO_CONTEXT, 
                                                           symbol_list.oop if symbol_list else OOP_NIL)
        elif isinstance(source, GemObject):
            return_oop = gcilnk.GciExecuteFromContext(source.oop, context.oop if context else OOP_NO_CONTEXT, 
                                                           symbol_list.oop if symbol_list else OOP_NIL)
        else:
            raise GemstoneApiError('Source is type {}.Expected source to be a str or GemObject'.format(source.__class__.__name__))
        if return_oop == OOP_NIL and gcilnk.GciErr(ctypes.byref(error)):
            raise make_GemstoneError(self, error)
        return self.get_or_create_gem_object(return_oop)

    def new_symbol(self, py_string):
        if not self.is_current_session:
            raise GemstoneApiError('Expected session to be the current session.')
        error = GciErrSType()
        return_oop = gcilnk.GciNewSymbol(py_string.encode('utf-8'))
        if gcilnk.GciErr(ctypes.byref(error)):
            raise make_GemstoneError(self, error)
        return self.get_or_create_gem_object(return_oop)

    def resolve_symbol(self, symbol, symbol_list=None):
        if not self.is_current_session:
            raise GemstoneApiError('Expected session to be the current session.')
        error = GciErrSType()
        if isinstance(symbol, str):
            return_oop = gcilnk.GciResolveSymbol(symbol.encode('utf-8') , symbol_list.oop if symbol_list else OOP_NIL)
        elif isinstance(symbol, GemObject):
            return_oop = gcilnk.GciResolveSymbolObj(symbol.oop, symbol_list.oop if symbol_list else OOP_NIL)
        else:
            raise GemstoneApiError('Symbol is type {}.Expected symbol to be a str or GemObject'.format(symbol.__class__.__name__))
        if return_oop == OOP_ILLEGAL and gcilnk.GciErr(ctypes.byref(error)):
            raise make_GemstoneError(self, error)
        return self.get_or_create_gem_object(return_oop)
        
    def log_out(self):
        if not self.is_current_session:
            raise GemstoneApiError('Expected session to be the current session.')
        error = GciErrSType()
        gcilnk.GciLogout()
        if gcilnk.GciErr(ctypes.byref(error)):
            raise make_GemstoneError(self, error)
        self.c_session_id = GCI_INVALID_SESSION_ID
        global current_linked_session
        current_linked_session = None

    def object_is_kind_of(self, instance, a_class):
        if not self.is_current_session:
            raise GemstoneApiError('Expected session to be the current session.')
        error = GciErrSType()
        is_kind_of_result = gcilnk.GciIsKindOf(instance.c_oop, a_class.c_oop)
        if is_kind_of_result == False and gcilnk.GciErr(ctypes.byref(error)):
            raise make_GemstoneError(self, error)
        return bool(is_kind_of_result)

    def object_gemstone_class(self, instance):
        if not self.is_current_session:
            raise GemstoneApiError('Expected session to be the current session.')
        error = GciErrSType()
        return_oop = gcilnk.GciFetchClass(instance.c_oop)
        if return_oop == OOP_NIL and gcilnk.GciErr(ctypes.byref(error)):
           raise make_GemstoneError(self, error)
        return self.get_or_create_gem_object(return_oop)

    def object_float_to_py(self, instance):
        if not self.is_current_session:
            raise GemstoneApiError('Expected session to be the current session.')
        error = GciErrSType()
        result = gcilnk.GciOopToFlt(instance.c_oop)
        if result != result and gcilnk.GciErr(ctypes.byref(error)):
            raise make_GemstoneError(self, error)
        return result

    def object_string_to_py(self, instance):
        if not self.is_current_session:
            raise GemstoneApiError('Expected session to be the current session.')
        start_index = 1
        num_bytes  = self.initial_fetch_size
        bytes_returned = num_bytes
        error = GciErrSType()
        py_bytes = b''
        utf8_string = OOP_NIL

        while bytes_returned == num_bytes:
            dest = (ByteType * (num_bytes + 1))
            bytes_returned = gcilnk.GciFetchUtf8Bytes_(instance.oop, start_index, dest, num_bytes, ctypes.byref(utf8_string), 0)
            if bytes_returned == 0 and gcilnk.GciErr(ctypes.byref(error)):
                raise make_GemstoneError(self, error)

            dest[bytes_returned] = b'\0'
            py_bytes += dest
            start_index = start_index + num_bytes
        if utf8_string != OOP_NIL:
            gcilnk.GciReleaseOops(ctypes.byref(utf8_string), 1)
            if gcilnk.GciErr(ctypes.byref(error)):
                raise make_GemstoneError(self, error)
        return py_bytes.decode('utf-8')

    def object_latin1_to_py(self, instance):
        if not self.is_current_session:
            raise GemstoneApiError('Expected session to be the current session.')

        start_index = 1
        num_bytes  = self.initial_fetch_size
        bytes_returned = num_bytes
        error = GciErrSType()

        py_bytes = b''
        while bytes_returned == num_bytes:
            dest = (ByteType * (num_bytes + 1))
            bytes_returned = gcilnk.GciFetchBytes_(instance.oop, start_index, dest, num_bytes)
            if bytes_returned == 0 and gcilnk.GciErr(ctypes.byref(error)):
                raise make_GemstoneError(self, error)

            dest[bytes_returned] = b'\0'
            py_bytes +=  dest
            start_index = start_index + num_bytes
        return py_bytes.decode('latin-1')

    def object_perform(self, instance, selector, *args):
        if not self.is_current_session:
            raise GemstoneApiError('Expected session to be the current session.')
        if not isinstance(selector, (str, GemObject)):
            raise GemstoneApiError('Selector is type {}.Expected selector to be a str or GemObject'.format(selector.__class__.__name__))
        error = GciErrSType()
        if not self.is_current_session:
            raise GemstoneApiError('Expected session to be the current session.')
        cargs = (OopType * len(args))(*[i.oop for i in args])

        if isinstance(selector, str):
            return_oop = gcilnk.GciPerform(instance.c_oop, selector.encode('utf-8'), cargs, len(args))
        else:
            return_oop = gcilnk.GciPerformSymDbg(instance.c_oop, selector.oop, cargs, len(args), 0)

        if return_oop == OOP_NIL and gcilnk.GciErr(ctypes.byref(error)):
            raise make_GemstoneError(self, error)
        return self.get_or_create_gem_object(return_oop)

#======================================================================================================================
