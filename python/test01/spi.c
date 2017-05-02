/*Doing stuff
*
*/
#include <Python.h>

static double max_val;
Py_ssize_t list_size; 
extern double max_value(double[], int);


static PyObject* set_data(PyObject* self, PyObject* arg)
{
	PyObject* input;
	if(!PyArg_ParseTuple(arg, "O", &input))
		return NULL;

	list_size = PyList_Size(input);
	double indata[list_size];
    PyObject* tempItem;

    for(int i = 0; i < list_size; i++) {
        tempItem = PyList_GET_ITEM(input, i);

        if(PyLong_Check(tempItem)){
           indata[i] = (double)PyLong_AsSsize_t(tempItem);
        }
        else if(PyFloat_Check(tempItem)){
           indata[i] = PyFloat_AS_DOUBLE(tempItem);
        }
        else{
        	printf("error input is not a float or int. \n");
        	Py_RETURN_NONE;
        }
    }
    max_val = max_value(indata, (int)(list_size));
	Py_RETURN_NONE;
}

static PyObject* get_max(PyObject* self){
	return PyFloat_FromDouble(max_val);
}


static PyMethodDef SpiMethods[] =
{
	{"set_data", (PyCFunction)set_data, METH_VARARGS, "set input data."},
	{"get_max", (PyCFunction)get_max, METH_NOARGS, "get max data."},
	{NULL, NULL, 0, NULL}
};


static struct PyModuleDef moduledef = {
    PyModuleDef_HEAD_INIT,
    "spi",     			/* m_name */
    "spi library",  	/* m_doc */
    -1,                 /* m_size */
    SpiMethods,    		/* m_methods */
    NULL,               /* m_reload */
    NULL,               /* m_traverse */
    NULL,               /* m_clear */
    NULL,               /* m_free */
};


PyMODINIT_FUNC


PyInit_spi(void)
{
    PyObject *module = PyModule_Create(&moduledef);
    return module;
}