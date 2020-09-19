#define _GNU_SOURCE 1
#include <Python.h>
#include <sys/time.h>
#include <stdio.h>
#include <stdbool.h>
#include <XPLM/XPLMDefs.h>
#include <XPLM/XPLMScenery.h>
#include "utils.h"
#include "plugin_dl.h"
#include "xppythontypes.h"

static const char probeName[] = "XPLMProbeRef";

static PyObject *XPLMCreateProbeFun(PyObject *self, PyObject *args)
{
  (void) self;
  int inProbeType;
  if(!PyArg_ParseTuple(args, "i", &inProbeType)){
    return NULL;
  }
  return getPtrRefOneshot(XPLMCreateProbe(inProbeType), probeName);
}

static PyObject *XPLMDestroyProbeFun(PyObject *self, PyObject *args)
{
  (void) self;
  PyObject *inProbe = NULL;
  if(!PyArg_ParseTuple(args, "O", &inProbe)){
    return NULL;
  }
  XPLMDestroyProbe(refToPtr(inProbe, probeName));
  Py_RETURN_NONE;
}

static PyObject *XPLMProbeTerrainXYZFun(PyObject *self, PyObject *args)
{
  (void) self;
  PyObject *probe, *outInfo;
  float inX, inY, inZ;
  int returnValues = 0;

  if(!PyArg_ParseTuple(args, "OfffO", &probe, &inX, &inY, &inZ, &outInfo)){
    PyErr_Clear();
    returnValues = 1;
    if(!PyArg_ParseTuple(args, "Offf", &probe, &inX, &inY, &inZ)){
      return NULL;
    }
  }
  XPLMProbeRef inProbe = refToPtr(probe, probeName);
  XPLMProbeInfo_t info;
  info.structSize = sizeof(info);
  XPLMProbeResult res = XPLMProbeTerrainXYZ(inProbe, inX, inY, inZ, &info);

  PyObject *ret;
  ret = PyProbeInfo_New(res, info.locationX, info.locationY, info.locationZ,
                           info.normalX, info.normalY, info.normalZ,
                           info.velocityX, info.velocityY, info.velocityZ, info.is_wet);
  if (returnValues) 
    return ret;

  pythonLogWarning("XPLMProbeTerrainXYZ does not require final info parameter");

  if (outInfo != Py_None)
    PyList_Append(outInfo, ret);
  
  return PyLong_FromLong(res);
}

static PyObject *XPLMGetMagneticVariationFun(PyObject *self, PyObject *args)
{
  (void)self;
  if(!XPLMGetMagneticVariation_ptr){
    PyErr_SetString(PyExc_RuntimeError , "XPLMGetMagneticVariation is available only in XPLM300 and up.");
    return NULL;
  }
  double latitude, longitude;
  if(!PyArg_ParseTuple(args, "dd", &latitude, &longitude)){
    return NULL;
  }
  return PyFloat_FromDouble(XPLMGetMagneticVariation_ptr(latitude, longitude));
}

static PyObject *XPLMDegTrueToDegMagneticFun(PyObject *self, PyObject *args)
{
  (void)self;
  if(!XPLMDegTrueToDegMagnetic_ptr){
    PyErr_SetString(PyExc_RuntimeError , "XPLMDegTrueToDegMagnetic is available only in XPLM300 and up.");
    return NULL;
  }
  float headingDegreesTrue;
  if(!PyArg_ParseTuple(args, "f", &headingDegreesTrue)){
    return NULL;
  }
  return PyFloat_FromDouble(XPLMDegTrueToDegMagnetic_ptr(headingDegreesTrue));
}

static PyObject *XPLMDegMagneticToDegTrueFun(PyObject *self, PyObject *args)
{
  (void)self;
  if(!XPLMDegMagneticToDegTrue_ptr){
    PyErr_SetString(PyExc_RuntimeError , "XPLMDegMagneticToDegTrue is available only in XPLM300 and up.");
    return NULL;
  }
  float headingDegreesMagnetic;
  if(!PyArg_ParseTuple(args, "f", &headingDegreesMagnetic)){
    return NULL;
  }
  return PyFloat_FromDouble(XPLMDegMagneticToDegTrue_ptr(headingDegreesMagnetic));
}


static PyObject *XPLMLoadObjectFun(PyObject *self, PyObject *args)
{
  (void)self;
  const char *inPath;
  if(!PyArg_ParseTuple(args, "s", &inPath)){
    return NULL;
  }
  XPLMObjectRef res = XPLMLoadObject(inPath);
  return getPtrRefOneshot(res, objRefName);
}



static PyObject *loaderDict;
static intptr_t loaderCntr;

