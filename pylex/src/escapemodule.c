#include "Python.h"

#include <sys/types.h>
#include <unistd.h>

/***********************************************/
static int lexer_state_init(PyObject *, PyObject *, PyObject *);
static void lexer_state_dealloc(PyObject *);

static PyObject *lexer_state_set_input_pos(PyObject *, PyObject *);
static PyObject *lexer_state_get_input_pos(PyObject *, PyObject *);
static PyObject *lexer_state_set_input(PyObject *, PyObject *);

typedef struct {
  PyObject_HEAD

  char   *next_char_ptr;
  char   *buf;
  int     size_of_buf;
} lexer_state_t;

static PyTypeObject lexer_state_type = {
  PyObject_HEAD_INIT(NULL)
};

static PyMethodDef lexer_state_methods[] = {
    {"set_input_pos", lexer_state_set_input_pos, METH_VARARGS,
     "Set index of next valid character to scan."},

    {"get_input_pos", lexer_state_get_input_pos, METH_NOARGS,
     "Return index of next char to scan."},

    {"set_input", lexer_state_set_input,         METH_VARARGS,
     "Set source of chars to read."},

    {NULL}
};

static int
lexer_state_init(PyObject *arg_self, PyObject *args, PyObject *kwds)
{
  lexer_state_t *self;

  assert(arg_self->ob_type == &lexer_state_type);
  self = (lexer_state_t *)arg_self;
  self->next_char_ptr = 0;
  self->buf           = 0;
  self->size_of_buf   = 0;
  return 0;
}

static void
lexer_state_dealloc(PyObject *arg_self)
{
  lexer_state_t *self;

  assert(arg_self->ob_type == &lexer_state_type);
  self = (lexer_state_t *)arg_self;
  if (self->buf)
    free(self->buf);
  self->next_char_ptr = 0;
  self->buf           = 0;
  self->size_of_buf   = 0;
  arg_self->ob_type->tp_free(arg_self);
}

static PyObject *
lexer_state_set_input_pos(PyObject *arg_self, PyObject *args)
{
  lexer_state_t *self;
  int pos;

  assert(arg_self->ob_type == &lexer_state_type);
  self = (lexer_state_t *)arg_self;
  if (!PyArg_ParseTuple(args, "i:set_input_pos", &pos))
    return 0;
  if (pos < 0 || pos > self->size_of_buf) {
    PyErr_Format(PyExc_RuntimeError, "position out of range");
    return 0;
  }
  if (self->buf==0 || self->size_of_buf==0) {
    PyErr_Format(PyExc_RuntimeError, "no input has been set");
    return 0;
  }
  self->next_char_ptr = self->buf + pos;

  Py_INCREF(Py_None);
  return Py_None;
}

static PyObject *
lexer_state_get_input_pos(PyObject *arg_self, PyObject *args)
{
  lexer_state_t *self;
  PyObject *result;

  assert(arg_self->ob_type == &lexer_state_type);
  self = (lexer_state_t *)arg_self;
  if (self->buf==0 || self->size_of_buf==0) {
    PyErr_Format(PyExc_RuntimeError, "no input has been set");
    return 0;
  }

  assert(self->next_char_ptr >= self->buf);
  assert(self->next_char_ptr < self->buf + self->size_of_buf);
  result = PyInt_FromLong(self->next_char_ptr - self->buf);
  return result;
}

static PyObject *
lexer_state_set_input(PyObject *arg_self, PyObject *args)
{
  lexer_state_t *self;
  char *tmp_buf;
  int i, tmp_buf_len;

  assert(arg_self->ob_type == &lexer_state_type);
  self = (lexer_state_t *)arg_self;
  if (!PyArg_ParseTuple(args, "s#:set_input", &tmp_buf, &tmp_buf_len))
    return 0;
  if (self->buf)
    free(self->buf);
  self->buf = malloc(tmp_buf_len);
  self->size_of_buf = tmp_buf_len;
  for (i=0; i<tmp_buf_len; i++)
    self->buf[i] = tmp_buf[i];
  self->next_char_ptr = self->buf;

  Py_INCREF(Py_None);
  return Py_None;
}

