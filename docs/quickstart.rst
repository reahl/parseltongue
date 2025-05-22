Quick Start Guide
=================

This guide will help you get started with Parseltongue, a Python interface to GemStone/S 64.

For more examples see :doc:`examples`, for API documentation, see :doc:`api/ptongue`.


Connecting to GemStone
----------------------

Log in by creating a session. You can choose between an RPCSession or
a LinkedSession.

Multiple RPCSessions can exist simultaneously, but only a single
instance of a LinkedSession is allowed per process::

    from ptongue.gemproxylinked import LinkedSession
    from ptongue.gemproxyrpc import RPCSession

    # For a linked session (runs in the same process)
    session = LinkedSession(
        username="DataCurator",
        password="swordfish"
    )

    # Or for an RPC session (connects to a remote gem)
    # session = RPCSession(
    #     username="DataCurator",
    #     password="swordfish"
    # )

    try:
        assert session.is_logged_in
    
        # Execute Smalltalk code
        result = session.execute("System gemVersionAt: #gsVersion")
        print(f"GemStone version: {result.to_py}")
    finally:
        session.log_out()


Resolving objects
-----------------

Looking up a Smalltalk symbol from the usual symbol dictionaries
results in a GemObject object being returned which represents that
object in Python::

    date_class = session.Date # Shorthand for session.resolve_symbol('Date')
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

A few collection types can also be transferred. Transferring
a collection also transfers its contents::

   gem_number = session.from_py(1)
   gem_collection = session.OrderedCollection.new()
   gem_collection.add(gem_number)

   py_list = gem_collection.to_py
   assert py_list[0] == 1

See :meth:`~ptongue.GemObject.to_py` and :meth:`~ptongue.GemstoneSession.from_py`.

Automatic translation of arguments
----------------------------------

Some arguments to Gemstone method calls can be turned into
GemObject instances without first having to :meth:`~ptongue.GemstoneSession.from_py`. them::

          
    long_ago = date_class.fromDays(1)
   
    long_ago_string = long_ago.asString()
    python_string = long_ago_string.to_py

    assert python_string == '1901/01/02'

    
Iterating over Gemstone collections
-----------------------------------

When a Gemstone object understands asOrdereredCollection, Python can iterate over
its elements without converting the collection or its elements to Python::

   gem_collection = session.OrderedCollection.new()
   gem_collection.add(1)

   assert [i.to_py for i in gem_collection] == [1]

This is useful when you want to iterate over a Gemstone collection and execute
methods without transferring it or its elements to Python.

   
Method name mapping
-------------------

In Python, method names are spelt differently. Each ':' in a Smalltalk
method symbol is replaced with a '_' in Python. When calling such a
method, you must pass the correct number of arguments as Python
positional arguments::

    user_globals = session.UserGlobals
    some_key = session.new_symbol('akey')
    
    user_globals.at_put(some_key, 123)  # Note 123 becomes from_py(123) as explained



A complete example
------------------

.. code-block:: python

    from ptongue import LinkedSession, GemObject

    session = LinkedSession(username="DataCurator", password="swordfish")

    try:
        assert session.is_logged_in

        date_class = session.Date # Shorthand for session.resolve_symbol('Date')
        assert isinstance(date_class, GemObject)

        today = date_class.today()
        assert isinstance(today, GemObject)
        assert today.isKindOf(date_class)

        long_ago = date_class.newDay_month_year(2,'Jan',1901)

        long_ago_string = long_ago.asString()
        python_string = long_ago_string.to_py

        assert python_string == '02/01/1901'

        user_globals = session.UserGlobals
        some_key = session.new_symbol('akey')

        user_globals.at_put(some_key, 123)  # Note 123 becomes from_py(123) as explained
        assert str(user_globals.at('akey')) == 'aSmallInteger(123)'
        assert user_globals.at('akey').to_py == 123
    finally:
        session.log_out()

Error Handling
--------------

.. code-block:: python

    from ptongue import LinkedSession, GemstoneError

    session = LinkedSession(username="DataCurator", password="swordfish")

    try:
        session.begin()
        
        try:
            # This will cause an error
            result = session.execute("1 zork: 2")
        except GemstoneError as e:
            print(f"Error: {e}")
            print(f"Error number: {e.number}")
            # You can continue execution after an error
            result = e.continue_with()
            
        print("Continuing")
        session.commit()
    finally:
        session.log_out()



        
License
-------

Parseltongue is licensed under the GNU Lesser General Public License v3.0 or later (LGPL-3.0-or-later).

This means you can:

- Use Parseltongue in commercial applications
- Modify Parseltongue privately
- Distribute Parseltongue as part of your applications

If you modify Parseltongue itself, you must distribute those modifications under the terms of the LGPL.

For the full license text, see the LICENSE file or visit: https://www.gnu.org/licenses/lgpl-3.0.html