static void objectLoaded(XPLMObjectRef inObject, void *inRefcon)
{
  PyObject *object = getPtrRefOneshot(inObject, objRefName);
  PyObject *pID = PyLong_FromVoidPtr(inRefcon);
  PyObject *loaderCallbackInfo = PyDict_GetItem(loaderDict, pID);
  if(loaderCallbackInfo == NULL){
    printf("Unknown callback requested in objectLoaded(%p).\n", inRefcon);
    return;
  }
  PyObject *res = PyObject_CallFunctionObjArgs(PyTuple_GetItem(loaderCallbackInfo, 1),
                                           object, PyTuple_GetItem(loaderCallbackInfo, 2), NULL);
  PyObject *err = PyErr_Occurred();
  if(err){
    printf("Error occured during the objectLoaded callback(inRefcon = %p):\n", inRefcon);
    PyErr_Print();
  }else{
    Py_DECREF(res);
  }
  PyDict_DelItem(loaderDict, pID);
  Py_DECREF(pID);
  Py_DECREF(object);
}


static PyObject *XPLMLoadObjectAsyncFun(PyObject *self, PyObject *args)
{
  (void)self;
  if(!XPLMLoadObjectAsync_ptr){
    PyErr_SetString(PyExc_RuntimeError , "XPLMLoadObjectAsync is available only in XPLM210 and up.");
    return NULL;
  }
  const char *inPath;
  PyObject *callback, *inRefcon, *pluginSelf;

  if(!PyArg_ParseTuple(args, "OsOO", &pluginSelf, &inPath, &callback, &inRefcon)) {
    PyErr_Clear();
    if(!PyArg_ParseTuple(args, "sOO", &inPath, &callback, &inRefcon)) {
      return NULL;
    }
  } else {
    pythonLogWarning("'self' deprecated as first parameter of XPLMLoadObjectAsync");
  }

  PyObject *argsObj = Py_BuildValue("(sOO)", inPath, callback, inRefcon);

  void *refcon = (void *)++loaderCntr;
  PyObject *key = PyLong_FromVoidPtr(refcon);
  PyDict_SetItem(loaderDict, key, argsObj);
  Py_DECREF(key);
  XPLMLoadObjectAsync_ptr(inPath, objectLoaded, refcon); /* path, callback, refcon */
  Py_DECREF(argsObj);
  Py_RETURN_NONE;
}

#if defined(XPLM_DEPRECATED)
static PyObject *XPLMDrawObjectsFun(PyObject *self, PyObject *args)
{
  (void)self;
  PyObject *object;
  int inCount;
  PyObject *locations;
  int lighting;
  int earth_relative;
  if(!PyArg_ParseTuple(args, "OiOii", &object, &inCount, &locations, &lighting, &earth_relative)){
    return NULL;
  }
  XPLMObjectRef inObject = refToPtr(object, objRefName);
  XPLMDrawInfo_t *inLocations = (XPLMDrawInfo_t *)malloc(inCount * sizeof(XPLMDrawInfo_t));
  int i;
  PyObject *locationsTuple = PySequence_Tuple(locations);
  for(i = 0; i < inCount; ++i){
    PyObject *loc = PySequence_Tuple(PyTuple_GetItem(locationsTuple, i));
    inLocations[i].structSize = sizeof(XPLMDrawInfo_t);
    inLocations[i].x = getFloatFromTuple(loc, 0);
    inLocations[i].y = getFloatFromTuple(loc, 1);
    inLocations[i].z = getFloatFromTuple(loc, 2);
    inLocations[i].pitch = getFloatFromTuple(loc, 3);
    inLocations[i].heading = getFloatFromTuple(loc, 4);
    inLocations[i].roll = getFloatFromTuple(loc, 5);
    Py_DECREF(loc);
  }
  Py_DECREF(locationsTuple);

  XPLMDrawObjects(inObject, inCount, inLocations, lighting, earth_relative);
  free(inLocations);
  Py_RETURN_NONE;
}
#endif

static PyObject *XPLMUnloadObjectFun(PyObject *self, PyObject *args)
{
  (void)self;
  XPLMObjectRef inObject = refToPtr(PyTuple_GetItem(args, 0), objRefName);
  XPLMUnloadObject(inObject);
  Py_RETURN_NONE;
}

static PyObject *libEnumDict;
static intptr_t libEnumCntr;

