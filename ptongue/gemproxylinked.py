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
    """
    GemStone library wrapper for 'gcilnk' - the linked session interface to GemStone.
    
    This class provides a Python wrapper around the C functions in the GemStone
    linked API (gcilnk). It maps C function signatures to Python methods using ctypes,
    allowing direct calls to the GemStone C API from Python.
    
    Supported GemStone versions range from 3.4.0 to 3.7.9999.
    
    This library is used for creating linked sessions where the GCI is linked 
    directly with your GemStone session rather than using remote procedure calls.
    """
    short_name = 'gcilnk'
    min_version = '3.4.0'
    max_version = '3.7.9999'
    
    def __init__(self, lib_path):
        """
        Initialize a GciLnk instance by loading the specified library path.
        
        Maps all the required C functions to Python methods using ctypes.
        
        Parameters
        ----------
        lib_path : str
            Path to the gcilnk shared library.
        """
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
    """
    A session that directly links to a GemStone database using the linked GCI API.
    
    LinkedSession provides a client that runs in the same process as the GemStone server
    (as opposed to RPCSession which connects to a remote server). Only one active 
    LinkedSession can exist at a time per process.
    
    :param username: GemStone user account name used for authentication
    :param password: GemStone password used for authentication
    :param stone_name: Name of the GemStone repository to connect to, defaults to 'gs64stone'
    :param host_username: If specified, the OS username used for connecting to the server
    :param host_password: Password for host_username, if required, defaults to empty string
    """
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
        """
        Return a string representation of the LinkedSession instance.
        
        :return: A string in the format 'LinkedSession(session_id)'
        """
        return '%s(%s)' % (self.__class__.__name__, self.c_session_id)
    
    def encrypt_password(self, unencrypted_password):
        """
        Encrypt a password for secure transmission to GemStone.
        
        Uses the GemStone encryption mechanism to create a secure password 
        representation suitable for sending over the network.
        
        :param unencrypted_password: The plaintext password to encrypt
        :return: The encrypted password ready for use with GciLoginEx
        """
        out_buff_size = 0
        encrypted_char = 0
        while encrypted_char == 0:
            out_buff_size = out_buff_size + self.initial_fetch_size
            out_buff = ctypes.create_string_buffer(out_buff_size)
            encrypted_char = gci.GciEncrypt(unencrypted_password.encode('utf-8'), out_buff, out_buff_size)
        return out_buff.value

    def remove_dead_gemstone_objects(self):
        """
        Release GemStone objects that are no longer referenced by Python.
        
        This method cleans up objects that were previously held by Python
        but are no longer referenced. It prevents memory leaks by informing
        GemStone that these objects can be released.
        
        :raises GemstoneError: If an error occurs during the GemStone operation
        """
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
        """
        Abort the current transaction.
        
        Any changes made since the last commit or abort will be discarded.
        
        :raises GemstoneApiError: If this session is not the current active session
        :raises GemstoneError: If an error occurs during the GemStone operation
        """
        error = GciErrSType()
        if not self.is_current_session:
            raise GemstoneApiError('Expected session to be the current session.')
        gci.GciAbort()
        if gci.GciErr(ctypes.byref(error)):
            raise GemstoneError(self, error)

    def begin(self):
        """
        Begin a new transaction.
        
        If there is an active transaction, it is aborted before starting a new one.
        
        :raises GemstoneApiError: If this session is not the current active session
        :raises GemstoneError: If an error occurs during the GemStone operation
        """
        error = GciErrSType()
        if not self.is_current_session:
            raise GemstoneApiError('Expected session to be the current session.')
        gci.GciBegin()
        if gci.GciErr(ctypes.byref(error)):
            raise GemstoneError(self, error)

    def commit(self):
        """
        Commit the current transaction.
        
        Write all changes made in the current transaction to the database.
        
        :raises GemstoneApiError: If this session is not the current active session
        :raises GemstoneError: If the commit fails or an error occurs during the GemStone operation
        """
        error = GciErrSType()
        if not self.is_current_session:
            raise GemstoneApiError('Expected session to be the current session.')
        if not gci.GciCommit() and gci.GciErr(ctypes.byref(error)):
            raise GemstoneError(self, error)

    @property
    def is_remote(self):
        """
        Determine whether this session is connected to a remote Gem.
        
        For a LinkedSession, this should typically return False unless 
        the session was configured in a special way.
        
        :return: True if connected to a remote Gem, False if using a linked Gem
        :raises GemstoneApiError: If this session is not the current active session
        :raises GemstoneError: If an error occurs during the GemStone operation
        """
        error = GciErrSType()
        if not self.is_current_session:
            raise GemstoneApiError('Expected session to be the current session.')
        session_is_remote = gci.GciSessionIsRemote()
        if gci.GciErr(ctypes.byref(error)):
            raise GemstoneError(self, error)
        return bool(session_is_remote)

    @property
    def is_logged_in(self):
        """
        Check if this session is currently logged in.
        
        :return: True if the session is logged in, False otherwise
        """
        return (self.c_session_id == gci.GciGetSessionId()) and (self.c_session_id != GCI_INVALID_SESSION_ID)

    @property
    def is_current_session(self):
        """
        Check if this session is the current active linked session.
        
        Only one linked session can be active at a time in a process.
        
        :return: True if this is the current active session, False otherwise
        """
        global current_linked_session
        return self is current_linked_session

    def py_to_string_(self, py_str):
        """
        Convert a Python string to a GemStone string object.
        
        :param py_str: The Python string to convert
        :return: The object ID (oop) of the new GemStone string
        :raises GemstoneApiError: If this session is not the current active session
        :raises GemstoneError: If an error occurs during the GemStone operation
        """
        error = GciErrSType()
        if not self.is_current_session:
            raise GemstoneApiError('Expected session to be the current session.')
        return_oop = gci.GciNewUtf8String(py_str.encode('utf-8'), True)
        if gci.GciErr(ctypes.byref(error)):
            raise GemstoneError(self, error)
        return return_oop

    def py_to_float_(self, py_float):
        """
        Convert a Python float to a GemStone Float or SmallDouble object.
        
        :param py_float: The Python float to convert
        :return: The object ID (oop) of the new GemStone float
        :raises GemstoneApiError: If this session is not the current active session
        :raises GemstoneError: If an error occurs during the GemStone operation
        """
        if not self.is_current_session:
            raise GemstoneApiError('Expected session to be the current session.')
        error = GciErrSType()
        return_oop = gci.GciFltToOop(py_float)
        if return_oop == OOP_NIL.value and gci.GciErr(ctypes.byref(error)):
            raise GemstoneError(self, error)
        return return_oop

    def execute(self, source, context=None, symbol_list=None):
        """
        Execute GemStone Smalltalk code.
        
        :param source: The Smalltalk code to execute, either as a Python string or 
                      a GemStone string object
        :param context: The context object in which to execute the code, defaults to None
                       (which uses the default nil context)
        :param symbol_list: The symbol list to use for name resolution, defaults to None
                           (which uses the default symbol list from the user's profile)
        :return: The result of executing the Smalltalk code
        :raises GemstoneApiError: If this session is not the current active session,
                                 or if the source is not of the expected type
        :raises GemstoneError: If an error occurs during execution
        """
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
        """
        Create a new GemStone Symbol object.
        
        :param py_string: The Python string to be converted to a Symbol
        :return: The new Symbol object
        :raises GemstoneApiError: If this session is not the current active session
        :raises GemstoneError: If an error occurs, such as if the string is too long to be a Symbol
        """
        if not self.is_current_session:
            raise GemstoneApiError('Expected session to be the current session.')
        error = GciErrSType()
        return_oop = gci.GciNewSymbol(py_string.encode('utf-8'))
        if gci.GciErr(ctypes.byref(error)):
            raise GemstoneError(self, error)
        return self.get_or_create_gem_object(return_oop)

    def resolve_symbol(self, symbol, symbol_list=None):
        """
        Resolve a symbol to its value in a symbol dictionary.
        
        :param symbol: The name of the symbol to resolve, either as a Python string
                      or a GemStone Symbol object
        :param symbol_list: The symbol list to use for resolution, defaults to None
                           (which uses the default symbol list from the user's profile)
        :return: The object that the symbol refers to
        :raises GemstoneApiError: If this session is not the current active session,
                                 or if symbol is not of the expected type
        :raises GemstoneError: If the symbol cannot be resolved or another error occurs
        """
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
        """
        Log out from the GemStone session.
        
        After log out, the session can no longer be used.
        
        :raises GemstoneApiError: If this session is not the current active session
        :raises GemstoneError: If an error occurs during logout
        """
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
        """
        Check if an object is an instance of a specified class or one of its subclasses.
        
        :param instance: The object to check
        :param a_class: The class to compare against
        :return: True if instance is of the specified class or a subclass, False otherwise
        :raises GemstoneApiError: If this session is not the current active session
        :raises GemstoneError: If an error occurs during the check
        """
        if not self.is_current_session:
            raise GemstoneApiError('Expected session to be the current session.')
        error = GciErrSType()
        is_kind_of_result = gci.GciIsKindOf(instance.oop, a_class.oop)
        if is_kind_of_result == False and gci.GciErr(ctypes.byref(error)):
            raise GemstoneError(self, error)
        return bool(is_kind_of_result)

    def object_gemstone_class(self, instance):
        """
        Get the class of a GemStone object.
        
        :param instance: The object whose class is to be determined
        :return: The class of the specified object
        :raises GemstoneApiError: If this session is not the current active session
        :raises GemstoneError: If an error occurs during the operation
        """
        if not self.is_current_session:
            raise GemstoneApiError('Expected session to be the current session.')
        error = GciErrSType()
        return_oop = gci.GciFetchClass(instance.oop)
        if return_oop == OOP_NIL.value and gci.GciErr(ctypes.byref(error)):
           raise GemstoneError(self, error)
        return self.get_or_create_gem_object(return_oop)

    def object_float_to_py(self, instance):
        """
        Convert a GemStone Float or SmallDouble to a Python float.
        
        :param instance: A GemStone Float or SmallDouble object
        :return: The Python float value
        :raises GemstoneApiError: If this session is not the current active session
        :raises GemstoneError: If the object is not a Float or SmallDouble, or if another error occurs
        """
        if not self.is_current_session:
            raise GemstoneApiError('Expected session to be the current session.')
        error = GciErrSType()
        result = gci.GciOopToFlt(instance.oop)
        if result != result and gci.GciErr(ctypes.byref(error)):
            raise GemstoneError(self, error)
        return result

    def object_string_to_py(self, instance):
        """
        Convert a GemStone String to a Python string.
        
        This method supports various string types in GemStone, including
        String, DoubleByteString, QuadByteString, and Utf8.
        
        :param instance: A GemStone string object
        :return: The Python string representation
        :raises GemstoneApiError: If this session is not the current active session
        :raises GemstoneError: If the object is not a string, or if another error occurs
        """
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
        """
        Convert a GemStone String or ByteArray to a Python string using Latin-1 encoding.
        
        :param instance: A GemStone string or byte object
        :return: The Python string representation using Latin-1 encoding
        :raises GemstoneApiError: If this session is not the current active session
        :raises GemstoneError: If an error occurs during conversion
        """
        return self.object_bytes_to_py(instance).decode('latin-1')

    def object_bytes_to_py(self, instance):
        """
        Convert a GemStone ByteArray or byte-based object to Python bytes.
        
        :param instance: A GemStone byte object
        :return: The Python bytes representation
        :raises GemstoneApiError: If this session is not the current active session
        :raises GemstoneError: If the object is not a byte object, or if another error occurs
        """
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
        """
        Send a message to a GemStone object.
        
        :param instance: The receiver of the message (the object to which the message is sent)
        :param selector: The message selector, either as a Python string or a GemStone Symbol
        :param args: The arguments to the message
        :return: The result of the message send
        :raises GemstoneApiError: If this session is not the current active session,
                                 or if the selector is not of the expected type
        :raises GemstoneError: If an error occurs during the message send,
                              such as if the object does not understand the selector
        """
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
        """
        Continue execution of a halted GemStone process.
        
        Used primarily for debugging or exception handling.
        
        :param gemstone_process: The GsProcess object that is halted
        :param continue_with_error_oop: If not None, an error object to continue with
        :param replace_top_of_stack_oop: Optional value to replace the top of the stack before continuing
        :return: The result of continuing execution
        :raises GemstoneError: If an error occurs during the operation
        """
        error = GciErrSType()
        return_oop = gci.GciContinueWith(gemstone_process.oop, replace_top_of_stack_oop, 0, continue_with_error_oop)
        if return_oop == OOP_ILLEGAL.value and gci.GciErr(ctypes.byref(error)):
            raise GemstoneError(self, error)
        return self.get_or_create_gem_object(return_oop)

    def object_clear_stack(self, gemstone_process):
        """
        Clear the execution stack of a GemStone process.
        
        This effectively terminates execution of the process.
        
        :param gemstone_process: The GsProcess object whose stack is to be cleared
        :raises GemstoneError: If an error occurs during the operation
        """
        error = GciErrSType()
        success = gci.GciClearStack(gemstone_process.oop)
        if gci.GciErr(ctypes.byref(error)):        
            raise GemstoneError(self, error)
#======================================================================================================================
