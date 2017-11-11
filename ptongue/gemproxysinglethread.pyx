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
cdef extern from "gci.hf":
   int GciSessionIdType
   
   void GciInitAppName(const char *applicationName, bint logWarnings)
   void GciSetNet(const char StoneName[], const char HostUserId[], const char HostPassword[], const char GemService[])
   bint GciInit(void)
   void GciShutdown(void)
   bint GciLogin(const char gemstoneUsername[], const char gemstonePassword[])
   bint GciErr(GciErrSType *errorReport)
   GciSessionIdType GciGetSessionId(void)
   void GciSetSessionId(GciSessionIdType sessionId)
   OopType GciExecuteStrFromContext(const char source[], OopType contextObject, OopType symbolList)
   OopType GciPerform(OopType receiver, const char selector[], const OopType args[], int numArgs)


#======================================================================================================================


#======================================================================================================================

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

    def perform(self, selector, *args):
        with self.session.as_current_session():
            cdef GciErrSType error
            assert isinstance(selector, str), 'TODO: raise error to say only str allowed for selector'

            cdef OopType return_oop = OOP_NIL
            cdef OopType* cargs = <OopType *>malloc(len(args) * sizeof(OopType))
            try:
                for i in xrange(len(args)):
                    cargs[i] = args[i].oop

                    return_oop = GciPerform(self.c_oop, to_c_bytes(selector), cargs, len(args))
            finally:
                free(cargs)
            if return_oop == OOP_NIL and GciErr(&error):  #TODO: check this logic: how do we know an error ocurred? should we always call this to check?
                raise make_GemstoneError(self, error)
            return self.session.get_or_create_gem_object(return_oop)

    def __str__(self):
        return '<%s object with oop %s>' % (self.__class__, self.c_oop)

#======================================================================================================================
cdef class Session:
    cdef GciSessionIdType c_session_id
    cdef object instances
    def __cinit__(self, str username, str password, str stone_name='gs64stone',
                  str host_username=None, str host_password='',
                  str netldi_task=''):
        self.initial_fetch_size = 200
        cdef GciErrSType error
        cdef char* c_host_username = NULL
        if host_username:
            c_host_username = to_c_bytes(host_username)

        self.instances = WeakValueDictionary()

        GciSetNet(stone_name.encode('utf-8'),
                  c_host_username,    
                  host_password.encode('utf-8'),
                  netldi_task.encode('utf-8'))

        clean_login = GciLogin(username.encode('utf-8'), password.encode('utf-8'))
        self.c_session_id = GciGetSessionId()
        if not clean_login:
            GciErr(&error)
            if self.c_session_id == GCI_INVALID_SESSION_ID:
                raise make_GemstoneError(self, error)
            else:
                pass # TODO: deal with warning

    def get_or_create_gem_object(self, oop):
        try:
            return self.instances[oop]
        except KeyError:
            new_gem_object = GemObject(self, oop)
            self.instances[oop] = new_gem_object
            return new_gem_object

    @contextlib.contextmanager
    def as_current_session(self):
        cdef GciSessionIdType c_current_session_id = GciGetSessionId()
        self.set_as_current_session()
        try:
            yield
        finally:
            GciSetSessionId(c_current_session_id)

    @property
    def is_current_session(self):
        return self.c_session_id == GciGetSessionId()

    def set_as_current_session(self):
        GciSetSessionId(self.c_session_id)
        
    def log_out(self):
        with self.as_current_session():
            GciLogout()
        #TODO: should we check for errors??

    def execute(self, str source_str, GemObject context=None, GemObject symbol_list=None):
        with self.as_current_session():
            cdef GciErrSType error
            cdef char *c_source_str = NULL
            if source_str:
                c_source_str = to_c_bytes(source_str)

            OopType GciExecuteStrFromContext(const char source[], OopType contextObject, OopType symbolList)
   
            cdef OopType return_oop = GciExecuteStrFromContext(c_source_str, context.oop if context else OOP_NO_CONTEXT, 
                                                               symbol_list.oop if symbol_list else OOP_NIL)

            if GciErr(&error):  #TODO: check this logic: how do we know an error ocurred? should we always call this to check?
                raise make_GemstoneError(self, error)
            return self.get_or_create_gem_object(return_oop)

    
#======================================================================================================================
