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

from weakref import WeakValueDictionary
import functools
import warnings
import pathlib
import os
import re
import packaging.version
from ctypes import CDLL

from ptongue.gemstone import *


#======================================================================================================================
well_known_class_names = { 
    OOP_CLASS_SMALL_INTEGER.value: 'small_integer',
    OOP_CLASS_LargeInteger.value: 'large_integer',
    OOP_CLASS_SMALL_DOUBLE.value: 'float',
    OOP_CLASS_Float.value: 'float',
    OOP_CLASS_STRING.value: 'string',
    OOP_CLASS_SYMBOL.value: 'string',
    OOP_CLASS_DoubleByteString.value: 'string',
    OOP_CLASS_DoubleByteSymbol.value: 'string',
    OOP_CLASS_QuadByteString.value: 'string',
    OOP_CLASS_QuadByteSymbol.value: 'string',
    OOP_CLASS_ByteArray.value: 'bytes',
    OOP_CLASS_CHARACTER.value: 'string',
    OOP_CLASS_Utf8.value: 'string',
    OOP_CLASS_Unicode7.value: 'string',
    OOP_CLASS_Unicode16.value: 'string',
    OOP_CLASS_Unicode32.value: 'string',
    OOP_CLASS_ORDERED_COLLECTION.value: 'ordered_collection',
    OOP_CLASS_N_DICTIONARY.value: 'dictionary',
    OOP_CLASS_IDENTITY_SET.value: 'identity_set'
 }

well_known_instances = {
    OOP_TRUE.value: True,
    OOP_FALSE.value: False,
    OOP_NIL.value: None
}

well_known_python_instances = {
    True: OOP_TRUE.value,
    False: OOP_FALSE.value,
    None: OOP_NIL.value
}

implemented_python_types = {
    'NoneType': 'boolean_or_none',
    'bool': 'boolean_or_none',
    'str': 'string',
    'int': 'integer',
    'float': 'float',
    'list': 'ordered_collection',
    'dict': 'dictionary',
    'set': 'identity_set'
}

#======================================================================================================================
def compute_small_integer_oop(py_int):
    if py_int <= MAX_SMALL_INT and py_int >= MIN_SMALL_INT:
        return (py_int << OOP_NUM_TAG_BITS) | OOP_TAG_SMALLINT
    else:
        raise OverflowError()

def to_c_bytes(py_string):
    return py_string.encode('utf-8') if py_string != None else None
    
#======================================================================================================================
class GemstoneLibrary:
    """A registry and factory for Gemstone library interfaces.
    
    This class provides functionality for registering, discovering, and loading
    Gemstone libraries based on their version compatibility. It serves as a registry
    and factory for library implementations, allowing the system to choose the
    appropriate implementation based on the available libraries.
    
    :cvar registered_libraries: List of registered library classes
    :cvar short_name: Short name identifier for the library
    :cvar min_version: Minimum supported version string
    :cvar max_version: Maximum supported version string
    """
    registered_libraries = []
    short_name = ''
    min_version = '1'
    max_version = '0'
    
    @classmethod
    def register(cls, library_class):
        """Register a library implementation class.
        
        This adds the given library class to the list of available implementations
        that can be selected based on version compatibility.
        
        :param library_class: The library class to register
        """
        cls.registered_libraries.append(library_class)
    
    @classmethod
    def find_library(cls, short_name):
        """Find and instantiate an appropriate library implementation.
        
        This method looks for compatible library files in the Gemstone installation
        directory and instantiates the most appropriate implementation class based
        on version compatibility.
        
        The method:
        1. Locates library files matching the given short name
        2. Extracts version information from the file name
        3. Finds registered library classes that support that version
        4. Instantiates the most recent compatible implementation
        
        :param short_name: Short name identifier for the library to find
        :return: An instance of the appropriate library implementation
        :raises Exception: If no compatible library file or implementation is found
        """
        lib_dir = pathlib.Path(os.environ['GEMSTONE']) / 'lib'
        lib_names = list(lib_dir.glob('*%s-*' % short_name))
        if not lib_names:
            raise Exception('Could not find a %s library in your $GEMSTONE (%s)' % (short_name, lib_dir) )
        if len(lib_names) > 1:
            raise Exception('Found many %s libraries in your $GEMSTONE (%s): %s' % (short_name, lib_dir, ','.join([i.name for i in lib_names])) )
        lib_path = lib_names[0]
        version, bits = re.match('lib%s-(.*)-(.*)..*' % short_name, lib_path.name).groups()
        matching_libraries = [i for i in cls.registered_libraries if i.short_name == short_name and packaging.version.parse(i.min_version) <= packaging.version.parse(version) <= packaging.version.parse(i.max_version)]
        if not matching_libraries:
            raise Exception('No support found for %s version %s' % (short_name, version))
        latest_matching_class = list(sorted(matching_libraries, key=lambda i: packaging.version.parse(i.min_version)))[-1]
        return latest_matching_class(lib_path)
        
    def __init__(self, lib_path):
        """Initialize a library instance.
        
        Loads the shared library from the specified path.
        
        :param lib_path: Path to the shared library file
        """
        self.library = CDLL(str(lib_path))

        
