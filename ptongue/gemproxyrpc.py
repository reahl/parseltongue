import ctypes
from ctypes import cdll, CDLL, create_string_buffer

from ptongue.gemstone import *
from ptongue.gemproxy import GemstoneError, GemObject, GemstoneSession, make_GemstoneError, to_c_bytes, InvalidSession, GemstoneApiError


class GciTs:
    def __init__(self):
        gcitl_filename = "libgcits-3.6.1-64.so"
        self.library = CDLL(gcitl_filename)

        self.GciTsEncrypt = self.library.GciTsEncrypt
        self.GciTsEncrypt.restype = ctypes.c_char_p
        self.GciTsEncrypt.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_size_t]

        
        self.GciTsLogin = self.library.GciTsLogin
        self.GciTsLogin.restype = GciSession
        self.GciTsLogin.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, BoolType, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p,
                                    ctypes.c_uint, ctypes.c_int, ctypes.POINTER(BoolType), ctypes.POINTER(GciErrSType)]

        self.GciTsLogout = self.library.GciTsLogout
        self.GciTsLogout.restype = BoolType
        self.GciTsLogout.argtypes = [GciSession, ctypes.POINTER(GciErrSType)]
        
        self.GciTsSessionIsRemote = self.library.GciTsSessionIsRemote
        self.GciTsSessionIsRemote.restype = ctypes.c_int
        self.GciTsSessionIsRemote.argtypes = [GciSession]

        self.GciTsExecute = self.library.GciTsExecute
        self.GciTsExecute.restype = OopType
        self.GciTsExecute.argtypes = [GciSession, ctypes.c_char_p, OopType, OopType, OopType, ctypes.c_int, ctypes.c_ushort, ctypes.POINTER(GciErrSType)]

        self.GciTsPerform = self.library.GciTsPerform
        self.GciTsPerform.restype = OopType
        self.GciTsPerform.argtypes = [GciSession, OopType, OopType, ctypes.c_char_p, ctypes.POINTER(OopType), ctypes.c_int, ctypes.c_int,
                                      ctypes.c_ushort, ctypes.POINTER(GciErrSType)]

        self.GciTsResolveSymbol = self.library.GciTsResolveSymbol
        self.GciTsResolveSymbol.restype = OopType
        self.GciTsResolveSymbol.argtypes = [GciSession, ctypes.c_char_p, OopType, ctypes.POINTER(GciErrSType)]

        self.GciTsResolveSymbolObj = self.library.GciTsResolveSymbolObj
        self.GciTsResolveSymbolObj.restype = OopType
        self.GciTsResolveSymbolObj.argtypes = [GciSession, OopType, OopType, ctypes.POINTER(GciErrSType)]

        self.GciTsNewSymbol = self.library.GciTsNewSymbol
        self.GciTsNewSymbol.restype = OopType
        self.GciTsNewSymbol.argtypes = [GciSession, ctypes.c_char_p, ctypes.POINTER(GciErrSType)]

        self.GciTsIsKindOf = self.library.GciTsIsKindOf
        self.GciTsIsKindOf.restype = ctypes.c_int
        self.GciTsIsKindOf.argtypes = [GciSession, OopType, OopType, ctypes.POINTER(GciErrSType)]

        self.GciTsFetchClass = self.library.GciTsFetchClass
        self.GciTsFetchClass.restype = OopType
        self.GciTsFetchClass.argtypes = [GciSession, OopType, ctypes.POINTER(GciErrSType)]

        self.GciTsAbort = self.library.GciTsAbort        
        self.GciTsAbort.restype = BoolType
        self.GciTsAbort.argtypes = [GciSession, ctypes.POINTER(GciErrSType)]

        self.GciTsCommit = self.library.GciTsCommit        
        self.GciTsCommit.restype = BoolType
        self.GciTsCommit.argtypes = [GciSession, ctypes.POINTER(GciErrSType)]

        self.GciTsBegin = self.library.GciTsBegin
        self.GciTsBegin.restype = BoolType
        self.GciTsBegin.argtypes = [GciSession, ctypes.POINTER(GciErrSType)]

        self.GciTsOopToDouble = self.library.GciTsOopToDouble
        self.GciTsOopToDouble.restype = BoolType
        self.GciTsOopToDouble.argtypes = [GciSession, OopType, ctypes.POINTER(ctypes.c_double), ctypes.POINTER(GciErrSType)]

        self.GciTsOopToI64 = self.library.GciTsOopToI64
        self.GciTsOopToI64.restype = BoolType
        self.GciTsOopToI64.argtypes = [GciSession, OopType, ctypes.POINTER(ctypes.c_int64), ctypes.POINTER(GciErrSType)]

        self.GciTsDoubleToOop = self.library.GciTsDoubleToOop
        self.GciTsDoubleToOop.restype = OopType
        self.GciTsDoubleToOop.argtypes = [GciSession, ctypes.c_double, ctypes.POINTER(GciErrSType)]

        self.GciTsI64ToOop = self.library.GciTsI64ToOop
        self.GciTsI64ToOop.restype = OopType
        self.GciTsI64ToOop.argtypes = [GciSession, ctypes.c_int64, ctypes.POINTER(GciErrSType)]

        self.GciTsFetchUtf8 = self.library.GciTsFetchUtf8
        self.GciTsFetchUtf8.restype = ctypes.c_int64
        self.GciTsFetchUtf8.argtypes = [GciSession, OopType, ctypes.POINTER(ByteType), ctypes.c_int64, ctypes.POINTER(ctypes.c_int64), ctypes.POINTER(GciErrSType)]

        self.GciTsFetchBytes = self.library.GciTsFetchBytes
        self.GciTsFetchBytes.restype = ctypes.c_int64
        self.GciTsFetchBytes.argtypes = [GciSession, OopType, ctypes.c_int64, ctypes.POINTER(ByteType), ctypes.c_int64, ctypes.POINTER(GciErrSType)]

        self.GciTsNewUtf8String = self.library.GciTsNewUtf8String
        self.GciTsNewUtf8String.restype = OopType
        self.GciTsNewUtf8String.argtypes = [GciSession, ctypes.c_char_p, BoolType, ctypes.POINTER(GciErrSType)]

        self.GciTsReleaseObjs = self.library.GciTsReleaseObjs
        self.GciTsReleaseObjs.restype = BoolType
        self.GciTsReleaseObjs.argtypes = [GciSession, ctypes.POINTER(OopType), ctypes.c_int, ctypes.POINTER(GciErrSType)]
        
        
