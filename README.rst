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
    


License
-------

Parseltongue is licensed under the GNU Lesser General Public License v3.0 or later (LGPL-3.0-or-later).

This means you can:

- Use Parseltongue in commercial applications
- Modify Parseltongue privately
- Distribute Parseltongue as part of your applications

If you modify Parseltongue itself, you must distribute those modifications under the terms of the LGPL.

For the full license text, see the LICENSE file or visit: https://www.gnu.org/licenses/lgpl-3.0.html


