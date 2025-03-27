# Copyright (C) 2025 Reahl Software Services (Pty) Ltd
# 
# This file is part of parseltongue.
#
# parseltongue is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# parseltongue is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with parseltongue.  If not, see <https://www.gnu.org/licenses/>.
import ctypes
from contextlib import contextmanager
from atexit import register
import warnings
from ctypes import cdll, CDLL, create_string_buffer

from ptongue.gemstone import *
from ptongue.gemproxy import GemstoneLibrary, GemstoneWarning, GemstoneSession, to_c_bytes, GemstoneError, GemstoneApiError, GemObject


is_gembuilder_initialised = False
current_linked_session = None
gci = None


class GciLnk(GemstoneLibrary):
    short_name = 'gcilnk'
    min_version = '3.4.0'
    max_version = '3.7.9999'
    def __init__(self, lib_path):
        super().__init__(lib_path)

        self.GciSetNet = self.library.GciSetNet
        self.GciSetNet.restype = None
        self.GciSetNet.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p]

        self.GciInit = self.library.GciInit
        self.GciInit.restype = BoolType
        self.GciInit.argtypes = []

        self.GciShutdown = self.library.GciShutdown
        self.GciShutdown.restype = None
        self.GciShutdown.argtypes = []

        self.GciEncrypt = self.library.GciEncrypt
        self.GciEncrypt.restype = ctypes.c_char_p
        self.GciEncrypt.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_uint]

        self.GciLoginEx = self.library.GciLoginEx
        self.GciLoginEx.restype = BoolType
        self.GciLoginEx.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_uint, ctypes.c_int]

        self.GciLogout = self.library.GciLogout
        self.GciLogout.restype = None
        self.GciLogout.argtypes = []

        self.GciErr = self.library.GciErr
        self.GciErr.restype = BoolType
        self.GciErr.argtypes = [ctypes.POINTER(GciErrSType)]

        self.GciBegin = self.library.GciBegin
        self.GciBegin.restype = None
        self.GciBegin.argtypes = []

        self.GciAbort = self.library.GciAbort
        self.GciAbort.restype = None
        self.GciAbort.argtypes = []

        self.GciCommit = self.library.GciCommit
        self.GciCommit.restype = BoolType
        self.GciCommit.argtypes = []

        self.GciGetSessionId = self.library.GciGetSessionId
        self.GciGetSessionId.restype = GciSessionIdType
        self.GciGetSessionId.argtypes = []

        self.GciReleaseOops = self.library.GciReleaseOops
        self.GciReleaseOops.restype = None
        self.GciReleaseOops.argtypes = [ctypes.POINTER(OopType), ctypes.c_int]

        self.GciIsRemote = self.library.GciIsRemote
        self.GciIsRemote.restype = BoolType
        self.GciIsRemote.argtypes = []

        self.GciSessionIsRemote = self.library.GciSessionIsRemote
        self.GciSessionIsRemote.restype = BoolType
        self.GciSessionIsRemote.argtypes = []

        self.GciIsKindOf = self.library.GciIsKindOf
        self.GciIsKindOf.restype = BoolType
        self.GciIsKindOf.argtypes = [OopType, OopType]

        self.GciExecuteStrFromContext = self.library.GciExecuteStrFromContext
        self.GciExecuteStrFromContext.restype = OopType
        self.GciExecuteStrFromContext.argtypes = [ctypes.c_char_p, OopType, OopType]

        self.GciExecuteFromContext = self.library.GciExecuteFromContext
        self.GciExecuteFromContext.restype = OopType
        self.GciExecuteFromContext.argtypes = [OopType, OopType, OopType]

        self.GciPerform = self.library.GciPerform
        self.GciPerform.restype = OopType
        self.GciPerform.argtypes = [OopType, ctypes.c_char_p, ctypes.POINTER(OopType), ctypes.c_int]

        self.GciPerformSymDbg = self.library.GciPerformSymDbg
        self.GciPerformSymDbg.restype = OopType
        self.GciPerformSymDbg.argtypes = [OopType, OopType, ctypes.POINTER(OopType), ctypes.c_int, ctypes.c_int]

        self.GciNewSymbol = self.library.GciNewSymbol
        self.GciNewSymbol.restype = OopType
        self.GciNewSymbol.argtypes = [ctypes.c_char_p]

        self.GciResolveSymbol = self.library.GciResolveSymbol
        self.GciResolveSymbol.restype = OopType
        self.GciResolveSymbol.argtypes = [ctypes.c_char_p, OopType]

        self.GciResolveSymbolObj = self.library.GciResolveSymbolObj
        self.GciResolveSymbolObj.restype = OopType
        self.GciResolveSymbolObj.argtypes = [OopType, OopType]

        self.GciFetchClass = self.library.GciFetchClass
        self.GciFetchClass.restype = OopType
        self.GciFetchClass.argtypes = [OopType]

        self.GciFetchBytes_ = self.library.GciFetchBytes_
        self.GciFetchBytes_.restype = int64
        self.GciFetchBytes_.argtypes = [OopType, int64, ctypes.POINTER(ByteType), int64]

        self.GciFetchUtf8Bytes_ = self.library.GciFetchUtf8Bytes_
        self.GciFetchUtf8Bytes_.restype = int64
        self.GciFetchUtf8Bytes_.argtypes = [OopType, int64, ctypes.POINTER(ByteType), int64, ctypes.POINTER(OopType), ctypes.c_int]

        self.GciOopToFlt = self.library.GciOopToFlt
        self.GciOopToFlt.restype = ctypes.c_double
        self.GciOopToFlt.argtypes = [OopType]

        self.GciNewUtf8String = self.library.GciNewUtf8String
        self.GciNewUtf8String.restype = OopType
        self.GciNewUtf8String.argtypes = [ctypes.c_char_p, BoolType]

        self.GciFltToOop = self.library.GciFltToOop
        self.GciFltToOop.restype = OopType
        self.GciFltToOop.argtypes = [ctypes.c_double]

        self.GciContinueWith = self.library.GciContinueWith
        self.GciContinueWith.restype = OopType
        self.GciContinueWith.argtypes = [OopType, OopType, ctypes.c_int, ctypes.POINTER(GciErrSType)]

        self.GciClearStack = self.library.GciClearStack
        self.GciClearStack.restype = None
        self.GciClearStack.argtypes = [OopType]

        self.GciSetHaltOnError = self.library.GciSetHaltOnError
        self.GciSetHaltOnError.restype = ctypes.c_int
        self.GciSetHaltOnError.argtypes = [ctypes.c_int]


