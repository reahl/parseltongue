from ctypes import cdll, CDLL, create_string_buffer

from ptongue.gemstone import *
from ptongue.gemproxy import GemstoneError, GemObject, GemstoneSession, make_GemstoneError

#======================================================================================================================
# cdef extern from "gcits.hf":
#     char* GciTsEncrypt(const char* password, char *outBuf, size_t outBuffSize)
#     GciSession GciTsLogin(
#         const char *StoneNameNrs,
#         const char *HostUserId, 
#         const char *HostPassword,
#         BoolType hostPwIsEncrypted,
#         const char *GemServiceNrs,
#         const char *gemstoneUsername,
#         const char *gemstonePassword,
#         unsigned int loginFlags, 
#         int haltOnErrNum,
#         BoolType *executedSessionInit,
#         GciErrSType *err);
#     BoolType GciTsLogout(GciSession sess, GciErrSType *err)
#     BoolType GciTsAbort(GciSession sess, GciErrSType *err)
#     BoolType GciTsBegin(GciSession sess, GciErrSType *err)
#     BoolType GciTsCommit(GciSession sess, GciErrSType *err)
#     int GciTsSessionIsRemote(GciSession sess)
#     OopType GciTsPerform(
#         GciSession sess,
#         OopType receiver,
#         OopType aSymbol,
#         const char* selectorStr,
#         const OopType *args, 
#         int numArgs,
#         int flags,
#         unsigned short environmentId,
#         GciErrSType *err)
#     OopType GciTsResolveSymbol(GciSession sess, const char* str, 
#         OopType symbolList, GciErrSType *err)
#     OopType GciTsResolveSymbolObj(GciSession sess, 
# 		OopType str, OopType symbolList, GciErrSType *err)
#     OopType GciTsNewSymbol(GciSession sess, const char *cString,
#         GciErrSType *err)
#     int GciTsIsKindOf(GciSession sess, OopType obj, OopType aClass, GciErrSType *err)
#     OopType GciTsFetchClass(GciSession sess, OopType obj, GciErrSType *err)
#     OopType GciTsExecute(GciSession sess,
#         const char* sourceStr, OopType sourceOop,
#         OopType contextObject, OopType symbolList,
#         int flags, unsigned short environmentId,  GciErrSType *err)
#     bint GciTsOopToI64(GciSession sess, OopType oop, int64 *result, GciErrSType *err)
#     bint GciTsOopToDouble(GciSession sess, OopType oop, double *result, GciErrSType *err)
#     int64 GciTsFetchUtf8(GciSession sess,OopType obj, ByteType *dest, int64 destSize, 
#         int64 *requiredSize, GciErrSType *err )
#     int64 GciTsFetchBytes(GciSession sess, OopType theObject, int64 startIndex, ByteType *dest, 
#         int64 numBytes, GciErrSType *err)
#     OopType GciTsDoubleToOop(GciSession sess, double aDouble, GciErrSType *err)
#     OopType GciTsI64ToOop(GciSession sess, int64 arg, GciErrSType *err)
#     OopType GciTsNewUtf8String(GciSession sess, const char* utf8data, 
#         bint convertToUnicode, GciErrSType *err)
#     bint GciTsReleaseObjs(GciSession sess, OopType *buf, int count, GciErrSType *err)