class GemstoneError(Exception):
    """Represents an exception that happened in a Gem.

    This class encapsulates errors that occurred within the Gemstone virtual machine,
    providing a Python-friendly interface to access information about the exception.

    This class is not a GemProxy like other Gem objects because it
    needs to be a Python Exception to work properly with Python's exception
    handling mechanisms.
    
    :ivar c_error: The C structure containing the error details.
    :ivar session: The Gemstone session where the error occurred.
    """
    def __init__(self, sess, c_error):
        """Initialize a new GemstoneError.
        
        :param sess: The Gemstone session where the error occurred.
        :param c_error: A C structure containing the error details.
        """
        self.c_error = c_error
        self.session = sess

    @property
    def category(self):
        obj = self.session.get_or_create_gem_object(self.c_error.category) if self.c_error.category else None
        return None if obj.isNil().to_py else obj

    @property
    def context(self):
        """Get the context where the exception occurred.
        
        The context is typically a GsProcess object representing the Smalltalk 
        execution state at the time of the error. This can be used for debugging
        and to manipulate the execution state.
        
        :return: A GemObject representing the GsProcess context, or None if 
                no context was provided.
        """
        obj = self.session.get_or_create_gem_object(self.c_error.context) if self.c_error.context else None
        return None if obj.isNil().to_py else obj

    @property
    def exception_obj(self):
        """Get the actual exception object from Gemstone.
        
        This is an instance of AbstractException or one of its subclasses that
        was signaled in the Gemstone environment. This may be nil if the error
        was not signaled from Smalltalk execution.
        
        :return: A GemObject representing the AbstractException, or None if no 
                exception object was provided.
        """
        obj = self.session.get_or_create_gem_object(self.c_error.exceptionObj) if self.c_error.exceptionObj else None
        return None if obj.isNil().to_py else obj

    @property
    def args(self):
        """Get the arguments of the exception.
        
        These are the arguments that were provided when the error was signaled,
        which provide additional context about the error condition.
        
        :return: A list of GemObjects representing the exception arguments, 
                or None if no arguments were provided.
        """
        return [self.session.get_or_create_gem_object(a) for a in self.c_error.args[:self.c_error.argCount]] if self.c_error.argCount else None

    @property
    def number(self):
        """Get the numeric error code for this exception.
        
        Gemstone assigns numeric codes to common errors. These can be used to
        identify specific error conditions programmatically.
        
        :return: An integer representing the Gemstone error number.
        """
        return self.c_error.number

    @property
    def arg_count(self):
        return self.c_error.argCount

    @property
    def is_fatal(self):
        """Check if this is a fatal error.
        
        Fatal errors typically cannot be recovered from and may indicate 
        serious problems with the Gemstone server that require administrative
        intervention.
        
        :return: True if the error is fatal, False otherwise.
        """
        return bool(self.c_error.fatal)

    @property
    def reason(self):
        """Get the reason for the exception.
        
        This field may contain additional context about why the exception occurred.
        
        :return: A UTF-8 decoded string containing the reason for the exception.
        """
        return self.c_error.reason.decode('utf-8')

    @property
    def message(self):
        """Get the error message.
        
        This contains the formatted error text, including any arguments that
        were provided.
        
        :return: A UTF-8 decoded string containing the error message.
        """
        return self.c_error.message.decode('utf-8')

    def __str__(self):
        """Get a string representation of the exception.
        
        This tries to use the Smalltalk exception's asString method,
        falling back to the C-level error message if that fails.
        
        :return: A string representation of the exception.
        """
        try:
            return self.exception_obj.asString().to_py
        except:
            return self.message

    def __repr__(self):
        """Get a detailed string representation of the exception.
        
        This tries to use the Smalltalk exception's printString method,
        falling back to the C-level error message if that fails.
        
        :return: A detailed string representation of the exception.
        """
        try:
            return self.exception_obj.printString().to_py
        except:
            return self.message

    def continue_with(self, continue_with_error=None, replace_top_of_stack=None):
        """Continue execution after the exception.
        
        This method allows for resuming execution at the point where the exception
        occurred, similar to how Smalltalk exceptions can be resumed.
        
        :param continue_with_error: Another GemstoneError to continue with. If provided,
                                   this error will be signaled instead, and replace_top_of_stack
                                   must be None.
        :param replace_top_of_stack: A GemObject to replace the top of the stack. This is
                                     used if continue_with_error is None.
        :return: The result of continuing execution as a GemObject.
        """
        replace_top_of_stack_oop = replace_top_of_stack.oop if replace_top_of_stack else OOP_ILLEGAL
        continue_with_error_oop = ctypes.byref(continue_with_error.c_error) if continue_with_error else None
        return self.session.object_continue_with(self.context, continue_with_error_oop, replace_top_of_stack_oop)

    def clear_stack(self):
        """Clear the stack of the process where the exception occurred.
        
        This terminates the execution context of the GsProcess where
        the error occurred, resetting it to a clean state.
        
        :return: The result of clearing the stack.
        """
        return self.session.object_clear_stack(self.context)        

    
