from libc.stdlib cimport *
from libc.string cimport memcpy

from gemproxy cimport *

#======================================================================================================================
cdef extern from "gcits.hf":
    char* GciTsEncrypt(const char* password, char *outBuf, size_t outBuffSize)
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
    bint GciTsReleaseObjs(GciSession sess, OopType *buf, int count, GciErrSType *err)

#======================================================================================================================
cdef class RPCSession(GemstoneSession):
    cdef GciSession c_session
    def __cinit__(self, str username, str password, str stone_name='gs64stone',
                  str host_username=None, str host_password='',
                  str netldi_task='gemnetobject'):
        cdef GciErrSType error
        cdef char* c_host_username = NULL
        if host_username:
            c_host_username = to_c_bytes(host_username)

        self.c_session = GciTsLogin(stone_name.encode('utf-8'),
                                    c_host_username,
                                    self.encrypt_password(host_password),
                                    True,
                                    netldi_task.encode('utf-8'),
                                    username.encode('utf-8'),
                                    self.encrypt_password(password),
                                    GCI_LOGIN_PW_ENCRYPTED, 0, &error)
        if self.c_session == NULL:
            raise make_GemstoneError(self, error)

    def encrypt_password(self, str unencrypted_password):
        cdef char *out_buff
        cdef bytes encrypted_password
        cdef unsigned int out_buff_size = 0
        cdef char *encrypted_char = NULL
        while(encrypted_char == NULL):
            out_buff_size = out_buff_size + self.initial_fetch_size
            out_buff = <char *>malloc((out_buff_size) * sizeof(char))
            try:
                encrypted_char = GciTsEncrypt(unencrypted_password.encode('utf-8'), out_buff, out_buff_size)
                if encrypted_char != NULL:
                    encrypted_password = out_buff
            finally:
                free(out_buff)
        return encrypted_password

    def remove_dead_gemstone_objects(self):
        cdef GciErrSType error
        cdef object dead_oops = []
        cdef OopType *c_dead_oops
        unreferenced_gemstone_objects = [oop for oop in self.deallocated_unfreed_gemstone_objects if oop not in self.instances]
        dead_oops.extend(unreferenced_gemstone_objects)
        if dead_oops:
            c_dead_oops = <OopType *>malloc(len(dead_oops) * sizeof(OopType))
            try:
                for index in xrange(0, len(dead_oops)):
                    c_dead_oops[index] = dead_oops[index] 
                if not GciTsReleaseObjs(self.c_session, c_dead_oops, len(dead_oops), &error):
                    raise make_GemstoneError(self, error)
            finally:
                free(c_dead_oops)
        self.deallocated_unfreed_gemstone_objects.clear()

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

    def py_to_string_(self, str py_str):
        cdef GciErrSType error
        cdef OopType return_oop
        return_oop = GciTsNewUtf8String(self.c_session, py_str.encode('utf-8'), True, &error)
        if return_oop == OOP_ILLEGAL:
            raise make_GemstoneError(self, error)
        return return_oop

    def py_to_float_(self, py_float):
        cdef GciErrSType error
        cdef OopType return_oop = OOP_NIL
        return_oop = GciTsDoubleToOop(self.c_session, py_float, &error)
        if return_oop == OOP_ILLEGAL:
            raise make_GemstoneError(self, error)
        return return_oop

    def execute(self, source, GemObject context=None, GemObject symbol_list=None):
        cdef GciErrSType error
        cdef OopType return_oop
        if isinstance(source, str):
            return_oop = GciTsExecute(self.c_session, source.encode('utf-8'), OOP_CLASS_Utf8,
                                               context.oop if context else OOP_NIL, 
                                               symbol_list.oop if symbol_list else OOP_NIL,
                                               0, 0,  &error)
        elif isinstance(source, GemObject):
            return_oop = GciTsExecute(self.c_session, NULL, source.oop,
                                               context.oop if context else OOP_NIL, 
                                               symbol_list.oop if symbol_list else OOP_NIL,
                                               0, 0,  &error)
        else:
            raise GemstoneApiError('Source is type {}.Expected source to be a str or GemObject'.format(source.__class__.__name__))
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
            raise GemstoneApiError('Symbol is type {}.Expected symbol to be a str or GemObject'.format(symbol.__class__.__name__))
        if return_oop == OOP_ILLEGAL:
            raise make_GemstoneError(self, error)
        return self.get_or_create_gem_object(return_oop)
           
    def log_out(self):
        cdef GciErrSType error
        if not GciTsLogout(self.c_session, &error):
            raise make_GemstoneError(self, error)

    def object_is_kind_of(self, GemObject instance, GemObject a_class):
        cdef GciErrSType error
        cdef int is_kind_of_result = GciTsIsKindOf(self.c_session, instance.c_oop, a_class.c_oop, &error)
        if is_kind_of_result == -1:
            raise make_GemstoneError(self, error)
        return <bint>is_kind_of_result

    def object_gemstone_class(self, GemObject instance):
        cdef GciErrSType error
        cdef OopType return_oop = GciTsFetchClass(self.c_session, instance.c_oop, &error)
        if return_oop == OOP_ILLEGAL:
           raise make_GemstoneError(self, error)
        return self.get_or_create_gem_object(return_oop)

    def object_float_to_py(self, GemObject instance):
        cdef GciErrSType error
        cdef double result = 0
        if not GciTsOopToDouble(self.c_session, instance.c_oop, &result, &error):
            raise make_GemstoneError(self, error)
        return result

    def object_string_to_py(self, GemObject instance):
        cdef GciErrSType error
        cdef int64 max_bytes
        cdef ByteType *c_string
        cdef int64 required_size = self.initial_fetch_size
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
                bytes_returned = GciTsFetchUtf8(self.c_session,
                         instance.c_oop, c_string, max_bytes, &required_size, &error)

                if bytes_returned == -1:
                    raise make_GemstoneError(self, error)

                c_string[bytes_returned] = '\0'
                py_bytes = c_string
            finally:
                free (c_string)

        return py_bytes.decode('utf-8')

    def object_latin1_to_py(self, GemObject instance):
        cdef int64 start_index = 1
        cdef int64 num_bytes  = self.initial_fetch_size
        cdef int64 bytes_returned = num_bytes
        cdef GciErrSType error
        cdef bytes py_bytes = b''
        cdef ByteType* dest
        while bytes_returned == num_bytes:
            dest = <ByteType *>malloc((num_bytes + 1) * sizeof(ByteType))
            try:
                bytes_returned = GciTsFetchBytes(self.c_session, instance.oop, start_index,
                                                        dest, num_bytes, &error);
                if bytes_returned == -1:
                    raise make_GemstoneError(self, error)

                dest[bytes_returned] = b'\0'
                py_bytes = py_bytes + dest
                start_index = start_index + num_bytes
            finally:
                free(dest)
        return py_bytes.decode('latin-1')

    def object_perform(self, GemObject instance, selector, *args):
        if not isinstance(selector, (str, GemObject)):
            raise GemstoneApiError('Selector is type {}.Expected selector to be a str or GemObject'.format(selector.__class__.__name__))
        cdef GciErrSType error
        cdef OopType selector_oop = selector.oop if isinstance(selector, GemObject) else OOP_ILLEGAL
        cdef char* selector_str = to_c_bytes(selector) if isinstance(selector, str) else NULL

        cdef OopType* cargs = <OopType *>malloc(len(args) * sizeof(OopType))
        for i in xrange(len(args)):
            cargs[i] = args[i].oop

        flags = 1
        environment_id = 0

        cdef OopType return_oop = GciTsPerform(self.c_session,
                                               instance.c_oop,
                                               selector_oop,
                                               selector_str,
                                               cargs, 
                                               len(args),
                                               flags,
                                               environment_id,
                                               &error)
        free(cargs)
        if return_oop == OOP_ILLEGAL:
            raise make_GemstoneError(self, error)
        return self.get_or_create_gem_object(return_oop)

#======================================================================================================================