GemstoneLibrary.register(GciLnk)

#======================================================================================================================
def gembuilder_dealloc(session):
    error = GciErrSType()
    gci.GciShutdown()
    if gci.GciErr(ctypes.byref(error)):
        raise GemstoneError(session, error)

def gembuilder_init(session):
    global gci
    global is_gembuilder_initialised

    gci = GemstoneLibrary.find_library('gcilnk')

    error = GciErrSType()
    if not gci.GciInit() and gci.GciErr(ctypes.byref(error)):
        raise GemstoneError(session, error)
    is_gembuilder_initialised = True
    register(gembuilder_dealloc, session)
    return gci

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

        gci.GciSetNet(stone_name.encode('utf-8'), to_c_bytes(host_username), to_c_bytes(host_password), ''.encode('utf-8'))
        
        clean_login = gci.GciLoginEx(username.encode('utf-8'), self.encrypt_password(password), GCI_LOGIN_PW_ENCRYPTED | GCI_LOGIN_QUIET, 0)
        self.c_session_id = gci.GciGetSessionId()
        if not clean_login:
            gci.GciErr(ctypes.byref(error))
            if self.c_session_id == GCI_INVALID_SESSION_ID.value:
                raise GemstoneError(self, error)
            else:
                warnings.warn(('{}: {}, {}'.format(error.exceptionObj, error.message, error.reason)).replace('\\n', ''), GemstoneWarning)

        current_linked_session = self

    def __repr__(self):
        return '%s(%s)' % (self.__class__.__name__, self.c_session_id)
    
    def encrypt_password(self, unencrypted_password):
        out_buff_size = 0
        encrypted_char = 0
        while encrypted_char == 0:
            out_buff_size = out_buff_size + self.initial_fetch_size
            out_buff = ctypes.create_string_buffer(out_buff_size)
            encrypted_char = gci.GciEncrypt(unencrypted_password.encode('utf-8'), out_buff, out_buff_size)
        return out_buff.value

    def remove_dead_gemstone_objects(self):
        error = GciErrSType()
        unreferenced_gemstone_objects = [oop for oop in self.deallocated_unfreed_gemstone_objects if oop not in self.instances]
        if unreferenced_gemstone_objects:
            dead_oop_count = len(unreferenced_gemstone_objects)
            c_dead_oops = (OopType * dead_oop_count)(*unreferenced_gemstone_objects)
            gci.GciReleaseOops(c_dead_oops, dead_oop_count)
            if gci.GciErr(ctypes.byref(error)):
                raise GemstoneError(self, error)
        self.deallocated_unfreed_gemstone_objects.clear()

    def abort(self):
        error = GciErrSType()
        if not self.is_current_session:
            raise GemstoneApiError('Expected session to be the current session.')
        gci.GciAbort()
        if gci.GciErr(ctypes.byref(error)):
            raise GemstoneError(self, error)

    def begin(self):
        error = GciErrSType()
        if not self.is_current_session:
            raise GemstoneApiError('Expected session to be the current session.')
        gci.GciBegin()
        if gci.GciErr(ctypes.byref(error)):
            raise GemstoneError(self, error)

    def commit(self):
        error = GciErrSType()
        if not self.is_current_session:
            raise GemstoneApiError('Expected session to be the current session.')
        if not gci.GciCommit() and gci.GciErr(ctypes.byref(error)):
            raise GemstoneError(self, error)

    @property
    def is_remote(self):
        error = GciErrSType()
        if not self.is_current_session:
            raise GemstoneApiError('Expected session to be the current session.')
        session_is_remote = gci.GciSessionIsRemote()
        if gci.GciErr(ctypes.byref(error)):
            raise GemstoneError(self, error)
        return bool(session_is_remote)

    @property
    def is_logged_in(self):
        return (self.c_session_id == gci.GciGetSessionId()) and (self.c_session_id != GCI_INVALID_SESSION_ID)

    @property
    def is_current_session(self):
        global current_linked_session
        return self is current_linked_session

    def py_to_string_(self, py_str):
        error = GciErrSType()
        if not self.is_current_session:
            raise GemstoneApiError('Expected session to be the current session.')
        return_oop = gci.GciNewUtf8String(py_str.encode('utf-8'), True)
        if gci.GciErr(ctypes.byref(error)):
            raise GemstoneError(self, error)
        return return_oop

    def py_to_float_(self, py_float):
        if not self.is_current_session:
            raise GemstoneApiError('Expected session to be the current session.')
        error = GciErrSType()
        return_oop = gci.GciFltToOop(py_float)
        if return_oop == OOP_NIL.value and gci.GciErr(ctypes.byref(error)):
            raise GemstoneError(self, error)
        return return_oop

    def execute(self, source, context=None, symbol_list=None):
        if not self.is_current_session:
            raise GemstoneApiError('Expected session to be the current session.')
        error = GciErrSType()
        if isinstance(source, str):
            return_oop = gci.GciExecuteStrFromContext(source.encode('utf-8'), context.oop if context else OOP_NO_CONTEXT, 
                                                      symbol_list.oop if symbol_list else OOP_NIL)
        elif isinstance(source, GemObject):
            return_oop = gci.GciExecuteFromContext(source.oop, context.oop if context else OOP_NO_CONTEXT, 
                                                   symbol_list.oop if symbol_list else OOP_NIL)
        else:
            raise GemstoneApiError('Source is type {}.Expected source to be a str or GemObject'.format(source.__class__.__name__))
        if return_oop == OOP_NIL.value and gci.GciErr(ctypes.byref(error)):
            raise GemstoneError(self, error)
        return self.get_or_create_gem_object(return_oop)

    def new_symbol(self, py_string):
        if not self.is_current_session:
            raise GemstoneApiError('Expected session to be the current session.')
        error = GciErrSType()
        return_oop = gci.GciNewSymbol(py_string.encode('utf-8'))
        if gci.GciErr(ctypes.byref(error)):
            raise GemstoneError(self, error)
        return self.get_or_create_gem_object(return_oop)

    def resolve_symbol(self, symbol, symbol_list=None):
        if not self.is_current_session:
            raise GemstoneApiError('Expected session to be the current session.')
        error = GciErrSType()
        if isinstance(symbol, str):
            return_oop = gci.GciResolveSymbol(symbol.encode('utf-8') , symbol_list.oop if symbol_list else OOP_NIL)
        elif isinstance(symbol, GemObject):
            return_oop = gci.GciResolveSymbolObj(symbol.oop, symbol_list.oop if symbol_list else OOP_NIL)
        else:
            raise GemstoneApiError('Symbol is type {}.Expected symbol to be a str or GemObject'.format(symbol.__class__.__name__))
        if return_oop == OOP_ILLEGAL.value and gci.GciErr(ctypes.byref(error)):
            raise GemstoneError(self, error)
        return self.get_or_create_gem_object(return_oop)
        
    def log_out(self):
        if not self.is_current_session:
            raise GemstoneApiError('Expected session to be the current session.')
        error = GciErrSType()
        gci.GciLogout()
        if gci.GciErr(ctypes.byref(error)):
            raise GemstoneError(self, error)
        self.c_session_id = GCI_INVALID_SESSION_ID
        global current_linked_session
        current_linked_session = None

    def object_is_kind_of(self, instance, a_class):
        if not self.is_current_session:
            raise GemstoneApiError('Expected session to be the current session.')
        error = GciErrSType()
        is_kind_of_result = gci.GciIsKindOf(instance.oop, a_class.oop)
        if is_kind_of_result == False and gci.GciErr(ctypes.byref(error)):
            raise GemstoneError(self, error)
        return bool(is_kind_of_result)

    def object_gemstone_class(self, instance):
        if not self.is_current_session:
            raise GemstoneApiError('Expected session to be the current session.')
        error = GciErrSType()
        return_oop = gci.GciFetchClass(instance.oop)
        if return_oop == OOP_NIL.value and gci.GciErr(ctypes.byref(error)):
           raise GemstoneError(self, error)
        return self.get_or_create_gem_object(return_oop)

    def object_float_to_py(self, instance):
        if not self.is_current_session:
            raise GemstoneApiError('Expected session to be the current session.')
        error = GciErrSType()
        result = gci.GciOopToFlt(instance.oop)
        if result != result and gci.GciErr(ctypes.byref(error)):
            raise GemstoneError(self, error)
        return result

    def object_string_to_py(self, instance):
        if not self.is_current_session:
            raise GemstoneApiError('Expected session to be the current session.')
        start_index = 1
        num_bytes  = self.initial_fetch_size
        bytes_returned = num_bytes
        error = GciErrSType()
        py_bytes = b''
        utf8_string = OopType(OOP_NIL.value)

        while bytes_returned == num_bytes:
            dest = (ByteType * (num_bytes + 1))()
            bytes_returned = gci.GciFetchUtf8Bytes_(instance.oop, start_index, dest, num_bytes, ctypes.byref(utf8_string), 0)
            if bytes_returned == 0 and gci.GciErr(ctypes.byref(error)):
                raise GemstoneError(self, error)

            py_bytes += bytearray(dest[:bytes_returned])
            start_index = start_index + num_bytes
            if utf8_string.value != OOP_NIL.value:
                gci.GciReleaseOops(ctypes.byref(utf8_string), 1)
                if gci.GciErr(ctypes.byref(error)):
                    raise GemstoneError(self, error)
        return py_bytes.decode('utf-8')

    def object_latin1_to_py(self, instance):
        return self.object_bytes_to_py(instance).decode('latin-1')

    def object_bytes_to_py(self, instance):
        if not self.is_current_session:
            raise GemstoneApiError('Expected session to be the current session.')

        start_index = 1
        num_bytes  = self.initial_fetch_size
        bytes_returned = num_bytes
        error = GciErrSType()

        py_bytes = b''
        while bytes_returned == num_bytes:
            dest = (ByteType * (num_bytes + 1))()
            bytes_returned = gci.GciFetchBytes_(instance.oop, start_index, dest, num_bytes)
            if bytes_returned == 0 and gci.GciErr(ctypes.byref(error)):
                raise GemstoneError(self, error)

            py_bytes +=  bytearray(dest[:bytes_returned])
            start_index = start_index + num_bytes
        return py_bytes

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
            return_oop = gci.GciPerform(instance.oop, selector.encode('utf-8'), cargs, len(args))
        else:
            return_oop = gci.GciPerformSymDbg(instance.oop, selector.oop, cargs, len(args), 0)

        if return_oop == OOP_NIL.value and gci.GciErr(ctypes.byref(error)):
            raise GemstoneError(self, error)
        return self.get_or_create_gem_object(return_oop)

    def object_continue_with(self, gemstone_process, continue_with_error_oop, replace_top_of_stack_oop):
        error = GciErrSType()
        return_oop = gci.GciContinueWith(gemstone_process.oop, replace_top_of_stack_oop, 0, continue_with_error_oop)
        if return_oop == OOP_ILLEGAL.value and gci.GciErr(ctypes.byref(error)):
            raise GemstoneError(self, error)
        return self.get_or_create_gem_object(return_oop)

    def object_clear_stack(self, gemstone_process):
        error = GciErrSType()
        success = gci.GciClearStack(gemstone_process.oop)
        if gci.GciErr(ctypes.byref(error)):        
            raise GemstoneError(self, error)
    
#======================================================================================================================
