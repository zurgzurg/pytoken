#include "Python.h"

/***********************************************/
static PyObject *lexbuf_new(void);
static void lexbuf_dealloc(PyObject *self);
static PyObject *lexbuf_getattr(PyObject *self, char *name);
static int lexbuf_setattr(PyObject *self, char *name, PyObject *val);

staticforward PyTypeObject lexbuf_type;

typedef struct {
  PyObject_HEAD

  void   *next_char_ptr;
  char   *buf;
} lexbuf_t;

static PyTypeObject lexbuf_type = {
  PyObject_HEAD_INIT(NULL)
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

static void
lexbuf_dealloc(PyObject *self)
{
  return;
}

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

/***************************************************************/
static PyObject *code_new(void);
static int code_init(PyObject *, PyObject *, PyObject *);
static PyObject *code_get_token(PyObject *, PyObject *);
static Py_ssize_t code_len(PyObject *);

staticforward PyTypeObject code_type;

typedef struct {
  PyObject_HEAD

  char   *buf;
  int     size_of_buf;
  int     num_in_buf;
} code_t;

static PyTypeObject code_type = {
  PyObject_HEAD_INIT(NULL)
  0,                                    /* ob_size */
  "escape.code",                        /* tp_name */
  sizeof(code_t),                       /* basic size */
  0,                                    /* item size */
  0,                                    /* tp_dealloc */
  0,                                    /* tp_print */
  0,                                    /* tp_getattr */
  0,                                    /* tp_setattr */
  0,                                    /* tp_compare */
  0,                                    /* tp_repr */
  0,                                    /* tp_as_number */
  0,                                    /* tp_as_sequence */
  0,                                    /* tp_as_mapping */
  0,                                    /* tp_hash */
  0,                                    /* tp_call */
  0,                                    /* tp_str */
  0,                                    /* tp_getattro */
  0,                                    /* tp_setattro       */
  0,                                    /* tp_as_buffer      */
  Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE, /* tp_flags      */
  PyDoc_STR("container for all executable code"),   /* tp_doc */
  0,                                    /* tp_traverse       */
  0,                                    /* tp_clear          */
  0,                                    /* tp_richcompare    */
  0,                                    /* tp_weaklistoffset */
  0,                                    /* tp_iter           */
  0,                                    /* tp_iternext       */
  0,                                    /* tp_methods        */
  0,                                    /* tp_members        */
  0,                                    /* tp_getset         */
  0,                                    /* tp_base           */
  0,                                    /* tp_dict           */
  0,                                    /* tp_descr_get      */
  0,                                    /* tp_descr_set      */
  0,                                    /* tp_dictoffset     */
  code_init,                            /* tp_init           */
  0,                                    /* tp_alloc          */
  0,                                    /* tp_new            */
};

static PyMethodDef code_methods[] = {
    {"get_token", code_get_token, METH_NOARGS,
     "Return the next token."},
    {NULL}
};

static PySequenceMethods code_seq_methods = {
  0, /* sq_length */
  0, /* sq_concat */
  0, /* sq_repeat */
  0, /* sq_item */
  0, /* sq_slice */
  0, /* sq_ass_item */
  0, /* sq_ass_slice */
  0, /* sq_contains */
  0, /* sq_inplace_concat */
  0, /* sq_inplace_repeat */
};

static PyObject *
code_new(void)
{
  code_t *result;

  result = PyObject_NEW (code_t, &code_type);
  result->num_in_buf    = 0;
  result->size_of_buf   = 1024;
  result->buf           = calloc(1, result->size_of_buf);
  return (PyObject *)result;
}

static int
code_init(PyObject *arg_self, PyObject *args, PyObject *kwds)
{
  code_t *self;

  self = (code_t *)arg_self;
  self->num_in_buf = 0;
  return 0;
}

static Py_ssize_t
code_len(PyObject *arg_self)
{
  code_t *self;

  assert(arg_self->ob_type == &code_type);
  self = (code_t *)arg_self;
  return self->num_in_buf;
}

static PyObject *
code_get_token(PyObject *arg_self_type, PyObject *arg_args)
{
  Py_INCREF(Py_None);
  return Py_None;
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
escape_make_code_obj(PyObject *self, PyObject *args)
{
  PyObject *result;

  result = code_new();
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
  {"make_code_obj",    escape_make_code_obj,     METH_VARARGS,
   PyDoc_STR("Create a architecture independant code object .")},
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
  if (code < 0)
    return;

  /****************************/
  /* runtime code obj support */
  /****************************/
  code_type.tp_new = PyType_GenericNew;
  code_type.tp_methods = code_methods;

  code_seq_methods.sq_length = code_len;
  code_type.tp_as_sequence = &code_seq_methods;

  code = PyType_Ready(&code_type);
  if (code < 0)
    return;
  Py_INCREF(&code_type);
  code = PyModule_AddObject(m, "code", (PyObject *)&code_type);
  if (code < 0)
    return;

  return;
}
