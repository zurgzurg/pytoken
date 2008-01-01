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
static PyObject *lexer_state_set_fill_method(PyObject *, PyObject *);
static PyObject *lexer_state_set_eob_found(PyObject *, PyObject *);
static PyObject *lexer_state_get_eob_found(PyObject *, PyObject *);

static PyObject *lexer_state_ldb(PyObject *, PyObject *);
static PyObject *lexer_state_ldw(PyObject *, PyObject *);
static PyObject *lexer_state_stb(PyObject *, PyObject *);
static PyObject *lexer_state_stw(PyObject *, PyObject *);

static int  *lexer_state_get_word_ptr(PyObject *);
static char *lexer_state_get_char_ptr(PyObject *);

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

  char           *next_char_ptr;
  char           *buf;
  int             size_of_buf;
  PyObject       *fill_ptr;
  int             eob_found;
} lexer_state_t;

static int is_valid_ptr(lexer_state_t *, char *);
static int is_valid_word_ptr(lexer_state_t *, int *);
static int is_valid_lstate_ptr(lexer_state_t *self, void *ptr);

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
    {"set_fill_method",   lexer_state_set_fill_method,   METH_VARARGS,
     "Set source of chars to read."},
    {"set_eob_found",     lexer_state_set_eob_found,     METH_VARARGS,
     "Set the eob_found flag."},
    {"get_eob_found",     lexer_state_get_eob_found,     METH_NOARGS,
     "Get the eob_found flag."},

    {"ldb",               lexer_state_ldb,               METH_VARARGS,
     "simulator method - load byte"},
    {"ldw",               lexer_state_ldw,               METH_VARARGS,
     "simulator method - load word"},
    {"stb",               lexer_state_stb,               METH_VARARGS,
     "simulator method - store byte"},
    {"stw",               lexer_state_stw,               METH_VARARGS,
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
  self->eob_found     = 0;
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
    PyErr_Format(PyExc_RuntimeError, "set_offset: no input has been set");
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
    PyErr_Format(PyExc_RuntimeError, "get_offset: no input has been set");
    return 0;
  }

  if (!is_valid_ptr(self, self->next_char_ptr))
    return 0;

  result = PyLong_FromUnsignedLong(self->next_char_ptr - self->buf);
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
    PyErr_Format(PyExc_RuntimeError, "get_addr: no input has been set");
    return 0;
  }

  if (!is_valid_ptr(self, self->next_char_ptr))
    return 0;

  result = PyLong_FromUnsignedLong((long)self->next_char_ptr);
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
  self->buf = malloc(tmp_buf_len + 2);
  self->size_of_buf = tmp_buf_len + 2;
  for (i=0; i<tmp_buf_len; i++)
    self->buf[i] = tmp_buf[i];
  self->buf[tmp_buf_len]     = '\0';
  self->buf[tmp_buf_len + 1] = '\0';
  self->next_char_ptr = self->buf;

  Py_INCREF(Py_None);
  return Py_None;
}

static PyObject *
lexer_state_set_fill_method(PyObject *arg_self, PyObject *args)
{
  lexer_state_t *self;
  PyObject *func;

  assert(arg_self->ob_type == &lexer_state_type);
  self = (lexer_state_t *)arg_self;
  if (!PyArg_ParseTuple(args, "O:set_fill_method", &func))
    return 0;
  if ( PyCallable_Check(func) != 1) {
    PyErr_Format(PyExc_RuntimeError, "Fill method is not callable");
    return 0;
  }
  Py_INCREF(func);
  self->fill_ptr = func;

  Py_INCREF(Py_None);
  return Py_None;
}

static PyObject *
lexer_state_set_eob_found(PyObject *arg_self, PyObject *args)
{
  lexer_state_t *self;
  int val;

  assert(arg_self->ob_type == &lexer_state_type);
  self = (lexer_state_t *)arg_self;
  if (!PyArg_ParseTuple(args, "i:set_eob_found", &val))
    return 0;

  if (val!=0 && val!=1) {
    PyErr_Format(PyExc_RuntimeError, "Can only set to 0 or 1.");
    return 0;
  }

  self->eob_found = val;
  Py_INCREF(Py_None);
  return Py_None;
}