/***************************************************************/
static int code_init(PyObject *, PyObject *, PyObject *);
static void code_dealloc(PyObject *);

static Py_ssize_t code_len(PyObject *);
static PyObject *code_item(PyObject *, Py_ssize_t);

static PyObject *code_get_token(PyObject *, PyObject *);
static PyObject *code_set_type(PyObject *, PyObject *);
static PyObject *code_append(PyObject *, PyObject *);

typedef struct {
  PyObject_HEAD

  union {
    char      *buf;
    PyObject **obuf;
  } u;
  int     size_of_buf; /* in objects */
  int     num_in_buf;  /* num objs   */
  int     obj_size;  /* machine code : obj_size=1 : bytes */
                     /* vcode : obj_size=4 : PyObjects - likely tuples */
  int     is_vcode;
} code_t;

static void code_grow(code_t *);

static PyTypeObject code_type = {
  PyObject_HEAD_INIT(NULL)
};

static PyMethodDef code_methods[] = {
    {"get_token", code_get_token, METH_VARARGS,
     "Return the next token."},

    {"set_type",  code_set_type,  METH_VARARGS,
     "Set type of code object to 'vcode' or 'mcode'."},

    {"append",    code_append,    METH_VARARGS,
     "Append a single chunk of data."},

    {NULL}
};

static PySequenceMethods code_seq_methods;

static int
code_init(PyObject *arg_self, PyObject *args, PyObject *kwds)
{
  code_t *self;

  assert(arg_self->ob_type == &code_type);
  self = (code_t *)arg_self;
  self->num_in_buf    = 0;
  self->size_of_buf   = 1024;
  self->is_vcode      = 0;
  self->obj_size      = 1;

  self->u.buf         = calloc(self->obj_size, self->size_of_buf);

  return 0;
}

