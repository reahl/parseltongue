#include <Python.h>
#include <structmember.h>//provides declarations that we use to handle attributes

typedef struct {
    PyObject_HEAD 	
    PyObject *first; /* first name */
    PyObject *last;  /* last name */
    int number;
} Noddy;

static void
Noddy_dealloc(Noddy* self)
{
    Py_XDECREF(self->first);//void Py_XDECREF(PyObject *o). Decrement the reference count for object o.
    Py_XDECREF(self->last);
    Py_TYPE(self)->tp_free((PyObject*)self);//??
    //Py_TYPE(o)
    //This macro is used to access the ob_type member of a Python object. It expands to: (((PyObject*)(o))->ob_type)
    //call tp_free member of the object’s type to free the object’s memory.
}

static PyObject *
Noddy_new(PyTypeObject *type, PyObject *args, PyObject *kwds)//initialize first and last names to empty strings
{
    Noddy *self;

    self = (Noddy *)type->tp_alloc(type, 0);//?? 
    if (self != NULL) {
        self->first = PyUnicode_FromString("");//PyObject *PyUnicode_FromString(const char *u) Create a Unicode object from a UTF-8 encoded null-terminated char buffer u.
        if (self->first == NULL) {
            Py_DECREF(self);//Decrement the reference count for object o.
            return NULL;
        }

        self->last = PyUnicode_FromString("");
        if (self->last == NULL) {
            Py_DECREF(self);
            return NULL;
        }

        self->number = 0;
    }

    return (PyObject *)self;
}

static int
Noddy_init(Noddy *self, PyObject *args, PyObject *kwds)//We provide an initialization function
{
    PyObject *first=NULL, *last=NULL, *tmp;

    static char *kwlist[] = {"first", "last", "number", NULL};

    if (! PyArg_ParseTupleAndKeywords(args, kwds, "|OOi", kwlist, //format: "|" Indicates that the remaining arguments in the Python argument list are optional,
    	//"O" Store a Python object in a C object pointer, "i" Convert a Python integer to a plain C int.
                                      &first, &last,
                                      &self->number))
        return -1;

    if (first) {
        tmp = self->first;
        Py_INCREF(first);
        self->first = first;
        Py_XDECREF(tmp);
    }

    if (last) {
        tmp = self->last;
        Py_INCREF(last);
        self->last = last;
        Py_XDECREF(tmp);
    }

    return 0;
}


static PyMemberDef Noddy_members[] = {
	//{name 	char * 	name of the member,
	//type 		int 	the type of the member in the C struct,
	//offset 	Py_ssize_t 	the offset in bytes that the member is located on the type’s object struct,
	//flags 	int 	flag bits indicating if the field should be read-only or writable,
	//doc 		char * 	points to the contents of the docstring}
    {"first", T_OBJECT_EX, offsetof(Noddy, first), 0,
     "first name"},//(T_ macro)T_OBJECT_EX = PyObject *
    {"last", T_OBJECT_EX, offsetof(Noddy, last), 0,
     "last name"},
    {"number", T_INT, offsetof(Noddy, number), 0,
     "noddy number"},//(T_ macro)T_INT = int
    {NULL}  /* Sentinel */
};

static PyObject *
Noddy_name(Noddy* self)//outputs the objects name as the concatenation of the first and last names.
{
    if (self->first == NULL) {
        PyErr_SetString(PyExc_AttributeError, "first");//Raised when an attribute reference or assignment fails.
        return NULL;
    }

    if (self->last == NULL) {
        PyErr_SetString(PyExc_AttributeError, "last");
        return NULL;
    }

    return PyUnicode_FromFormat("%S %S", self->first, self->last);
}

static PyMethodDef Noddy_methods[] = {
    {"name", (PyCFunction)Noddy_name, METH_NOARGS,
     "Return the name, combining the first and last name"
    },
    {NULL}  /* Sentinel */
};

static PyTypeObject NoddyType = { //install members
    PyVarObject_HEAD_INIT(NULL, 0)
    "noddy.Noddy",             /* tp_name */
    sizeof(Noddy),             /* tp_basicsize */
    0,                         /* tp_itemsize */
    (destructor)Noddy_dealloc, /* tp_dealloc */
    0,                         /* tp_print */
    0,                         /* tp_getattr */
    0,                         /* tp_setattr */
    0,                         /* tp_reserved */
    0,                         /* tp_repr */
    0,                         /* tp_as_number */
    0,                         /* tp_as_sequence */
    0,                         /* tp_as_mapping */
    0,                         /* tp_hash  */
    0,                         /* tp_call */
    0,                         /* tp_str */
    0,                         /* tp_getattro */
    0,                         /* tp_setattro */
    0,                         /* tp_as_buffer */
    Py_TPFLAGS_DEFAULT |
        Py_TPFLAGS_BASETYPE,   // tp_flags: class flag definition.
    "Noddy objects",           /* tp_doc */
    0,                         /* tp_traverse */
    0,                         /* tp_clear */
    0,                         /* tp_richcompare */
    0,                         /* tp_weaklistoffset */
    0,                         /* tp_iter */
    0,                         /* tp_iternext */
    Noddy_methods,             // tp_methods: method definitions
    Noddy_members,             // tp_members: member definitions
    0,                         /* tp_getset */
    0,                         /* tp_base */
    0,                         /* tp_dict */
    0,                         /* tp_descr_get */
    0,                         /* tp_descr_set */
    0,                         /* tp_dictoffset */
    (initproc)Noddy_init,      // tp_init: It is used to initialize an object after it’s created. Python __init__() method.
    0,                         // tp_alloc: Allocate memory .PyType_Ready() fills tp_alloc for us by inheriting it from our base class, which is object by default.
    Noddy_new,                 // tp_new: The new member is responsible for creating (as opposed to initializing) objects of the type. Python __new__() method.
};

static PyModuleDef noddy2module = {
    PyModuleDef_HEAD_INIT,
    "noddy2",
    "Example module that creates an extension type.",
    -1,
    NULL, NULL, NULL, NULL, NULL
};

PyMODINIT_FUNC
PyInit_noddy2(void)
{
    PyObject* m;

    if (PyType_Ready(&NoddyType) < 0)// allocate memory
        return NULL;

    m = PyModule_Create(&noddy2module);
    if (m == NULL)
        return NULL;

    Py_INCREF(&NoddyType);
    PyModule_AddObject(m, "Noddy", (PyObject *)&NoddyType);
    return m;
}
