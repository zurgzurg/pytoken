#include "Python.h"

#include <sys/types.h>
#include <unistd.h>
#include <sys/mman.h>
#include <limits.h>

/***************************************************************/
/***************************************************************/
/***                                                         ***/
/*** lexer state - buffer to scan, position in buffer and    ***/
/*** any misc data                                           ***/
/***                                                         ***/
/***************************************************************/
/***************************************************************/
static int lexer_state_init(PyObject *, PyObject *, PyObject *);
static void lexer_state_dealloc(PyObject *);

static PyObject *lexer_state_has_data(PyObject *, PyObject *);

static PyObject *lexer_state_set_cur_offset(PyObject *, PyObject *);
static PyObject *lexer_state_get_cur_offset(PyObject *, PyObject *);
static PyObject *lexer_state_set_cur_addr(PyObject *, PyObject *);
static PyObject *lexer_state_get_cur_addr(PyObject *, PyObject *);
static PyObject *lexer_state_set_input(PyObject *, PyObject *);

static PyObject *lexer_state_ldb(PyObject *, PyObject *);
static PyObject *lexer_state_ldw(PyObject *, PyObject *);
static PyObject *lexer_state_stb(PyObject *, PyObject *);
static PyObject *lexer_state_stw(PyObject *, PyObject *);


/*******************************************/
/*                                         */
/* next_char_ptr points to the next char   */
/* to be read. Or it can point to one byte */
/* past the end of the buffer to signify   */
/* there is no more input                  */
/*                                         */
/* word read and write are done with the   */
/* native endian style.                    */
/*                                         */
/*******************************************/
typedef struct {
  PyObject_HEAD

  char   *next_char_ptr;
  char   *buf;
  int     size_of_buf;
} lexer_state_t;

static int is_valid_ptr(lexer_state_t *, char *);
static int is_valid_word_ptr(lexer_state_t *, int *);

static PyTypeObject lexer_state_type = {
  PyObject_HEAD_INIT(NULL)
};

