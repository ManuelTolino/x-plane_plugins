#ifndef UTILS__H
#define UTILS__H

#include <Python.h>
#include <stdbool.h>

const char *objRefName; 
const char *commandRefName;

void dbg(const char *msg);
bool objToList(PyObject *item, PyObject *list);
float getFloatFromTuple(PyObject *seq, Py_ssize_t i);
long getLongFromTuple(PyObject *seq, Py_ssize_t i);


#endif
