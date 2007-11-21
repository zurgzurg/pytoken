#include "Python.h"

/***********************************************/

typedef struct {
  PyObject_HEAD

  void   *next_char_ptr;
  char   *buf;
} lexbuf_t;

/***********************************************/

static void
lexbuf_dealloc(PyObject *self)
{
  return;
}

#if 0
static int
lexbuf_print(PyObject *self, FILE *fp, int flags)
{
  return 1;
}

static PyObject *
lexbuf_repr(PyObject *self)
{
  PyObject *r;

  r = PyString_FromString("#<lexbuf_obj>");
  return r;
}

static PyObject *
lexbuf_str(PyObject *self)
{
  PyObject *r;

  r = PyString_FromString("#<lexbuf_obj>");
  return r;
}
#endif


static PyObject *
lexbuf_getattr(PyObject *self, char *name)
{
  Py_INCREF(Py_None);
  return Py_None;
}

static int
lexbuf_setattr(PyObject *self, char *name, PyObject *val)
{
  return 1;
}

static PyTypeObject lexbuf_type = {
  PyObject_HEAD_INIT(&PyType_Type)
  0,                        /*ob_size*/
  "lexbuf",                 /*tp_name*/
  sizeof(lexbuf_t),         /*tp_basicsize*/
  0,                        /*tp_itemsize*/
                     /* methods */
  lexbuf_dealloc,           /*tp_dealloc*/
  0,                        /*tp_print*/
  lexbuf_getattr,           /*tp_getattr*/
  lexbuf_setattr,           /*tp_setattr*/
  0,                        /*tp_compare*/
  0,                        /*tp_repr*/
  0,                        /*tp_as_number*/
  0,                        /*tp_as_sequence*/
  0,                        /*tp_as_mapping*/
  0,                        /*tp_hash*/
  0,                        /*tp_call*/
  0,                        /*tp_str*/
};

static PyObject *
lexbuf_new(void)
{
  lexbuf_t *result;

  result = PyObject_NEW (lexbuf_t, &lexbuf_type);
  result->next_char_ptr = 0;
  result->buf           = 0;
  return (PyObject *)result;
}

/***************************************************************/

static PyObject *
escape_make_buffer(PyObject *self, PyObject *args)
{
  PyObject *result;

  result = lexbuf_new();
  return result;
}

static PyObject *
escape_get_func_addr(PyObject *self, PyObject *args)
{
  char *func_name;
  void *func_ptr;
  PyObject *result;

  if (!PyArg_ParseTuple(args, "s:get_func_addr", &func_name))
    return NULL;
  if (strcmp(func_name, "PyObject_CallMethod")==0)
    func_ptr = &PyObject_CallMethod;
  else {
    PyErr_SetString(PyExc_RuntimeError, "Unknown function name");
    return 0;
  }

  result = PyInt_FromLong((long)func_ptr);
  return result;
}


static PyMethodDef escape_methods[] = {
  {"make_buffer",      escape_make_buffer,       METH_VARARGS,
   PyDoc_STR("Create a new buffer to use with lexer obj.")},
  {"get_func_addr",    escape_get_func_addr,     METH_VARARGS,
   PyDoc_STR("Return address of certain python C api functions.")},
  {NULL,     NULL}
};

PyDoc_STRVAR(module_doc,
             "Module to give py lexer objects a way to get a the "
"underlying python implementation, as well as a way to call the"
"generated machine code.");

PyMODINIT_FUNC
initescape(void)
{
  PyObject *m;
  int code;

  m = Py_InitModule3("escape", escape_methods, module_doc);
  if (m == NULL)
    return;

  code = PyType_Ready(&lexbuf_type);

  return;
}
