/*Test some python extensions.
*
*/
#include <Python.h>
#include "test_data.h"

static PyObject *TestError;
Py_ssize_t list_size; 

char has_data;

static PyObject* test_set_data(PyObject* self, PyObject* arg)
{
	if (has_data == 1){
		has_data = 0;
		test_data(0, 0, 3);
	}

	PyObject* input;
	if(!PyArg_ParseTuple(arg, "O", &input)){ //int PyArg_ParseTuple(PyObject *args, const char *format, ...) Parse the parameters of a function that takes only positional parameters into local variables
		PyErr_SetString(TestError, "Error! Cannot parse data.");
		Py_RETURN_NONE;
	}
	printf("not broken\n");

	list_size = PyList_Size(input);
	double input_data[list_size];
    PyObject* tempItem;

    for(int i = 0; i < list_size; i++) {
        tempItem = PyList_GET_ITEM(input, i);

        if(PyLong_Check(tempItem)){
           input_data[i] = (double)PyLong_AsSsize_t(tempItem);
        }
        else if(PyFloat_Check(tempItem)){
           input_data[i] = PyFloat_AS_DOUBLE(tempItem);
        }
        else{
        	PyErr_SetString(TestError, "Error! Input is not a float or int.");
            //void PyErr_SetString(PyObject *type, const char *message)
        	Py_RETURN_NONE;
        }
    }

    has_data = 1;
    if(!test_data(input_data, list_size, 1)){
    	PyErr_SetString(TestError, "Error! Data could not be set.");
    }

	Py_RETURN_NONE;
}

static PyObject* test_get_max(PyObject* self){
	double max_val;
	if(has_data == 0){
		PyErr_SetString(TestError, "Error! No data.");
		Py_RETURN_NONE;
	}
	else{
		max_val = max_value(test_data(0, list_size, 2), list_size);
		return PyFloat_FromDouble(max_val);
	}
}


//Module’s Method Table
static PyMethodDef TestMethods[] =
{
	//{ml_name 	char * 			name of the method, 
	//ml_meth 	PyCFunction 	pointer to the C implementation, 
	//ml_flags 	int				flag bits indicating how the call should be constructed,
	//ml_doc 	char * 			points to the contents of the docstring},
	{"set_data", (PyCFunction)test_set_data, METH_VARARGS, "set input data."},
	{"get_max", (PyCFunction)test_get_max, METH_NOARGS, "get max data."},
	{NULL, NULL, 0, NULL}
};


static struct PyModuleDef moduledef = {
    PyModuleDef_HEAD_INIT,	//m_base
    "test",     		// m_name
    "test library",  	// m_doc 
    -1,                 // m_size 
    TestMethods,    	// m_methods
    NULL,               // m_reload 
    NULL,               // m_traverse 
    NULL,               // m_clear 
    NULL,               // m_free 
};


PyMODINIT_FUNC


PyInit_test(void)
{
    PyObject *module = PyModule_Create(&moduledef);

    if(module!=NULL){
	    TestError = PyErr_NewException("test.error", NULL, NULL);
        // PyObject* PyErr_NewException(const char *name, PyObject *base, PyObject *dict) creates and returns a new exception class
	    Py_INCREF(TestError);            
        //void Py_INCREF(PyObject *o) Increment the reference count for object o
	    PyModule_AddObject(module, "error", TestError);
        //int PyModule_AddObject(PyObject *module, const char *name, PyObject *value) Add an object to module as name
	}

    return module;
}