class InvalidSession(Exception):
    """Indicates a problem with the current Session."""
    pass

class NotSupported(Exception):
    """Thrown when an attempt is made to do something that is not
       supported. For example, if you try to transfer a type of Python object
       to Gemstone which cannot be transferred.
    """
    pass

class GemstoneApiError(Exception):
    """Thrown when problems are detected while communicating via the underlying C API."""
    pass

class GemstoneWarning(Warning):
    """Represents a warning condition related to this API."""
    pass

#======================================================================================================================
class GemObject:
    """A Python object that represents a given object in a Gem.

    This class serves as a bridge between Python code and Gemstone objects. Each instance
    wraps a reference to an object in a Gemstone session and provides methods to interact
    with that object.

    A GemObject forwards method calls to its counterpart in the Gem. It returns other
    GemObject objects (and if the method takes arguments, those must also be GemObject
    objects)::
             
        today = date_class.today()
        assert isinstance(today, GemObject)
        assert today.is_kind_of(date_class)

    In Python, method names are spelled differently. Each ':' in a Smalltalk
    method symbol is replaced with a '_' in Python. When calling such a
    method, you must pass the correct number of arguments as Python
    positional arguments::

        user_globals.at_put(some_key, gem_number)

    :ivar oop: The object-oriented pointer value in the Gemstone VM.
    :ivar session: Reference to the session this object belongs to.
    """
    
    def __init__(self, session, oop):
        """Initialize a new GemObject.

        :param session: The Gemstone session this object belongs to.
        :param oop: The object-oriented pointer value in the Gemstone VM.
        """
        self.oop = oop
        self.session = session

    @property
    def is_nil(self):
        """Check if this object is Gemstone's nil.

        :return: True if this object is nil, False otherwise.
        """
        return self.oop == OOP_NIL.value

    @property
    def is_symbol(self):
        """Check if this object is a Gemstone Symbol.

        :return: True if this object is a Symbol, False otherwise.
        """
        return self.is_kind_of(self.session.get_or_create_gem_object(OOP_CLASS_SYMBOL.value))

    @property
    def to_py(self):
        """Convert this GemObject to an appropriate Python object.

        This method transfers the GemObject to a Python object of appropriate type.
        This is only supported for basic types, such as unicode strings, various
        numbers and booleans.

        :return: A Python representation of this Gemstone object.
        :raises NotSupported: If the object cannot be converted to a Python type.
        """
        return self.session.object_to_py(self)

    def is_kind_of(self, a_class):
        """Check if this object is an instance of the given class or one of its subclasses.

        :param a_class: A Gemstone class object to check against.
        :return: True if this object is an instance of the given class or a subclass,
                False otherwise.
        """
        return self.session.object_is_kind_of(self, a_class)
    
    def gemstone_class(self):
        """Get the Gemstone class of this object.

        :return: A GemObject representing the class of this object.
        """
        return self.session.object_gemstone_class(self)

    def __getattr__(self, name):
        """Handle attribute access for methods not defined in Python.

        This method intercepts attribute access and converts it to method calls
        on the Gemstone object. This allows for natural Python syntax when calling
        Gemstone methods.

        :param name: The name of the attribute being accessed.
        :return: A function that, when called, will invoke the corresponding
                method on the Gemstone object.
        """
        return functools.partial(self.perform_mapped_selector, name)

    def perform_mapped_selector(self, selector, *args):
        """Perform a method call using Python method name conventions.

        This method provides the implementation for calling Gemstone methods
        using Python naming conventions (underscores instead of colons).

        :param selector: The Python-style method name (with underscores).
        :param args: Arguments to pass to the method.
        :return: The result of the method call.
        :raises TypeError: If an incorrect number of arguments is provided.
        """
        smalltalk_selector = selector.replace('_', ':')
        if args or '_' in selector:
           smalltalk_selector += ':'
        expected_args = smalltalk_selector.count(':')
        if len(args) != expected_args:
            raise TypeError('%s() takes exactly %s arguments (%s given)' % (selector, expected_args, len(args)))
        selector_symbol = self.session.new_symbol(smalltalk_selector)
        return self.perform(selector_symbol, *[(i if isinstance(i, self.__class__) else self.session.from_py(i)) for i in args])

    def perform(self, selector, *args):
        """Directly perform a method on the Gemstone object.

        This is the low-level method that actually executes a method call on the
        Gemstone object. It accepts a Gemstone selector (Symbol) and arguments.

        :param selector: The method selector, either as a GemObject Symbol
                         or a string that will be converted to a Symbol.
        :param args: GemObject arguments to pass to the method.
        :return: The result of the method call.
        """
        return self.session.object_perform(self, selector, *args)

    def __iter__(self):
        """Provide iteration over collection objects.

        This allows Gemstone collections to be iterated over using Python's
        iteration protocol.

        :yield: Each element in the collection.
        """
        self_as_collection = self.asOrderedCollection()
        for i in range(1, self_as_collection.size().to_py+1):
            yield self_as_collection.at(i)
        
    def __repr__(self):
        """Provide a string representation for debugging.

        :return: A string representation showing the class name and OOP.
        """
        return '%s(%s)' % (self.__class__.__name__, self.oop)

    def __str__(self):
        """Provide a human-readable string representation.

        This method attempts to create a readable representation of the Gemstone
        object, similar to how it would be displayed in Gemstone itself.

        :return: A human-readable string representation of the object.
        """
        if self.perform('isBehavior').to_py:
            printed = self.perform('printString').to_py
        else:
            class_name = self.perform('class').perform('printString').to_py
            pre = 'an' if (class_name[0] in 'AEIOU') else 'a'
            description = '%s%s' % (pre, class_name)
            gem_printed = self.perform('printString')
            if gem_printed.perform('size').to_py <= max(len(class_name) * 2, 30):
                printed = gem_printed.to_py
                if not printed.startswith(description):
                    printed = '%s(%s)' % (description, printed)
            else:
                printed = description
        return printed

    def __del__(self):
        """Clean up resources when this object is garbage collected.

        This method ensures that when a Python GemObject is garbage collected,
        the corresponding Gemstone object is added to a list of objects that
        should be released on the Gemstone side.
        """
        if self.session.is_logged_in:
            if len(self.session.deallocated_unfreed_gemstone_objects) > self.session.export_set_free_batch_size:
                self.session.remove_dead_gemstone_objects()
            self.session.deallocated_unfreed_gemstone_objects.add(self.oop)
            
