/*python errors
*
*/

extern string getPythonErrorString() {
	if (!PyErr_Occurred()) {
	return "No Python error";
	}

	PyObject *type, *value, *traceback;
	PyErr_Fetch(&type, &value, &traceback);
	PyErr_Clear();

	string message = "Python error: ";
	if (type) {
		type = PyObject_Str(type);
		message += PyString_AsString(type);
	}
	if (value) {
		value = PyObject_Str(value);
		message += ": ";
		message += PyString_AsString(value);
	}
	Py_XDECREF(type);
	Py_XDECREF(value);
	Py_XDECREF(traceback);

	return message;
}

extern void checkForPythonError(void) {
	if (PyErr_Occurred()) {
		throw PythonError(getPythonErrorString());
	}
}

extern void requirePythonError(void) {
	if (!PyErr_Occurred()) {
		throw PythonError("Boost.Python exception, but no Python error set.");
	}
}