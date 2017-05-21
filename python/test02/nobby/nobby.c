#include <Python.h>

typedef struct {
    PyObject_HEAD//macro brings in fields: Py_REFCNT and Py_TYPE.These macros are used to access ob_refcnt field and a pointer to a type object of PyObject.
    /* Type-specific fields go here. */
} noddy_NoddyObject;

static PyTypeObject noddy_NoddyType = {
    PyVarObject_HEAD_INIT(NULL, 0)
    "noddy.Noddy",             /* tp_name */
    sizeof(noddy_NoddyObject), /* tp_basicsize */
    0,                         /* tp_itemsize */
    0,                         /* tp_dealloc */
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
    Py_TPFLAGS_DEFAULT,        /* tp_flags */
    "Noddy objects",           /* tp_doc */
};

static PyModuleDef noddymodule = {
    PyModuleDef_HEAD_INIT,
    "noddy",
    "Example module that creates an extension type.",
    -1,
    NULL, NULL, NULL, NULL, NULL
};

PyMODINIT_FUNC
PyInit_noddy(void)
{
    PyObject* m;

    noddy_NoddyType.tp_new = PyType_GenericNew;//  PyObject* PyType_GenericNew(PyTypeObject *type, PyObject *args, PyObject *kwds)
    //Generic handler for the tp_new slot of a type object. Create a new instance using the type’s tp_alloc slot.
    //newfunc PyTypeObject.tp_new
    //An optional pointer to an instance creation function.

    if (PyType_Ready(&noddy_NoddyType) < 0)
        return NULL;
    //int PyType_Ready(PyTypeObject *type).  This function is responsible for adding inherited slots from a type’s base class.
    //This initializes the Noddy type, filing in a number of members, including ob_type.

    m = PyModule_Create(&noddymodule);
    //This adds the type to the module dictionary. This allows us to create Noddy instances by calling the Noddy class
    if (m == NULL)
        return NULL;

    Py_INCREF(&noddy_NoddyType);
    PyModule_AddObject(m, "Noddy", (PyObject *)&noddy_NoddyType);
    return m;
}