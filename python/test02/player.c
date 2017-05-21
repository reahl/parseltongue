//Test type
#include <Python.h>
#include <structmember.h>//provides declarations that we use to handle attributes

typedef struct {
    PyObject_HEAD
    PyObject *name;     //str
    PyObject *rank;     //long
    PyObject *tier;     //str
} Player;

static void
Player_dealloc(Player* self)//free data allocated in init
{
    Py_XDECREF(self->name);
    Py_XDECREF(self->rank);
    Py_XDECREF(self->tier);
    Py_TYPE(self)->tp_free((PyObject*)self);
}

static PyObject *
Player_new(PyTypeObject *type, PyObject *args, PyObject *kwds)//create a new instance of class
{
    Player *self;

    self = (Player *)type->tp_alloc(type, 0);
    if (self != NULL) {
        self->name = PyUnicode_FromString("");
        if (self->name == NULL) {
            Py_DECREF(self);
            return NULL;
        }

        self->rank = PyLong_FromLong((long)0);
        if (self->rank == NULL) {
            Py_DECREF(self);
            return NULL;
        }

        self->tier = PyUnicode_FromString("");
        if (self->tier == NULL) {
            Py_DECREF(self);
            return NULL;
        }
    }

    return (PyObject *)self;
}

static int
Player_init(Player *self, PyObject *args, PyObject *kwds)//initialization function
{
    PyObject *name=NULL, *rank=NULL, *tier=NULL, *tmp;

    static char *kwlist[] = {"name", "rank", "tier", NULL};

    if (! PyArg_ParseTupleAndKeywords(args, kwds, "|OOO", kwlist,
                                      &name, &rank, &tier))
        return -1;

    if (name) {
        if(PyUnicode_Check(name)){
            tmp = self->name;
            Py_INCREF(name);
            self->name = name;
            Py_XDECREF(tmp);
        }
        else{
            PyErr_SetString(PyExc_TypeError, "name must be unicode.");
            return -1;
        }
    }

    if (rank) {
        if(PyLong_Check(rank) && PyLong_AsLong(rank) >= 0){
            tmp = self->rank;
            Py_INCREF(rank);
            self->rank = rank;
            Py_XDECREF(tmp);
        }
        else{
            PyErr_SetString(PyExc_TypeError, "rank must be unsigned long.");
            return -1;
        }
    }

    if (tier) {
        if(PyUnicode_Check(tier)){
        tmp = self->tier;
        Py_INCREF(tier);
        self->tier = tier;
        Py_XDECREF(tmp);
        }
        else{
            PyErr_SetString(PyExc_TypeError, "tier must be unicode.");
            return -1;
        }
    }

    return 0;
}

static PyObject*
Player_str(Player *self, PyObject *args, PyObject *kwds){
    return PyUnicode_FromFormat("Name: %S, Rank: %S, Tier: %S", self->name, self->rank, self->tier);
}

static PyObject *
Player_increase_rank(Player* self, PyObject* arg)
{
    PyObject *new_rank=NULL, *tmp;
    long rank_inc = 1;
    tmp = self->rank;

    if(!PyArg_ParseTuple(arg, "|i", &rank_inc)){
        Py_RETURN_NONE;
    }

    new_rank = PyLong_FromLong(PyLong_AsLong(tmp) + rank_inc);

    if(new_rank){
        Py_INCREF(new_rank);
        self->rank = new_rank;
        Py_XDECREF(tmp);
    }

    Py_RETURN_NONE;
}

static PyObject *
Player_decrease_rank(Player* self, PyObject* arg)
{
    PyObject *new_rank=NULL, *tmp;
    long rank_dec = 1;
    tmp = self->rank;
    long rank = PyLong_AsLong(tmp);

    if(!PyArg_ParseTuple(arg, "|i", &rank_dec)){
        Py_RETURN_NONE;
    }

    rank -= (long)rank_dec;
    if (rank<0){
        printf("rank cannot be bellow 0. rank if decreased: %ld\n", rank);
        Py_RETURN_NONE;
    }

    new_rank = PyLong_FromLong(rank);

    if(new_rank){
        Py_INCREF(new_rank);
        self->rank = new_rank;
        Py_XDECREF(tmp);
    }

    Py_RETURN_NONE;
}

static PyObject *
Player_getname(Player *self, void *closure)
{
    return self->name;
}

static int
Player_setname(Player *self, PyObject *value, void *closure)
{
    if (value == NULL) {
        PyErr_SetString(PyExc_TypeError, "Cannot delete the name.");
        return -1;
    }

    if (! PyUnicode_Check(value)) {
        PyErr_SetString(PyExc_TypeError, "name must be unicode.");
        return -1;
    }

    Py_DECREF(self->name);
    Py_INCREF(value);
    self->name = value;

    return 0;
}

