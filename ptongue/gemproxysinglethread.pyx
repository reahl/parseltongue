from libc.stdlib cimport *
from libc.string cimport memcpy
from contextlib import contextmanager
from atexit import register
import warnings

from gemproxy cimport *

#======================================================================================================================
cdef extern from "gci.hf":
    void GciInitAppName(const char *applicationName, bint logWarnings)
    void GciSetNet(const char StoneName[], const char HostUserId[], const char HostPassword[], const char GemService[])
    bint GciInit()
    void GciShutdown()
    void GciUnload()
    bint GciLogin(const char gemstoneUsername[], const char gemstonePassword[])
    void GciLogout()
    bint GciErr(GciErrSType *errorReport)
    void GciClearStack(OopType aGsProcess)
    void GciBegin()
    void GciAbort()
    bint GciCommit()
    GciSessionIdType GciGetSessionId()
    void GciSetSessionId(GciSessionIdType sessionId)
    bint GciIsRemote()
    bint GciSessionIsRemote()
    bint GciIsKindOf(OopType anObj, OopType aClassHistory)
    OopType GciExecuteStrFromContext(const char source[], OopType contextObject, OopType symbolList)
    OopType GciExecuteFromContext(OopType source, OopType contextObject, OopType symbolList)
    OopType GciPerform(OopType receiver, const char selector[], const OopType args[], int numArgs)
    OopType GciPerformSymDbg(OopType receiver, OopType selector, const OopType args[], int numArgs, int flags)
    OopType GciNewSymbol(const char *cString)
    OopType GciResolveSymbol(const char *cString , OopType symbolList)
    OopType GciResolveSymbolObj(OopType aString, OopType symbolList)

#======================================================================================================================
cdef bint is_init = False
cdef LinkedSession current_linked_session = None

#======================================================================================================================
cdef gembuilder_init():
    cdef GciErrSType error
    if not GciInit() and GciErr(&error):
        raise make_GemstoneError(None, error)
    is_init = True

@register
def gembuilder_dealoc():
    cdef GciErrSType error
    GciShutdown();
    if GciErr(&error):
        raise make_GemstoneError(None, error)

#======================================================================================================================
class GemstoneWarning(Warning):
    pass