static void libraryEnumerator(const char *inFilePath, void *inRef)
{
  PyObject *pID = PyLong_FromVoidPtr(inRef);
  PyObject *libEnumCallbackInfo = PyDict_GetItem(libEnumDict, pID);
  Py_XDECREF(pID);
  if(libEnumCallbackInfo == NULL){
    printf("Unknown callback requested from libraryEnumerator(%p).\n", inRef);
    return;
  }
  PyObject *res = PyObject_CallFunction(PySequence_GetItem(libEnumCallbackInfo, 4), "(sO)",
                                           inFilePath, PySequence_GetItem(libEnumCallbackInfo, 5));
  Py_XDECREF(res);
}

static PyObject *XPLMLookupObjectsFun(PyObject *self, PyObject *args)
{
  (void)self;
  const char *inPath;
  float inLatitude, inLongitude;
  PyObject *enumerator;
  PyObject *ref;
  PyObject *pluginSelf;
  if(!PyArg_ParseTuple(args, "OsffOO", &pluginSelf, &inPath, &inLatitude, &inLongitude, &enumerator, &ref)) {
    PyErr_Clear();
    if(!PyArg_ParseTuple(args, "sffOO", &inPath, &inLatitude, &inLongitude, &enumerator, &ref)) {
      return NULL;
    }
  } else {
    pythonLogWarning("'self' deprecated as first parameter of XPLMLookupObjects");
  }
  pluginSelf = get_pluginSelf();
  void *myRef = (void *)++libEnumCntr;
  PyObject *refObj = PyLong_FromVoidPtr(myRef);
  
  PyObject *argsObj = Py_BuildValue("(OsffOO)", pluginSelf, inPath, inLatitude, inLongitude, enumerator, ref);
  PyDict_SetItem(libEnumDict, refObj, argsObj);
  Py_DECREF(argsObj);
  Py_XDECREF(refObj);
  int res = XPLMLookupObjects(inPath, inLatitude, inLongitude, libraryEnumerator, myRef);
  return PyLong_FromLong(res);
}

static PyObject *cleanup(PyObject *self, PyObject *args)
{
  (void) self;
  (void) args;
  PyDict_Clear(loaderDict);
  Py_DECREF(loaderDict);
  PyDict_Clear(libEnumDict);
  Py_DECREF(libEnumDict);
  Py_RETURN_NONE;
}

static PyMethodDef XPLMSceneryMethods[] = {
  {"XPLMCreateProbe", XPLMCreateProbeFun, METH_VARARGS, ""},
  {"XPLMDestroyProbe", XPLMDestroyProbeFun, METH_VARARGS, ""},
  {"XPLMProbeTerrainXYZ", XPLMProbeTerrainXYZFun, METH_VARARGS, ""},
  {"XPLMDegMagneticToDegTrue", XPLMDegMagneticToDegTrueFun, METH_VARARGS, ""},
  {"XPLMGetMagneticVariation", XPLMGetMagneticVariationFun, METH_VARARGS, ""},
  {"XPLMDegTrueToDegMagnetic", XPLMDegTrueToDegMagneticFun, METH_VARARGS, ""},
  {"XPLMLoadObject", XPLMLoadObjectFun, METH_VARARGS, ""},
  {"XPLMLoadObjectAsync", XPLMLoadObjectAsyncFun, METH_VARARGS, ""},
#if defined(XPLM_DEPRECATED)
  {"XPLMDrawObjects", XPLMDrawObjectsFun, METH_VARARGS, ""},
#endif
  {"XPLMUnloadObject", XPLMUnloadObjectFun, METH_VARARGS, ""},
  {"XPLMLookupObjects", XPLMLookupObjectsFun, METH_VARARGS, ""},
  {"cleanup", cleanup, METH_VARARGS, ""},
  {NULL, NULL, 0, NULL}
};

static struct PyModuleDef XPLMSceneryModule = {
  PyModuleDef_HEAD_INIT,
  "XPLMScenery",
  NULL,
  -1,
  XPLMSceneryMethods,
  NULL,
  NULL,
  NULL,
  NULL
};

PyMODINIT_FUNC
PyInit_XPLMScenery(void)
{
  if(!(loaderDict = PyDict_New())){
    return NULL;
  }
  if(!(libEnumDict = PyDict_New())){
    return NULL;
  }

  PyObject *mod = PyModule_Create(&XPLMSceneryModule);
  if(mod){
    PyModule_AddIntConstant(mod, "xplm_ProbeY", xplm_ProbeY);

    PyModule_AddIntConstant(mod, "xplm_ProbeHitTerrain", xplm_ProbeHitTerrain);
    PyModule_AddIntConstant(mod, "xplm_ProbeError", xplm_ProbeError);
    PyModule_AddIntConstant(mod, "xplm_ProbeMissed", xplm_ProbeMissed );
  }

  return mod;
}