static void
code_dealloc(PyObject *arg_self)
{
  code_t *self;
  int i;

  assert(arg_self->ob_type == &code_type);
  self = (code_t *)arg_self;
  if (self->is_vcode) {
    for (i=0; i<self->num_in_buf; i++)
      Py_DECREF(self->u.obuf[i]);
    free(self->u.obuf);
    self->u.obuf = 0;
  }

  arg_self->ob_type->tp_free(arg_self);
  return;
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
code_item(PyObject *arg_self, Py_ssize_t i)
{
  code_t *self;

  assert(arg_self->ob_type == &code_type);
  self = (code_t *)arg_self;
  if (i < 0 || i > self->num_in_buf) {
    PyErr_Format(PyExc_RuntimeError, "code_item index out of range");
    return 0;
  }

  if (self->is_vcode) {
    Py_INCREF(self->u.obuf[i]);
    return self->u.obuf[i];
  }

  Py_INCREF(Py_None);
  return Py_None;
}

static PyObject *
code_get_token(PyObject *arg_self, PyObject *args)
{
  code_t *self;
  PyObject *lbuf, *m, *d, *func, *res;

  assert(arg_self->ob_type == &code_type);
  self = (code_t *)arg_self;
  
  if (!PyArg_ParseTuple(args, "O!:get_token", &lexer_state_type, &lbuf))
    return 0;

  if (self->is_vcode) {
    m = PyImport_ImportModule("pylex");
    if (m==0)
      return 0;
    d = PyModule_GetDict(m);
    Py_DECREF(m);
    if (d==0)
      return 0;
    func = PyDict_GetItemString(d, "run_vcode_simulation");
    if (func == 0)
      return 0;
    if (!PyFunction_Check(func)) {
      PyErr_Format(PyExc_RuntimeError, "run_vcode_simulation not a function");
      return 0;
    }
    res = PyObject_CallFunctionObjArgs(func, arg_self, lbuf, 0);
    return res;
  }

  Py_INCREF(Py_None);
  return Py_None;
}

static PyObject *
code_set_type(PyObject *arg_self, PyObject *args)
{
  code_t *self;
  char *type_name;

  assert(arg_self->ob_type == &code_type);
  self = (code_t *)arg_self;

  if (self->num_in_buf != 0) {
    PyErr_Format(PyExc_RuntimeError, "set_type can only be called on "
		 "empty code objects");
    return 0;
  }
  if (!PyArg_ParseTuple(args, "s:set_type", &type_name))
    return 0;

  if (strcmp(type_name, "vcode")==0) {
    self->obj_size = 4;
    self->is_vcode = 1;
  }
  else if (strcmp(type_name, "mcode")==0) {
    self->obj_size = 1;
    self->is_vcode = 0;
  }
  else {
    PyErr_Format(PyExc_RuntimeError, "Unknown type for code object");
    return 0;
  }

  Py_INCREF(Py_None);
  return Py_None;
}

static PyObject *
code_append(PyObject *arg_self, PyObject *args)
{
  code_t *self;
  PyObject *tup;

  assert(arg_self->ob_type == &code_type);
  self = (code_t *)arg_self;
  assert(self->num_in_buf <= self->size_of_buf);

  if (self->is_vcode) {
    if (!PyArg_ParseTuple(args, "O", &tup))
      return 0;
    if (!PyTuple_Check(tup)) {
      PyErr_Format(PyExc_RuntimeError, "vcode code objects can only "
		   "append tuples.");
      return 0;
    }
    if (self->num_in_buf == self->size_of_buf)
      code_grow(self);
    Py_INCREF(tup);
    self->u.obuf[ self->num_in_buf ] = tup;
    self->num_in_buf++;
  }
  else {
    PyErr_Format(PyExc_RuntimeError, "Not yet supported.");
    return 0;
  }

  Py_INCREF(Py_None);
  return Py_None;
}

static void
code_grow(code_t *self)
{
  self->size_of_buf = 2 * self->size_of_buf;
  self->u.buf         = realloc(self->u.buf,
				self->size_of_buf * self->obj_size);
  assert(self->u.buf != 0);
  return;
}

/***************************************************************/
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

#if 0
  pid_t pid;
  pid = getpid();
  printf("pid= %d\n", pid);
  sleep(10);
#endif

  m = Py_InitModule3("escape", escape_methods, module_doc);
  if (m == NULL)
    return;

  /****************************/
  /* lexer state support      */
  /****************************/
  lexer_state_type.tp_name        = "escape.lexer_state";
  lexer_state_type.tp_basicsize   = sizeof(lexer_state_t);
  lexer_state_type.tp_new         = PyType_GenericNew;
  lexer_state_type.tp_dealloc     = lexer_state_dealloc;
  lexer_state_type.tp_methods     = lexer_state_methods;
  lexer_state_type.tp_flags       = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE;
  lexer_state_type.tp_doc         = "Full state for lexer code objs.";
  lexer_state_type.tp_init        = lexer_state_init;

  code = PyType_Ready(&lexer_state_type);
  if (code < 0)
    return;

  Py_INCREF(&lexer_state_type);
  code = PyModule_AddObject(m, "lexer_state", (PyObject *)&lexer_state_type);
  if (code < 0)
    return;

  /****************************/
  /* runtime code obj support */
  /****************************/
  code_type.tp_name        = "escape.code";
  code_type.tp_basicsize   = sizeof(code_t);
  code_type.tp_new         = PyType_GenericNew;
  code_type.tp_dealloc     = code_dealloc;
  code_type.tp_methods     = code_methods;
  code_type.tp_flags       = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE;
  code_type.tp_doc         = "Container for all executable code.";
  code_type.tp_init        = code_init;
  code_type.tp_as_sequence = &code_seq_methods;

  code_seq_methods.sq_length = code_len;
  code_seq_methods.sq_item   = code_item;


  code = PyType_Ready(&code_type);
  if (code < 0)
    return;

  Py_INCREF(&code_type);
  code = PyModule_AddObject(m, "code", (PyObject *)&code_type);
  if (code < 0)
    return;

  return;
}