#======================================================================================================================
class GemstoneSession:
    """A Python interface for managing a connection to a Gemstone database.
    
    This class provides the foundation for interacting with Gemstone objects from Python.
    It manages conversion between Python and Gemstone objects, caches Gemstone objects 
    to maintain identity, and handles object lifecycle management.
    
    The session maintains a cache of GemObject instances to ensure that the same 
    Gemstone object is always represented by the same Python object during its lifetime.
    
    :ivar instances: A weak dictionary mapping OOPs to GemObject instances
    :ivar deallocated_unfreed_gemstone_objects: Set of OOPs pending release
    :ivar initial_fetch_size: Default size for fetching data chunks
    :ivar export_set_free_batch_size: Batch size for releasing objects
    """
    def __init__(self):
        """Initialize a new Gemstone session.
        
        Sets up the object cache and management structures.
        """
        self.instances = WeakValueDictionary()
        self.deallocated_unfreed_gemstone_objects = set()
        self.initial_fetch_size = 200
        self.export_set_free_batch_size = 1000
        
    def get_or_create_gem_object(self, oop):
        """Get an existing GemObject or create a new one for the given OOP.
        
        This method ensures that the same OOP is always represented by the
        same Python GemObject instance. If an object for the given OOP already
        exists in the cache, it is returned; otherwise, a new one is created.
        
        :param oop: Object-oriented pointer (OOP) value for a Gemstone object
        :return: A GemObject instance representing the object
        """
        try:
            return self.instances[oop]
        except KeyError:
            new_gem_object = GemObject(self, oop)
            self.instances[oop] = new_gem_object
            return new_gem_object
            
    def from_py(self, py_object):
        """Convert a Python object to its corresponding Gemstone representation.
        
        This method determines the appropriate conversion method based on the
        Python object's type and delegates to a specialized conversion method.
        
        :param py_object: A Python object to convert
        :return: A GemObject representing the converted object
        :raises NotSupported: If the Python type cannot be converted
        """
        try:
            method_name = implemented_python_types[py_object.__class__.__name__]
            return_oop = getattr(self, 'py_to_{}_'.format(method_name))(py_object)
        except KeyError:
            raise NotSupported('Cannot convert %s to a GemObject' % py_object.__class__.__name__)
        return self.get_or_create_gem_object(return_oop)
        
    def py_to_boolean_or_none_(self, py_object):
        """Convert Python None, True, or False to their Gemstone equivalents.
        
        :param py_object: Python None, True, or False
        :return: OOP value for the corresponding Gemstone object
        """
        return well_known_python_instances[py_object]
        
    def py_to_integer_(self, py_int):
        """Convert a Python integer to a Gemstone integer.
        
        For values that fit in a SmallInteger, creates a direct OOP.
        For larger integers, uses Gemstone LargeInteger.
        
        :param py_int: A Python integer
        :return: OOP value for the corresponding Gemstone integer
        """
        try:
            return_oop = compute_small_integer_oop(py_int)
        except OverflowError:    
            return_oop = self.execute('^{}'.format(py_int)).oop
        return return_oop
        
    def py_to_ordered_collection_(self, py_list):
        """Convert a Python list to a Gemstone OrderedCollection.
        
        :param py_list: A Python list
        :return: OOP value for a corresponding Gemstone OrderedCollection
        """
        collection = self.resolve_symbol('OrderedCollection').new()
        for i in py_list:
            collection.add(self.from_py(i))
        return collection.oop
        
    def py_to_dictionary_(self, py_dict):
        """Convert a Python dictionary to a Gemstone Dictionary.
        
        :param py_dict: A Python dictionary
        :return: OOP value for a corresponding Gemstone Dictionary
        """
        dictionary = self.resolve_symbol('Dictionary').new()
        for key, value in py_dict.items():
            dictionary.at_put(self.from_py(key), self.from_py(value))
        return dictionary.oop
        
    def py_to_identity_set_(self, py_set):
        """Convert a Python set to a Gemstone IdentitySet.
        
        :param py_set: A Python set
        :return: OOP value for a corresponding Gemstone IdentitySet
        """
        identity_set = self.resolve_symbol('IdentitySet').new()
        for i in py_set:
            identity_set.add(self.from_py(i))
        return identity_set.oop
    
    def object_to_py(self, instance):
        """Convert a Gemstone object to its corresponding Python representation.
        
        This method determines the appropriate conversion method based on the
        Gemstone object's class and delegates to a specialized conversion method.
        
        :param instance: A GemObject to convert to Python
        :return: The corresponding Python object
        :raises NotSupported: If the Gemstone class cannot be converted
        """
        try: 
            return well_known_instances[instance.oop]
        except KeyError:
            try:
                gem_class_name = well_known_class_names[instance.gemstone_class().oop]
            except KeyError:
                raise NotSupported('Cannot convert a gemstone %s to python' % instance.gemstone_class().name().to_py)
            return getattr(self, 'object_{}_to_py'.format(gem_class_name))(instance)
    
    def object_small_integer_to_py(self, instance):
        """Convert a Gemstone SmallInteger to a Python integer.
        
        :param instance: A GemObject representing a SmallInteger
        :return: The corresponding Python integer
        :raises GemstoneApiError: If the object is not a SmallInteger
        """
        if GCI_OOP_IS_SMALL_INT(instance.oop):
            return ctypes.c_int64(instance.oop).value >> ctypes.c_int64(OOP_NUM_TAG_BITS).value
        else:
            raise GemstoneApiError('Expected oop to represent a Small Integer.')
            
    def object_large_integer_to_py(self, instance):
        """Convert a Gemstone LargeInteger to a Python integer.
        
        :param instance: A GemObject representing a LargeInteger
        :return: The corresponding Python integer
        """
        string_result = self.object_latin1_to_py(self.object_perform(instance, 'asString'))
        return int(string_result)
        
    def object_ordered_collection_to_py(self, instance):
        """Convert a Gemstone OrderedCollection to a Python list.
        
        :param instance: A GemObject representing an OrderedCollection
        :return: The corresponding Python list
        """
        py_list = []
        for i in range(1, instance.size().to_py+1):
            py_list.append(instance.at(i).to_py)
        return py_list
        
    def object_dictionary_to_py(self, instance):
        """Convert a Gemstone Dictionary to a Python dictionary.
        
        :param instance: A GemObject representing a Dictionary
        :return: The corresponding Python dictionary
        """
        py_dict = {}
        keys = instance.keys().asArray()
        for i in range(1, keys.size().to_py+1):
            key = keys.at(self.from_py(i))
            value = instance.at(key)
            py_dict[key.to_py] = value.to_py
        return py_dict
    
    def object_identity_set_to_py(self, instance):
        """Convert a Gemstone IdentitySet to a Python set.
        
        :param instance: A GemObject representing an IdentitySet
        :return: The corresponding Python set
        """
        py_set = set()
        items = instance.asArray()
        for i in range(1, items.size().to_py+1):
            item = items.at(self.from_py(i))
            py_set.add(item.to_py)
        return py_set
        
    def __getattr__(self, name):
        """Allow direct access to Gemstone globals as attributes.
        
        This method allows Gemstone globals to be accessed as attributes
        of the session object, e.g., session.OrderedCollection instead of
        session.resolve_symbol('OrderedCollection').
        
        :param name: Name of the Gemstone global to access
        :return: A GemObject representing the global
        """
        return self.resolve_symbol(name)

#======================================================================================================================