static PyObject *
Player_getrank(Player *self, void *closure)
{
    return self->rank;
}

static int
Player_setrank(Player *self, PyObject *value, void *closure)
{
    if (value == NULL) {
        PyErr_SetString(PyExc_TypeError, "Cannot delete the rank.");
        return -1;
    }

    if (! (PyLong_Check(value) && PyLong_AsLong(value) >= 0)) {
        PyErr_SetString(PyExc_TypeError, "rank must be unsigned long.");
        return -1;
    }

    Py_DECREF(self->rank);
    Py_INCREF(value);
    self->rank = value;

    return 0;
}

static PyObject *
Player_gettier(Player *self, void *closure)
{
    return self->tier;
}

static int
Player_settier(Player *self, PyObject *value, void *closure)
{
    if (value == NULL) {
        PyErr_SetString(PyExc_TypeError, "Cannot delete the tier.");
        return -1;
    }

    if (! PyUnicode_Check(value)) {
        PyErr_SetString(PyExc_TypeError, "tier must be unicode.");
        return -1;
    }

    Py_DECREF(self->tier);
    Py_INCREF(value);
    self->tier = value;

    return 0;
}

// static PyMemberDef Player_members[] = {
//     //{name     char *  name of the member,
//     //type      int     the type of the member in the C struct,
//     //offset    Py_ssize_t  the offset in bytes that the member is located on the type’s object struct,
//     //flags     int     flag bits indicating if the field should be read-only or writable,
//     //doc       char *  points to the contents of the docstring}
//     {"name", T_OBJECT_EX, offsetof(Player, name), 0,
//      "player name"},//(T_ macro)T_OBJECT_EX = PyObject *
//     {"rank", T_OBJECT_EX, offsetof(Player, rank), 0,
//      "player rank"},
//     {"tier", T_OBJECT_EX, offsetof(Player, tier), 0,
//      "player tier"},
//     {NULL}  /* Sentinel */
// };

static PyMethodDef Player_methods[] = {
    {"increase_rank", (PyCFunction)Player_increase_rank, METH_VARARGS,
     "Increase rank of player"},
    {"decrease_rank", (PyCFunction)Player_decrease_rank, METH_VARARGS,
     "Decrease rank of player"},
    {NULL}  /* Sentinel */
};

static PyGetSetDef Player_getseters[] = {
    {"name",
     (getter)Player_getname, (setter)Player_setname,
     "player name",
     NULL},
    {"rank",
     (getter)Player_getrank, (setter)Player_setrank,
     "player rank",
     NULL},
    {"tier",
     (getter)Player_gettier, (setter)Player_settier,
     "player tier",
     NULL},
    {NULL}  /* Sentinel */
};

static PyTypeObject PlayerType = { //install members
    PyVarObject_HEAD_INIT(NULL, 0)
    "player.Player",             /* tp_name */
    sizeof(Player),             /* tp_basicsize */
    0,                         /* tp_itemsize */
    (destructor)Player_dealloc, /* tp_dealloc */
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
    (reprfunc)Player_str,      /* tp_str */
    0,                         /* tp_getattro */
    0,                         /* tp_setattro */
    0,                         /* tp_as_buffer */
    Py_TPFLAGS_DEFAULT |
        Py_TPFLAGS_BASETYPE,   // tp_flags: class flag definition.
    "Player objects",           /* tp_doc */
    0,                         /* tp_traverse */
    0,                         /* tp_clear */
    0,                         /* tp_richcompare */
    0,                         /* tp_weaklistoffset */
    0,                         /* tp_iter */
    0,                         /* tp_iternext */
    Player_methods,            // tp_methods: method definitions
    0,            				// tp_members: member definitions
    Player_getseters,          /* tp_getset */
    0,                         /* tp_base */
    0,                         /* tp_dict */
    0,                         /* tp_descr_get */
    0,                         /* tp_descr_set */
    0,                         /* tp_dictoffset */
    (initproc)Player_init,      // tp_init: It is used to initialize an object after it’s created. Python __init__() method.
    0,                         // tp_alloc: Allocate memory .PyType_Ready() fills tp_alloc for us by inheriting it from our base class, which is object by default.
    Player_new,                 // tp_new: The new member is responsible for creating (as opposed to initializing) objects of the type. Python __new__() method.
};

static PyModuleDef playermodule = {
    PyModuleDef_HEAD_INIT,
    "player",
    "Example module that creates an extension type.",
    -1,
    NULL, NULL, NULL, NULL, NULL
};

PyMODINIT_FUNC
PyInit_player(void)
{
    PyObject* m;

    if (PyType_Ready(&PlayerType) < 0)
        return NULL;

    m = PyModule_Create(&playermodule);
    if (m == NULL)
        return NULL;

    Py_INCREF(&PlayerType);
    PyModule_AddObject(m, "Player", (PyObject *)&PlayerType);
    return m;
}