static PyObject *
lexer_state_get_eob_found(PyObject *arg_self, PyObject *args)
{
  lexer_state_t *self;
  PyObject *result;

  assert(arg_self->ob_type == &lexer_state_type);
  self = (lexer_state_t *)arg_self;
  assert(self->eob_found==0 || self->eob_found==1);
  result = PyInt_FromLong(self->eob_found);
  return result;
}

static PyObject *
lexer_state_ldb(PyObject *arg_self, PyObject *args)
{
  lexer_state_t *self;
  char *ptr, ch;
  PyObject *obj_arg, *result;

  assert(arg_self->ob_type == &lexer_state_type);
  self = (lexer_state_t *)arg_self;
  if (!PyArg_ParseTuple(args, "O:ldb", &obj_arg))
    return 0;
  ptr = lexer_state_get_char_ptr(obj_arg);
  if (ptr == 0)
    return 0;
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
  int *ptr;
  long val;
  PyObject *result, *obj_arg;

  assert(arg_self->ob_type == &lexer_state_type);
  self = (lexer_state_t *)arg_self;

  if (!PyArg_ParseTuple(args, "O:ldw", &obj_arg))
    return 0;
  ptr = lexer_state_get_word_ptr(obj_arg);
  if (ptr == 0)
    return 0;
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
  int val;
  char *dst_ptr, ch;
  PyObject *obj_arg;

  assert(arg_self->ob_type == &lexer_state_type);
  self = (lexer_state_t *)arg_self;
  if (!PyArg_ParseTuple(args, "Oi:stb", &obj_arg, &val))
    return 0;
  dst_ptr = lexer_state_get_char_ptr(obj_arg);
  if (dst_ptr==0)
    return 0;
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
  int val, *dst_ptr;
  PyObject *obj_arg;

  assert(arg_self->ob_type == &lexer_state_type);
  self = (lexer_state_t *)arg_self;
  if (!PyArg_ParseTuple(args, "Oi:stw", &obj_arg, &val))
    return 0;
  dst_ptr = lexer_state_get_word_ptr(obj_arg);
  if (dst_ptr == 0)
    return 0;
  if (!is_valid_word_ptr(self, dst_ptr))
    return 0;
  
  *dst_ptr = val;

  Py_INCREF(Py_None);
  return Py_None;
}

static int  *
lexer_state_get_word_ptr(PyObject *obj)
{
  unsigned long ul;
  int *result;

  assert(obj != 0);
  if (PyInt_Check(obj) || PyLong_Check(obj)) {
    ul = PyInt_AsUnsignedLongMask(obj);
    result = (int *)ul;
    return result;
  }

  PyErr_Format(PyExc_RuntimeError, "cannot get word pointer from non-num.");
  return 0;
}

static char *
lexer_state_get_char_ptr(PyObject *obj)
{
  unsigned long ul;
  char *result;

  assert(obj != 0);
  if (PyInt_Check(obj) || PyLong_Check(obj)) {
    ul = PyInt_AsUnsignedLongMask(obj);
    result = (char *)ul;
    return result;
  }

  PyErr_Format(PyExc_RuntimeError, "cannot get char pointer from non-num.");
  return 0;
}

