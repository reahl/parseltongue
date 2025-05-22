Examples
========

Here are some examples demonstrating how to use Parseltongue to interact with GemStone/S 64.

Basic Session Management
------------------------

.. code-block:: python

    from ptongue.gemproxylinked import LinkedSession

    # Create a linked session
    session = LinkedSession(
        username="DataCurator",
        password="swordfish",
        stone_name="gs64stone"
    )

    try:
        # Start a transaction
        session.begin()
        
        # Do some work...
        
        # Commit the transaction
        session.commit()
    except Exception as e:
        # In case of error, abort the transaction
        session.abort()
        raise
    finally:
        # Always log out
        session.log_out()

Working with Collections
------------------------

.. code-block:: python

    from ptongue.gemproxylinked import LinkedSession

    session = LinkedSession(username="DataCurator", password="swordfish")

    try:
        session.begin()
        
        # Create different types of collections
        array = session.execute("Array new: 3")
        dictionary = session.resolve_symbol('Dictionary').new()
        set = session.resolve_symbol('IdentitySet').new()
        
        # Working with arrays
        array.at_put(1, "First")
        array.at_put(2, "Second")
        array.at_put(3, "Third")
        
        # Working with dictionaries
        dictionary.at_put(session.new_symbol('key1'), "Value 1")
        dictionary.at_put(session.new_symbol('key2'), "Value 2")
        
        # Working with sets
        set.add("Item 1")
        set.add("Item 2")
        set.add("Item 1")  # Won't add duplicate
        
        # Convert to Python
        py_array = array.to_py
        py_dict = dictionary.to_py
        py_set = set.to_py
        
        print(f"Array: {py_array}")
        print(f"Dictionary: {py_dict}")
        print(f"Set: {py_set}")
        
        session.commit()
    finally:
        session.log_out()

Converting Between Python and GemStone
--------------------------------------

.. code-block:: python

    from ptongue.gemproxylinked import LinkedSession

    session = LinkedSession(username="DataCurator", password="swordfish")

    try:
        session.begin()
        
        # Python to GemStone
        py_int = 42
        py_float = 3.14159
        py_string = "Hello, GemStone!"
        py_list = [1, 2, 3, 4]
        py_dict = {"a": 1, "b": 2}
        py_set = {1, 2, 3}
        
        gs_int = session.from_py(py_int)
        gs_float = session.from_py(py_float)
        gs_string = session.from_py(py_string)
        gs_list = session.from_py(py_list)
        gs_dict = session.from_py(py_dict)
        gs_set = session.from_py(py_set)
        
        # GemStone to Python
        assert gs_int.to_py == py_int
        assert gs_float.to_py == py_float
        assert gs_string.to_py == py_string
        assert gs_list.to_py == py_list
        assert gs_dict.to_py == py_dict
        assert gs_set.to_py == py_set
        
        # Working with dates
        today = session.resolve_symbol('Date').today()
        py_date_string = today.asString().to_py
        print(f"Today is: {py_date_string}")
        
        session.commit()
    finally:
        session.log_out()

Database Operations
-------------------

.. code-block:: python

    from ptongue.gemproxylinked import LinkedSession

    session = LinkedSession(username="DataCurator", password="swordfish")

    try:
        session.begin()
        
        # Store data in UserGlobals
        user_globals = session.resolve_symbol('UserGlobals')
        
        # Create a persistent object
        person_class = session.execute('''
        Object subclass: 'Person'
            instVarNames: #('name' 'age')
            classVars: #()
            classInstVars: #()
            poolDictionaries: #()
            inDictionary: UserGlobals
            constraints: #()
        ''')
        
        # Add methods to the class
        session.execute('''
        Person compile: 'name: aString
            name := aString' 
            classified: 'accessing'
        ''')
        
        session.execute('''
        Person compile: 'age: anInteger
            age := anInteger' 
            classified: 'accessing'
        ''')
        
        session.execute('''
        Person compile: 'printString
            ^ name, '' (age: '', age printString, '')'''' 
            classified: 'printing'
        ''')
        
        # Create an instance
        person = person_class.new()
        person.name_("John Doe")
        person.age_(30)
        
        # Store in UserGlobals
        user_globals.at_put(session.new_symbol('myPerson'), person)
        
        # Retrieve and use the object
        retrieved_person = user_globals.at(session.new_symbol('myPerson'))
        print(f"Person: {retrieved_person.printString().to_py}")
        
        session.commit()
    finally:
        session.log_out()

These examples demonstrate the basic functionality of Parseltongue. For more advanced usage, refer to the API documentation.