# cdef extern from "gcirtl.hf":
#     cdef cppclass GciRtlFnameBuf:
#         GciRtlFnameBuf() except +
#     BoolType GciTsLoad(const char *path, char *errBuf, size_t errBufSize)
#     BoolType GciRtlLoad(BoolType useRpc, const char *path, char errBuf[], size_t errBufSize)
#     BoolType GciRtlIsLoaded()
#     void GciRtlUnload()


    
#======================================================================================================================
class RPCSession(GemstoneSession):
    def __init__(self, username, password, stone_name='gs64stone',
                  host_username=None, host_password=None,
                  netldi_task='gemnetobject'):
        super().__init__()
        gcitl_filename = "libgcits-3.6.1-64.so"
        cdll.LoadLibrary(gcitl_filename)
        self.gcits = CDLL(gcitl_filename)

        c_host_username = 0
        if host_username:
            c_host_username = to_c_bytes(host_username)

        c_host_password = 0
        if host_password:
            c_host_password = to_c_bytes(host_password)

        error = GciErrSType()
        executedSessionInit = ctypes.c_int()
        self.c_session = self.gcits.GciTsLogin(stone_name.encode('utf-8'),
                                               c_host_username,
                                               self.encrypt_password(c_host_password),
                                               True,
                                               netldi_task.encode('utf-8'),
                                               username.encode('utf-8'),
                                               self.encrypt_password(password),
                                               0,
                                               0,
                                               ctypes.byref(executedSessionInit),
                                               ctypes.byref(error))
        if self.c_session == 0:
            raise make_GemstoneError(self, error)

    def encrypt_password(self, unencrypted_password):
        if not unencrypted_password:
            return None
        out_buff_size = 0
        encrypted_char = 0
        while encrypted_char == 0:
            out_buff_size = out_buff_size + self.initial_fetch_size
            out_buff = ctypes.create_string_buffer(out_buff_size)
            encrypted_char = self.gcits.GciTsEncrypt(unencrypted_password.encode('utf-8'), out_buff, out_buff_size)
        return out_buff.value

    def remove_dead_gemstone_objects(self):
        error = GciErrSType()
        unreferenced_gemstone_objects = [oop for oop in self.deallocated_unfreed_gemstone_objects if oop not in self.instances]
        if unreferenced_gemstone_objects:
            c_dead_oops = (OopType * len(unreferenced_gemstone_objects))()
            for index in xrange(0, len(unreferenced_gemstone_objects)):
                c_dead_oops[index] = unreferenced_gemstone_objects[index] 
            if not self.gcits.GciTsReleaseObjs(self.c_session, c_dead_oops, len(dead_oops), ctypes.byref(error)):
                raise make_GemstoneError(self, error)
        self.deallocated_unfreed_gemstone_objects.clear()

    def abort(self):
        error = GciErrSType()
        if not self.gcits.GciTsAbort(self.c_session, ctypes.byref(error)):
            raise make_GemstoneError(self, error)

    def begin(self):
        error = GciErrSType()
        if not self.gcits.GciTsBegin(self.c_session, ctypes.byref(error)):
            raise make_GemstoneError(self, error)

    def commit(self):
        if not self.gcits.GciTsCommit(self.c_session, ctypes.byref(error)):
            raise make_GemstoneError(self, error)

    @property
    def is_remote(self):
        remote = self.gcits.GciTsSessionIsRemote(self.c_session)
        if remote == -1:
            raise InvalidSession()
        return bool(remote)

    @property
    def is_logged_in(self):
        remote = self.gcits.GciTsSessionIsRemote(self.c_session)
        return remote != -1

    def py_to_string_(self, py_str):
        error = GciErrSType()
        return_oop = self.gcits.GciTsNewUtf8String(self.c_session, py_str.encode('utf-8'), True, ctypes.byref(error))
        if return_oop == OOP_ILLEGAL:
            raise make_GemstoneError(self, error)
        return return_oop

    def py_to_float_(self, py_float):
        error = GciErrSType()
        return_oop = self.gcits.GciTsDoubleToOop(self.c_session, py_float, ctypes.byref(error))
        if return_oop == OOP_ILLEGAL:
            raise make_GemstoneError(self, error)
        return return_oop

    def execute(self, source, context=None, symbol_list=None):
        error = GciErrSType()
        if isinstance(source, str):
            return_oop = self.gcits.GciTsExecute(self.c_session, source.encode('utf-8'), OOP_CLASS_Utf8,
                                               context.oop if context else OOP_NIL, 
                                               symbol_list.oop if symbol_list else OOP_NIL,
                                               0, 0,  ctypes.byref(error))
        elif isinstance(source, GemObject):
            return_oop = self.gcits.GciTsExecute(self.c_session, 0, source.oop,
                                               context.oop if context else OOP_NIL, 
                                               symbol_list.oop if symbol_list else OOP_NIL,
                                               0, 0,  ctypes.byref(error))
        else:
            raise GemstoneApiError('Source is type {}.Expected source to be a str or GemObject'.format(source.__class__.__name__))
        if return_oop == OOP_ILLEGAL:
            raise make_GemstoneError(self, error)
        return self.get_or_create_gem_object(return_oop)

    def new_symbol(self, py_string):
        error = GciErrSType()
        return_oop = self.gcits.GciTsNewSymbol(self.c_session, py_string.encode('utf-8'), ctypes.byref(error))
        if return_oop == OOP_ILLEGAL:
            raise make_GemstoneError(self, error)
        return self.get_or_create_gem_object(return_oop)

    def resolve_symbol(self, symbol, symbol_list=None):
        error = GciErrSType()
        if isinstance(symbol, str):
            return_oop = self.gcits.GciTsResolveSymbol(self.c_session, symbol.encode('utf-8'), 
                                            symbol_list.oop if symbol_list else OOP_NIL, ctypes.byref(error))
        elif isinstance(symbol, GemObject):
            return_oop = self.gcits.GciTsResolveSymbolObj(self.c_session, symbol.oop, 
                                            symbol_list.oop if symbol_list else OOP_NIL, ctypes.byref(error))
        else:
            raise GemstoneApiError('Symbol is type {}.Expected symbol to be a str or GemObject'.format(symbol.__class__.__name__))
        if return_oop == OOP_ILLEGAL:
            raise make_GemstoneError(self, error)
        return self.get_or_create_gem_object(return_oop)
           
    def log_out(self):
        error = GciErrSType()
        if not self.gcits.GciTsLogout(self.c_session, ctypes.byref(error)):
            raise make_GemstoneError(self, error)

    def object_is_kind_of(self, instance, a_class):
        error = GciErrSType()
        is_kind_of_result = self.gcits.GciTsIsKindOf(self.c_session, instance.c_oop, a_class.c_oop, ctypes.byref(error))
        if is_kind_of_result == -1:
            raise make_GemstoneError(self, error)
        return bool(is_kind_of_result)

    def object_gemstone_class(self, instance):
        error = GciErrSType()
        return_oop = self.gcits.GciTsFetchClass(self.c_session, instance.c_oop, ctypes.byref(error))
        if return_oop == OOP_ILLEGAL:
           raise make_GemstoneError(self, error)
        return self.get_or_create_gem_object(return_oop)

    def object_float_to_py(self, instance):
        error = GciErrSType()
        result = ctypes.c_double()
        if not self.gcits.GciTsOopToDouble(self.c_session, instance.c_oop, ctypes.byref(result), ctypes.byref(error)):
            raise make_GemstoneError(self, error)
        return result.value

    def object_string_to_py(self, instance):
        error = GciErrSType()
        max_bytes = 0
        required_size = int64(self.initial_fetch_size)
        tries = 0
        while required_size > max_bytes:
            tries = tries + 1
            if tries > 2:
                raise GemstoneApiError('Expected self.gcits.GciTsFetchUtf8 to fetch all bytes on a second call.')
            max_bytes = required_size
            c_string = (ByteType * (max_bytes + 1))()
            bytes_returned = self.gcits.GciTsFetchUtf8(self.c_session,
                     instance.c_oop, c_string, max_bytes, ctypes.by_ref(required_size), ctypes.byref(error))

            if bytes_returned == -1:
                raise make_GemstoneError(self, error)

            c_string[bytes_returned] = b'\0'
            py_bytes = c_string.value

        return py_bytes.decode('utf-8')

    def object_latin1_to_py(self, instance):
        error = GciErrSType()
        start_index = 1
        num_bytes  = self.initial_fetch_size
        bytes_returned = num_bytes
        py_bytes = b''
        while bytes_returned == num_bytes:
            dest = (ByteType * (num_bytes + 1))()
            bytes_returned = self.gcits.GciTsFetchBytes(self.c_session, instance.oop, start_index,
                                                    dest, num_bytes, ctypes.byref(error));
            if bytes_returned == -1:
                raise make_GemstoneError(self, error)

            dest[bytes_returned] = b'\0'
            py_bytes += dest
            start_index = start_index + num_bytes
        return py_bytes.decode('latin-1')

    def object_perform(self, instance, selector, *args):
        error = GciErrSType()
        if not isinstance(selector, (str, GemObject)):
            raise GemstoneApiError('Selector is type {}.Expected selector to be a str or GemObject'.format(selector.__class__.__name__))

        selector_oop = selector.oop if isinstance(selector, GemObject) else OOP_ILLEGAL
        selector_str = to_c_bytes(selector) if isinstance(selector, str) else 0

        cargs = (OopType * len(args))
        for i in xrange(len(args)):
            cargs[i] = args[i].oop

        flags = 1
        environment_id = 0

        return_oop = self.gcits.GciTsPerform(self.c_session,
                                               instance.c_oop,
                                               selector_oop,
                                               selector_str,
                                               cargs, 
                                               len(args),
                                               flags,
                                               environment_id,
                                               ctypes.byref(error))
        if return_oop == OOP_ILLEGAL:
            raise make_GemstoneError(self, error)
        return self.get_or_create_gem_object(return_oop)

#======================================================================================================================