#======================================================================================================================
class RPCSession(GemstoneSession):
    def __init__(self, username, password, stone_name='gs64stone',
                  host_username=None, host_password=None,
                  netldi_task='gemnetobject'):
        super().__init__()
        
        self.gcits = GciTs()
        
        c_host_username = None
        if host_username:
            c_host_username = to_c_bytes(host_username)

        error = GciErrSType()
        executedSessionInit = ctypes.c_int()
        
        self.c_session = self.gcits.GciTsLogin(stone_name.encode('utf-8'),
                                               c_host_username,
                                               self.encrypt_password(host_password),
                                               True,
                                               netldi_task.encode('utf-8'),
                                               username.encode('utf-8'),
                                               self.encrypt_password(password),
                                               GCI_LOGIN_PW_ENCRYPTED,
                                               0,
                                               ctypes.byref(executedSessionInit),
                                               ctypes.byref(error))
        if not self.c_session:
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
            c_dead_oops = (OopType * len(unreferenced_gemstone_objects))(*unreferenced_gemstone_objects)
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
        error = GciErrSType()
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
        if return_oop == OOP_ILLEGAL.value:
            raise make_GemstoneError(self, error)
        return return_oop

    def py_to_float_(self, py_float):
        error = GciErrSType()
        return_oop = self.gcits.GciTsDoubleToOop(self.c_session, py_float, ctypes.byref(error))
        if return_oop == OOP_ILLEGAL.value:
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
            return_oop = self.gcits.GciTsExecute(self.c_session, None, source.oop,
                                               context.oop if context else OOP_NIL, 
                                               symbol_list.oop if symbol_list else OOP_NIL,
                                               0, 0,  ctypes.byref(error))
        else:
            raise GemstoneApiError('Source is type {}.Expected source to be a str or GemObject'.format(source.__class__.__name__))
        if return_oop == OOP_ILLEGAL.value:
            raise make_GemstoneError(self, error)
        return self.get_or_create_gem_object(return_oop)

    def new_symbol(self, py_string):
        error = GciErrSType()
        return_oop = self.gcits.GciTsNewSymbol(self.c_session, py_string.encode('utf-8'), ctypes.byref(error))
        if return_oop == OOP_ILLEGAL.value:
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
        if return_oop == OOP_ILLEGAL.value:
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
        if return_oop == OOP_ILLEGAL.value:
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
        while required_size.value > max_bytes:
            tries = tries + 1
            if tries > 2:
                raise GemstoneApiError('Expected self.gcits.GciTsFetchUtf8 to fetch all bytes on a second call.')
            max_bytes = required_size.value
            c_string = (ByteType * (max_bytes + 1))()
            bytes_returned = self.gcits.GciTsFetchUtf8(self.c_session,
                     instance.c_oop, c_string, max_bytes, ctypes.byref(required_size), ctypes.byref(error))

            if bytes_returned == -1:
                raise make_GemstoneError(self, error)

            py_bytes = bytearray(c_string[:bytes_returned])

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

            py_bytes += bytearray(dest[:bytes_returned])
            start_index = start_index + num_bytes
        return py_bytes.decode('latin-1')

    def object_perform(self, instance, selector, *args):
        error = GciErrSType()
        if not isinstance(selector, (str, GemObject)):
            raise GemstoneApiError('Selector is type {}.Expected selector to be a str or GemObject'.format(selector.__class__.__name__))

        selector_oop = selector.oop if isinstance(selector, GemObject) else OOP_ILLEGAL
        selector_str = to_c_bytes(selector) if isinstance(selector, str) else None

        cargs = (OopType * len(args))(*args)
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
        if return_oop == OOP_ILLEGAL.value:
            raise make_GemstoneError(self, error)
        return self.get_or_create_gem_object(return_oop)

#======================================================================================================================
