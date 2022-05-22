Parseltongue
============

Parseltongue is a library that lets Python programs execute methods on
objects inside a GemStone Smalltalk server.


Sessions
--------

Log in by creating a session. You can choose between an RPCSession or
a LinkedSession::

    linked_session = LinkedSession('DataCurator', 'swordfish')
    
    assert linked_session.is_logged_in
    assert not linked_session.is_remote 
    assert linked_session.is_current_session
    
    linked_session.log_out()
                
Multiple RPCSessions can exist simultaneously, but only a single
instance of a LinkedSession is allowed per process.


Resolving objects
-----------------

Looking up a Smalltalk symbol from the usual symbol dictionaries
results in a GemObject object being returned which represents that
object in Python::

    date_class = session.resolve_symbol('Date')
    assert isinstance(date_class, GemObject)

    
Calling methods
---------------

A GemObject object forwards method calls to its counterpart in the
Gem. It returns other GemObject objects (and if the method takes
arguments, those must also be GemObject objects)::
                
    today = date_class.today()
    assert isinstance(today, GemObject)
    assert today.isKindOf(date_class)
    

Transferring basic objects
--------------------------

Some basic objects can be transferred between GemStone and
Python. These include unicode strings, various numbers and booleans::
          
   gem_number = session.from_py(1)
   long_ago = date_class.fromDays(gem_number)
   
   long_ago_string = long_ago.asString()
   python_string = long_ago_string.to_py

   assert python_string == '1901/01/02'


Automatic translation of arguments
----------------------------------

Some arguments to Gemstone method calls can be turned into
GemObject instances automatically::

          
   long_ago = date_class.fromDays(1)
   
   long_ago_string = long_ago.asString()
   python_string = long_ago_string.to_py

   assert python_string == '1901/01/02'
   
   
Method name mapping
-------------------

In Python, method names are spelt differently. Each ':' in a Smalltalk
method symbol is replaced with a '_' in Python. When calling such a
method, you must pass the correct number of arguments as Python
positional arguments::

    user_globals = session.resolve_symbol('UserGlobals')
    some_key = session.new_symbol('akey')
    gem_number = session.from_py(123)
    
    user_globals.at_put(some_key, gem_number)
    



which types of python things can be to_gemstoned on the fly (anything that can be passed to .from_py)
which types can be to_py

set <> IdentitySet
list <> OrderedCollection
dict <> Dictionary
bytes <> ByteArray
str   <> DoubleByteString / QuadByteString / Utf8 / Unicode7 / Unicode16 / Unicode32
str <> Symbol
str <> Character
int <> SmallInteger, LargeInteger
float <> SmallDouble, Float
bool <> Boolean


list, dict, set
 create an empty equivalent in GemStone, create a gemstone-site equivalent of each element and add it to the collection in gemstone

the reverse is true for to_py on IdentitySet, OrderedCollection, Dictionary
 

iterate through Collection
  returns GemObjects