#======================================================================================================================
cdef class LinkedSession(GemstoneSession):
    cdef GciSessionIdType c_session_id
    def __cinit__(self, str username, str password):
        cdef GciErrSType error
        cdef char* c_host_username = NULL

        if not is_init:
            gembuilder_init()

        global current_linked_session
        if current_linked_session != None:
            raise GemstoneApiError('There is an active linked session. Can not create another session.')

        is_logged_in = True

        if GciErr(&error):
            raise make_GemstoneError(self, error)

        clean_login = GciLogin(username.encode('utf-8'), password.encode('utf-8'))
        self.c_session_id = GciGetSessionId()
        if not clean_login:
            GciErr(&error)
            if self.c_session_id == GCI_INVALID_SESSION_ID:
                raise make_GemstoneError(self, error)
            else:
                warnings.warn(('{}: {}, {}'.format(self.exception_obj, self.message, self.reason)).replace('\\n', ''),GemstoneWarning)

        current_linked_session = self

    def abort(self):
        cdef GciErrSType error
        if not self.is_current_session:
            raise GemstoneApiError('Expected session to be the current session.')
        GciAbort()
        if GciErr(&error):
            raise make_GemstoneError(self, error)

    def begin(self):
        cdef GciErrSType error
        if not self.is_current_session:
            raise GemstoneApiError('Expected session to be the current session.')
        GciBegin()
        if GciErr(&error):
            raise make_GemstoneError(self, error)

    def commit(self):
        cdef GciErrSType error
        if not self.is_current_session:
            raise GemstoneApiError('Expected session to be the current session.')
        if not GciCommit() and GciErr(&error):
            raise make_GemstoneError(self, error)

    @property
    def is_remote(self):
        if not self.is_current_session:
            raise GemstoneApiError('Expected session to be the current session.')
        return GciSessionIsRemote()

    @property
    def is_logged_in(self):
        return self.c_session_id != GCI_INVALID_SESSION_ID

    @property
    def is_current_session(self):
        return self.c_session_id == GciGetSessionId()

    def execute(self, source, GemObject context=None, GemObject symbol_list=None):
        cdef GciErrSType error
        cdef OopType return_oop 
        if not self.is_current_session:
            raise GemstoneApiError('Expected session to be the current session.')
        if isinstance(source, str):
            return_oop = GciExecuteStrFromContext(source.encode('utf-8'), context.oop if context else OOP_NO_CONTEXT, 
                                                           symbol_list.oop if symbol_list else OOP_NIL)
        elif isinstance(source, GemObject):
            return_oop = GciExecuteFromContext(source.oop, context.oop if context else OOP_NO_CONTEXT, 
                                                           symbol_list.oop if symbol_list else OOP_NIL)
        else:
            raise GemstoneApiError('Source is type {}.Expected source to be a str or GemObject'.format(source.__class__.__name__))
        if return_oop == OOP_NIL and GciErr(&error):
            raise make_GemstoneError(self, error)
        return self.get_or_create_gem_object(return_oop)

    def new_symbol(self, str py_string):
        cdef GciErrSType error
        cdef OopType return_oop
        if not self.is_current_session:
            raise GemstoneApiError('Expected session to be the current session.')
        return_oop = GciNewSymbol(py_string.encode('utf-8'))
        if GciErr(&error):
            raise make_GemstoneError(self, error)
        return self.get_or_create_gem_object(return_oop)

    def resolve_symbol(self, symbol, GemObject symbol_list=None):
        cdef GciErrSType error
        cdef OopType return_oop = OOP_NIL
        if not self.is_current_session:
            raise GemstoneApiError('Expected session to be the current session.')
        if isinstance(symbol, str):
            return_oop = GciResolveSymbol(symbol.encode('utf-8') , symbol_list.oop if symbol_list else OOP_NIL)
        elif isinstance(symbol, GemObject):
            return_oop = GciResolveSymbolObj(symbol.oop, symbol_list.oop if symbol_list else OOP_NIL)
        else:
            raise GemstoneApiError('Symbol is type {}.Expected symbol to be a str or GemObject'.format(symbol.__class__.__name__))
        if return_oop == OOP_ILLEGAL and GciErr(&error):
            raise make_GemstoneError(self, error)
        return self.get_or_create_gem_object(return_oop)
        
    def log_out(self):
        cdef GciErrSType error
        if not self.is_current_session:
            raise GemstoneApiError('Expected session to be the current session.')
        GciLogout()
        if GciErr(&error):
            raise make_GemstoneError(self, error)
        self.c_session_id = GCI_INVALID_SESSION_ID
        global current_linked_session
        current_linked_session = None

    def object_is_kind_of(self, GemObject instance, GemObject a_class):
        cdef GciErrSType error
        cdef int is_kind_of_result
        if not self.is_current_session:
            raise GemstoneApiError('Expected session to be the current session.')
        is_kind_of_result = GciIsKindOf(instance.c_oop, a_class.c_oop)
        if is_kind_of_result == False and GciErr(&error):
            raise make_GemstoneError(self, error)
        return <bint>is_kind_of_result

    def object_perform(self, GemObject instance, selector, *args):
        if not isinstance(selector, (str, GemObject)):
            raise GemstoneApiError('Selector is type {}.Expected selector to be a str or GemObject'.format(selector.__class__.__name__))
        cdef GciErrSType error
        cdef OopType* cargs
        cdef OopType return_oop = OOP_NIL
        if not self.is_current_session:
            raise GemstoneApiError('Expected session to be the current session.')
        cargs = <OopType *>malloc(len(args) * sizeof(OopType))
        try:
            for i in xrange(len(args)):
                cargs[i] = args[i].oop
            if isinstance(selector, str):
                return_oop = GciPerform(instance.c_oop, selector.encode('utf-8'), cargs, len(args))
            else:
                return_oop = GciPerformSymDbg(instance.c_oop, selector, cargs, len(args), False)
        finally:
            free(cargs)
        if return_oop == OOP_NIL and GciErr(&error):
            raise make_GemstoneError(self, error)
        return self.get_or_create_gem_object(return_oop)

#======================================================================================================================