static int
is_valid_ptr(lexer_state_t *self, char *ch_ptr)
{
  if (is_valid_lstate_ptr(self, ch_ptr))
    return 1;
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
  if (is_valid_lstate_ptr(self, w_ptr))
    return 1;
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

static int
is_valid_lstate_ptr(lexer_state_t *self, void *ptr)
{
  char *start, *end, *ptr2;

  start = (char *)self;
  end = start + sizeof(lexer_state_t);

  ptr2 = (char *)ptr;
  if (ptr2 >= start && ptr2 <= end)
    return 1;
  return 0;
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

static PyObject *code_get_token(PyObject *, PyObject *, PyObject *);
static PyObject *code_set_type(PyObject *, PyObject *);
static PyObject *code_append(PyObject *, PyObject *);
static PyObject *code_get_start_addr(PyObject *, PyObject *);
static PyObject *code_get_code(PyObject *, PyObject *);

static PyObject *code_get_fill_caller_addr(PyObject *, PyObject *);
static int code_call_fill_ptr(lexer_state_t *self);

typedef struct {
  PyObject_HEAD

  union {
    char      *buf;
    PyObject **obuf;
  } u;
  int     size_of_buf; /* in objects */
  int     num_in_buf;  /* num objs   */
  int     obj_size;    /* machine code : obj_size=1 : bytes */
                       /* vcode : obj_size=4 : PyObjects - likely tuples */

  int     is_vcode;
} code_t;

static void code_grow(code_t *);

static PyTypeObject code_type = {
  PyObject_HEAD_INIT(NULL)
};

static PyMethodDef code_methods[] = {
    {"get_token", (PyCFunction)code_get_token, METH_KEYWORDS,
     "Return the next token."},

    {"set_type",  code_set_type,  METH_VARARGS,
     "Set type of code object to 'vcode' or 'mcode'."},

    {"append",    code_append,    METH_VARARGS,
     "Append a single chunk of data."},

    {"get_start_addr", code_get_start_addr, METH_NOARGS,
     "Return start address of code buffer."},

    {"get_fill_caller_addr", code_get_fill_caller_addr, METH_NOARGS,
     "Return address of function that can call the lexer_state fill method."},

    {"get_code",  code_get_code, METH_NOARGS,
     "Return code buffer."},

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
code_get_token(PyObject *arg_self, PyObject *args, PyObject *kwdict)
{
  code_t *code_obj_ptr;
  PyObject *lbuf, *m, *d, *func, *res, *bool_db_flag;
  typedef int (*asm_func_t)(code_t *, lexer_state_t *);
  asm_func_t asm_func;
  int debug_flag, v;
  static char *kwlist[] = {"lexer_state", "debug", 0};

  unsigned char *base;
  int status;

  assert(arg_self->ob_type == &code_type);
  code_obj_ptr = (code_t *)arg_self;
  
  debug_flag = 0;
  if (!PyArg_ParseTupleAndKeywords(args, kwdict, "O!|i:get_token", kwlist,
				   &lexer_state_type, &lbuf, &debug_flag))
    return 0;

  if (code_obj_ptr->is_vcode) {
    bool_db_flag = PyBool_FromLong(debug_flag);

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
    res = PyObject_CallFunctionObjArgs(func, arg_self, lbuf, bool_db_flag, 0);
    return res;
  }

  //__asm__ __volatile__ ( "mfence" : : : "memory" );
  base = (unsigned char *)((unsigned int)code_obj_ptr->u.buf & 0xFFFFF000);
  status = mprotect(base, 4096, PROT_READ | PROT_WRITE | PROT_EXEC);
  if (status != 0) {
    perror("mprotect failed.\n");
    exit(1);
  }

  asm_func = (asm_func_t)(code_obj_ptr->u.buf);
  v = (*asm_func)(code_obj_ptr, (lexer_state_t*)lbuf);
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

static PyObject *
code_get_start_addr(PyObject *arg_self, PyObject *args)
{
  code_t *self;
  PyObject *result;

  assert(arg_self->ob_type == &code_type);
  self = (code_t *)arg_self;
  if (self->u.buf == 0) {
    Py_INCREF(Py_None);
    return Py_None;
  }

  result = PyLong_FromLong((long)self->u.buf);
  return result;
}

static PyObject *
code_get_code(PyObject *arg_self, PyObject *args)
{
  code_t *self;
  PyObject *result;

  assert(arg_self->ob_type == &code_type);
  self = (code_t *)arg_self;
  if (self->is_vcode) {
    Py_INCREF(Py_None);
    return Py_None;
  }

  result = PyString_FromStringAndSize(self->u.buf, self->num_in_buf);
  return result;
}

/****************************************************************/
/*                                                              */
/* fill protocol - when end of buffer is found the fill method  */
/* will be called. The method should return 0 if no new data is */
/* added to the buffer. A 1 should be returned if new data is   */
/* added to the buffer, -- need to figure out how to shift the  */
/* buffer contents. A 2 indicates some kind of error, a python  */
/* error is expected to be set.                                 */
/*                                                              */
/****************************************************************/
static PyObject *
code_get_fill_caller_addr(PyObject *arg_self, PyObject *args)
{
  PyObject *result;
  long addr;

  addr = (long)&code_call_fill_ptr;
  result = PyInt_FromLong(addr);
  return result;
}

static int
code_call_fill_ptr(lexer_state_t *lstate)
{
  PyObject *fill_status, *arg_list;
  long val;

  if (lstate == 0) {
    PyErr_Format(PyExc_RuntimeError, "null lexer state sent to fill runtime");
    return 2;
  }
  if (lstate->fill_ptr == 0) {
    PyErr_Format(PyExc_RuntimeError, "no fill pointer set in lexer state obj");
    return 2;
  }
  arg_list = Py_BuildValue("(O)", lstate);
  if (arg_list == 0)
    return 2;

  fill_status = PyObject_Call(lstate->fill_ptr, arg_list, 0);
  if (fill_status == 0)
    return 2;

  if ( ! PyNumber_Check(fill_status)) {
    PyErr_Format(PyExc_RuntimeError, "Fill method returned non-numeric");
    Py_DECREF(fill_status);
    return 2;
  }

  val = PyInt_AsLong(fill_status);
  Py_DECREF(fill_status);
  if (val != 0 && val != 1) {
    PyErr_Format(PyExc_RuntimeError,
		 "Unexpected return val from fill method=%ld", val);
    return 2;
  }
  

  return val;
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
  long long llval;
  long lval;
  PyObject *obj;

  if (!PyArg_ParseTuple(args, "L:get_obj_from_id", &llval))
    return 0;
  lval = llval;
  obj = (PyObject *)lval;
  if (obj->ob_type != &lexer_state_type) {
    PyErr_SetString(PyExc_RuntimeError, "Bad id - not lex_state obj.");
    return 0;
  }
  Py_INCREF(obj);
  return obj;
}

static PyObject *
escape_get_char_ptr_offset(PyObject *self, PyObject *args)
{
  lexer_state_t lstate;
  char *p1, *p2;
  int offset;
  PyObject *result;
  
  p1 = (char *)&lstate;
  p2 = (char *)&lstate.next_char_ptr;
  offset = p2 - p1;
  result = PyInt_FromLong(offset);
  return result;
}

static PyObject *
escape_get_eob_found_offset(PyObject *self, PyObject *args)
{
  lexer_state_t lstate;
  char *p1, *p2;
  int offset;
  PyObject *result;
  
  p1 = (char *)&lstate;
  p2 = (char *)&lstate.eob_found;
  offset = p2 - p1;
  result = PyInt_FromLong(offset);
  return result;
}

static PyObject *
escape_get_fill_caller_addr(PyObject *self, PyObject *args)
{
  long addr;
  PyObject *r;

  addr = (long)&code_call_fill_ptr;
  r = PyInt_FromLong(addr);
  return r;
}

static PyObject *
escape_regtest01(PyObject *self, PyObject *args)
{
  PyObject *lbuf, *result;

  if (!PyArg_ParseTuple(args, "O!:", &lexer_state_type, &lbuf))
    return 0;
  result = PyObject_CallMethod(lbuf, "get_cur_addr", 0);
  return result;
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

  {"get_char_ptr_offset", escape_get_char_ptr_offset, METH_NOARGS,
   PyDoc_STR("Return lex state offset for character pos ptr.")},

  {"get_eob_found_offset", escape_get_eob_found_offset, METH_NOARGS,
   PyDoc_STR("Return lex state offset for eob_found flag.")},

  {"get_fill_caller_addr", escape_get_fill_caller_addr, METH_NOARGS,
   PyDoc_STR("Get address of code_call_fill_ptr function.")},

  {"regtest01",        escape_regtest01,         METH_VARARGS, NULL},
   

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