static PyMethodDef lexer_state_methods[] = {
    {"has_data",          lexer_state_has_data,          METH_NOARGS,
     "Set index of next valid character to scan."},

    {"set_cur_offset",    lexer_state_set_cur_offset,    METH_VARARGS,
     "Set index of next valid character to scan."},

    {"get_cur_offset",    lexer_state_get_cur_offset,    METH_NOARGS,
     "Return index of next char to scan."},

    {"set_cur_addr",      lexer_state_set_cur_addr,      METH_VARARGS,
     "Return index of next char to scan."},

    {"get_cur_addr",      lexer_state_get_cur_addr,      METH_NOARGS,
     "Return index of next char to scan."},

    {"set_input",         lexer_state_set_input,         METH_VARARGS,
     "Set source of chars to read."},

    {"ldb",       lexer_state_ldb,                 METH_VARARGS,
     "simulator method - load byte"},
    {"ldw",       lexer_state_ldw,                 METH_VARARGS,
     "simulator method - load word"},
    {"stb",       lexer_state_stb,                 METH_VARARGS,
     "simulator method - store byte"},
    {"stw",       lexer_state_stw,                 METH_VARARGS,
     "simulator method - store word"},

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
lexer_state_has_data(PyObject *arg_self, PyObject *args)
{
  lexer_state_t *self;

  assert(arg_self->ob_type == &lexer_state_type);
  self = (lexer_state_t *)arg_self;
  if (self->buf!=0 && self->size_of_buf>0 && self->next_char_ptr!=0) {
    Py_INCREF(Py_True);
    return Py_True;
  }
  Py_INCREF(Py_False);
  return Py_False;
}

static PyObject *
lexer_state_set_cur_offset(PyObject *arg_self, PyObject *args)
{
  lexer_state_t *self;
  int offset;

  assert(arg_self->ob_type == &lexer_state_type);
  self = (lexer_state_t *)arg_self;
  if (!PyArg_ParseTuple(args, "i:set_cur_offset", &offset))
    return 0;
  if (self->buf==0 || self->size_of_buf==0) {
    PyErr_Format(PyExc_RuntimeError, "no input has been set");
    return 0;
  }
  if (!is_valid_ptr(self, self->buf + offset))
    return 0;
  self->next_char_ptr = self->buf + offset;

  Py_INCREF(Py_None);
  return Py_None;
}

static PyObject *
lexer_state_get_cur_offset(PyObject *arg_self, PyObject *args)
{
  lexer_state_t *self;
  PyObject *result;

  assert(arg_self->ob_type == &lexer_state_type);
  self = (lexer_state_t *)arg_self;
  if (self->buf==0 || self->size_of_buf==0) {
    PyErr_Format(PyExc_RuntimeError, "no input has been set");
    return 0;
  }

  if (!is_valid_ptr(self, self->next_char_ptr))
    return 0;

  result = PyInt_FromLong(self->next_char_ptr - self->buf);
  return result;
}

static PyObject *
lexer_state_get_cur_addr(PyObject *arg_self, PyObject *args)
{
  lexer_state_t *self;
  PyObject *result;

  assert(arg_self->ob_type == &lexer_state_type);
  self = (lexer_state_t *)arg_self;
  if (self->buf==0 || self->size_of_buf==0) {
    PyErr_Format(PyExc_RuntimeError, "no input has been set");
    return 0;
  }

  if (!is_valid_ptr(self, self->next_char_ptr))
    return 0;

  result = PyInt_FromLong((long)self->next_char_ptr);
  return result;
}

static PyObject *
lexer_state_set_cur_addr(PyObject *arg_self, PyObject *args)
{
  lexer_state_t *self;
  int ival;
  char *ptr;

  assert(arg_self->ob_type == &lexer_state_type);
  self = (lexer_state_t *)arg_self;
  if (!PyArg_ParseTuple(args, "i:set_cur_addr", &ival))
    return 0;
  ptr = (char *)ival;
  if (!is_valid_ptr(self, ptr))
    return 0;
  self->next_char_ptr = (char *)ptr;

  Py_INCREF(Py_None);
  return Py_None;
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

static PyObject *
lexer_state_ldb(PyObject *arg_self, PyObject *args)
{
  lexer_state_t *self;
  int i;
  char *ptr, ch;
  PyObject *result;

  assert(arg_self->ob_type == &lexer_state_type);
  self = (lexer_state_t *)arg_self;
  if (!PyArg_ParseTuple(args, "i:ldb", &i))
    return 0;
  ptr = (char *)i;
  if (!is_valid_ptr(self, ptr))
    return 0;
  ch = *ptr;
  result = PyInt_FromLong(ch);
  return result;
}

static PyObject *
lexer_state_ldw(PyObject *arg_self, PyObject *args)
{
  lexer_state_t *self;
  int i, val, *ptr;
  PyObject *result;

  assert(arg_self->ob_type == &lexer_state_type);
  self = (lexer_state_t *)arg_self;
  if (!PyArg_ParseTuple(args, "i:ldw", &i))
    return 0;
  ptr = (int *)i;
  if (!is_valid_word_ptr(self, ptr))
    return 0;
  val = *ptr;
  result = PyInt_FromLong(val);
  return result;
}

static PyObject *
lexer_state_stb(PyObject *arg_self, PyObject *args)
{
  lexer_state_t *self;
  int ptr_as_int, val;
  char *dst_ptr, ch;

  assert(arg_self->ob_type == &lexer_state_type);
  self = (lexer_state_t *)arg_self;
  if (!PyArg_ParseTuple(args, "ii:stb", &ptr_as_int, &val))
    return 0;
  dst_ptr = (char *)ptr_as_int;
  if (!is_valid_ptr(self, dst_ptr))
    return 0;

  if (val<0 || val > 0xFF) {
    PyErr_Format(PyExc_RuntimeError, "val out of range to store in byte");
    return 0;
  }

  ch = val;
  *dst_ptr = ch;

  Py_INCREF(Py_None);
  return Py_None;
}

static PyObject *
lexer_state_stw(PyObject *arg_self, PyObject *args)
{
  lexer_state_t *self;
  int ptr_as_int, val, *dst_ptr;

  assert(arg_self->ob_type == &lexer_state_type);
  self = (lexer_state_t *)arg_self;
  if (!PyArg_ParseTuple(args, "ii:stw", &ptr_as_int, &val))
    return 0;
  dst_ptr = (int *)ptr_as_int;
  if (!is_valid_word_ptr(self, dst_ptr))
    return 0;
  
  *dst_ptr = val;

  Py_INCREF(Py_None);
  return Py_None;
}

static int
is_valid_ptr(lexer_state_t *self, char *ch_ptr)
{
  if (ch_ptr < self->buf) {
    PyErr_Format(PyExc_RuntimeError, "Invalid char pointer: before buf");
    return 0;
  }
  if (ch_ptr >= self->buf + self->size_of_buf + 1) {
    PyErr_Format(PyExc_RuntimeError, "Invalid char pointer: after buf");
    return 0;
  }
  return 1;
}

static int
is_valid_word_ptr(lexer_state_t *self, int *w_ptr)
{
  if ((char *)w_ptr < self->buf) {
    PyErr_Format(PyExc_RuntimeError, "Invalid word pointer: before buf");
    return 0;
  }
  if ((char *)w_ptr >= self->buf + self->size_of_buf - sizeof(int)) {
    PyErr_Format(PyExc_RuntimeError, "Invalid word pointer: after buf");
    return 0;
  }
  return 1;
}

/***************************************************************/
/***************************************************************/
/***                                                         ***/
/*** the actual code objects - supports vcode - or actual    ***/
/*** machine code. vcode is designed to be interpreted by    ***/
/*** the python simulator function in pylex.py               ***/
/***                                                         ***/
/***************************************************************/
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
  typedef int (*asm_func_t)(code_t *, lexer_state_t *);
  asm_func_t asm_func;
  int v;

  unsigned char *base;
  int status;

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

  //__asm__ __volatile__ ( "mfence" : : : "memory" );
  base = (unsigned char *)((unsigned int)self->u.buf & 0xFFFFF000);
  status = mprotect(base, 4096, PROT_READ | PROT_WRITE | PROT_EXEC);
  if (status != 0) {
    perror("mprotect failed.\n");
    exit(1);
  }

  asm_func = (asm_func_t)(self->u.buf);
  v = (*asm_func)(self, (lexer_state_t*)lbuf);
  res = PyInt_FromLong(v);
  return res;
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
  int ival;

  assert(arg_self->ob_type == &code_type);
  self = (code_t *)arg_self;
  assert(self->num_in_buf <= self->size_of_buf);

  if (self->is_vcode) {
    if (!PyArg_ParseTuple(args, "O:append", &tup))
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

    Py_INCREF(Py_None);
    return Py_None;
  }

  if (!PyArg_ParseTuple(args, "i:append", &ival))
    return 0;
  if (self->num_in_buf == self->size_of_buf)
    code_grow(self);
  self->u.buf[ self->num_in_buf ] = (char)(ival & 0xFF);
  self->num_in_buf++;

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
/***************************************************************/
/***                                                         ***/
/*** general low-level helper funcs                          ***/
/***                                                         ***/
/***************************************************************/
/***************************************************************/
static PyObject *
escape_get_func_addr(PyObject *self, PyObject *args)
{
  char *func_name;
  void *func_ptr;
  PyObject *result;

  if (!PyArg_ParseTuple(args, "s:get_func_addr", &func_name))
    return 0;
  if (strcmp(func_name, "PyObject_CallMethod")==0)
    func_ptr = &PyObject_CallMethod;
  else {
    PyErr_SetString(PyExc_RuntimeError, "Unknown function name");
    return 0;
  }

  result = PyInt_FromLong((long)func_ptr);
  return result;
}

static PyObject *
escape_get_bytes(PyObject *self, PyObject *args)
{
  char *ptr;
  int   n_bytes;
  PyObject *result;

  if (!PyArg_ParseTuple(args, "ii:get_bytes", &ptr, &n_bytes))
    return 0;
  result = PyString_FromStringAndSize(ptr, n_bytes);
  return result;
}

static PyObject *
escape_print_gdb_info(PyObject *self, PyObject *args)
{
  pid_t pid;
  pid = getpid();

  printf("pid= %d\n", pid);
  sleep(10);

  Py_INCREF(Py_None);
  return Py_None;
}

static PyObject *
escape_get_obj_from_id(PyObject *self, PyObject *args)
{
  int ival;
  PyObject *obj;

  if (!PyArg_ParseTuple(args, "i:get_obj_from_id", &ival))
    return 0;
  obj = (PyObject *)ival;
  if (obj->ob_type != &lexer_state_type) {
    PyErr_SetString(PyExc_RuntimeError, "Bad id - not lex_state obj.");
    return 0;
  }
  Py_INCREF(obj);
  return obj;
}

static PyMethodDef escape_methods[] = {
  {"get_func_addr",    escape_get_func_addr,     METH_VARARGS,
   PyDoc_STR("Return address of certain python C api functions.")},

  {"get_bytes",        escape_get_bytes,         METH_VARARGS,
   PyDoc_STR("Print process id and pause.")},

  {"print_gdb_info",   escape_print_gdb_info,    METH_NOARGS,
   PyDoc_STR("Print process id and pause.")},

  {"get_obj_from_id",  escape_get_obj_from_id,   METH_VARARGS,
   PyDoc_STR("Turn a python id back into an object.")},

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
