/*

Copyright (c) 2008-2009, Ram Bhamidipaty
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are
met:

    * Redistributions of source code must retain the above
      copyright notice, this list of conditions and the
      following disclaimer.

    * Redistributions in binary form must reproduce the above
      copyright notice, this list of conditions and the following
      disclaimer in the documentation and/or other materials
      provided with the distribution.

    * Neither the name of Ram Bhamidipaty nor the names of its
      contributors may be used to endorse or promote products
      derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
"AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

*/

#include "Python.h"

#include <sys/types.h>
#include <unistd.h>
#include <sys/mman.h>
#include <stdint.h>
#include <limits.h>

#define PYTOKEN_DEBUG 0

static int  escape_stop_here_counter = 0;
void escape_stop_here(void);

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
static PyObject *lexer_state_get_match_text(PyObject *, PyObject *);
static PyObject *lexer_state_set_input(PyObject *, PyObject *);
static PyObject *lexer_state_set_fill_method(PyObject *, PyObject *);
static PyObject *lexer_state_get_all_state(PyObject *, PyObject *);

static PyObject *lexer_state_add_to_buffer(PyObject *, PyObject *);

static PyObject *lexer_state_ldb(PyObject *, PyObject *);
static PyObject *lexer_state_ldw(PyObject *, PyObject *);
static PyObject *lexer_state_stb(PyObject *, PyObject *);
static PyObject *lexer_state_stw(PyObject *, PyObject *);

static int  *lexer_state_get_word_ptr(PyObject *);
static char *lexer_state_get_char_ptr(PyObject *);

static PyObject *lexer_state_repr(PyObject *);
static PyObject *lexer_state_str(PyObject *);

/***************************************************************/
/***************************************************************/
/***                                                         ***/
/*** uval32_t --> simple uint32_t wrapper                    ***/
/***                                                         ***/
/***************************************************************/
/***************************************************************/
static int uval32_init(PyObject *, PyObject *, PyObject *);
static void uval32_dealloc(PyObject *);
static PyObject *uval32_repr(PyObject *);
static PyObject *uval32_str(PyObject *);

static PyObject *uval32_get_str(PyObject *, PyObject *);

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

  char           *buf;
  char           *next_char_ptr;
  char           *start_of_token;
  int             size_of_buf;

  int             chars_in_buf;
  /* there are two extra null chars in the buffer - used to mark the end
     of buffer. Those two are always counted as being part of the number
     of chars in the buffer. */

  PyObject       *fill_obj;
} lexer_state_t;

static int is_valid_ptr(lexer_state_t *, char *);
static int is_valid_word_ptr(lexer_state_t *, int *);
static int is_valid_lstate_ptr(lexer_state_t *self, void *ptr);

#if PYTOKEN_DEBUG
static void lexer_state_print_buf(lexer_state_t *, int n_to_print);
#endif

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

    {"get_match_text",     lexer_state_get_match_text,   METH_NOARGS,
     "Add ARG to buffer. ARG can be a string."},


    {"set_input",         lexer_state_set_input,         METH_VARARGS,
     "Set source of chars to read."},
    {"set_fill_method",   lexer_state_set_fill_method,   METH_VARARGS,
     "Set source of chars to read."},

    {"add_to_buffer",     lexer_state_add_to_buffer,     METH_VARARGS,
     "Add ARG to buffer. ARG can be a string."},

    {"get_all_state",     lexer_state_get_all_state,     METH_NOARGS,
     "Return base ptr, buf size, next char ptr as tuple."},

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

  self->buf            = 0;
  self->next_char_ptr  = 0;
  self->start_of_token = 0;
  self->size_of_buf    = 0;
  self->chars_in_buf   = 0;
  self->fill_obj       = 0;

  return 0;
}

static void
lexer_state_dealloc(PyObject *arg_self)
{
  lexer_state_t *self;

  assert(arg_self->ob_type == &lexer_state_type);
  self = (lexer_state_t *)arg_self;
  if (self->buf) {
    memset(self->buf, 0, self->size_of_buf);
    free(self->buf);
  }
  self->buf            = 0;
  self->next_char_ptr  = 0;
  self->start_of_token = 0;
  self->size_of_buf    = 0;
  self->chars_in_buf   = 0;
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
    return NULL;
  if (self->buf==0 || self->size_of_buf==0) {
    PyErr_Format(PyExc_RuntimeError, "set_offset: no input has been set");
    return NULL;
  }
  if (!is_valid_ptr(self, self->buf + offset))
    return NULL;
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
    return NULL;
  }

  if (!is_valid_ptr(self, self->next_char_ptr))
    return NULL;

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
    return NULL;
  }

  if (!is_valid_ptr(self, self->next_char_ptr))
    return NULL;

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
    return NULL;
  ptr = (char *)ival;
  if (!is_valid_ptr(self, ptr))
    return NULL;
  self->next_char_ptr = (char *)ptr;

  Py_INCREF(Py_None);
  return Py_None;
}

static PyObject *
lexer_state_get_match_text(PyObject *arg_self, PyObject *args)
{
  lexer_state_t *self;
  PyObject *str;
  size_t n;

  assert(arg_self->ob_type == &lexer_state_type);
  self = (lexer_state_t *)arg_self;
  if (!is_valid_ptr(self, self->next_char_ptr))
    return NULL;
  if (!is_valid_ptr(self, self->start_of_token))
    return NULL;

  n = self->next_char_ptr - self->start_of_token;
  assert (n > 0);

 str = PyString_FromStringAndSize(self->start_of_token, n);
 return str;
}

static PyObject *
lexer_state_set_input(PyObject *arg_self, PyObject *args)
{
  PyObject *obj;
  lexer_state_t *self;
  const char *tmp_buf;
  int i, tmp_buf_len;

  assert(arg_self->ob_type == &lexer_state_type);
  self = (lexer_state_t *)arg_self;
  if (!PyArg_ParseTuple(args, "O:set_input", &obj))
    return NULL;

  if (PyString_Check(obj)) {
    tmp_buf_len = PyString_Size(obj);
    tmp_buf = PyString_AsString(obj);

    if (self->buf)
      free(self->buf);

    self->buf            = malloc(tmp_buf_len + 2);
    self->next_char_ptr  = self->buf;
    self->start_of_token = 0;
    self->size_of_buf    = tmp_buf_len + 2;
    self->chars_in_buf   = tmp_buf_len + 2;
    
    for (i=0; i<tmp_buf_len; i++)
      self->buf[i] = tmp_buf[i];
    self->buf[tmp_buf_len]     = '\0';
    self->buf[tmp_buf_len + 1] = '\0';
  }
  else if (PyFile_Check(obj)) {
    size_t n_read;
    FILE *fp;

    fp = PyFile_AsFile(obj);
    if (self->buf)
      free(self->buf);
    self->buf            = malloc(4096 + 2);
    self->next_char_ptr  = self->buf;
    self->start_of_token = 0;
    self->size_of_buf    = 4096 + 2;
    n_read = fread(self->buf, 1, 4096, fp);
    self->chars_in_buf   = n_read + 2;
    self->buf[n_read] = '\0';
    self->buf[n_read + 1] = '\0';

    self->fill_obj = obj;
    Py_INCREF(obj);
  }
  else {
    PyErr_Format(PyExc_RuntimeError, "lexer_state set_input() method called "
		 "with object not of type file or string. Stopping.");
    return NULL;
  }

  Py_INCREF(Py_None);
  return Py_None;
}

static int
lexer_state_resize_buffer(lexer_state_t *self, int new_size)
{
  char *new_buf;
  int n_remaining;

  new_buf = malloc(new_size + 2);
  if (new_buf == 0)
    return 0;

  n_remaining = self->chars_in_buf - (self->start_of_token - self->buf);
  memcpy(new_buf, self->start_of_token, n_remaining);

  self->next_char_ptr = new_buf + (self->next_char_ptr - self->buf);
  self->start_of_token = new_buf;
  self->size_of_buf = new_size;
  self->chars_in_buf = n_remaining;

  free(self->buf);
  self->buf = new_buf;

  return 1;
}

static PyObject *
lexer_state_set_fill_method(PyObject *arg_self, PyObject *args)
{
  lexer_state_t *self;
  PyObject *fill_obj;

  assert(arg_self->ob_type == &lexer_state_type);
  self = (lexer_state_t *)arg_self;
  if (!PyArg_ParseTuple(args, "O:set_fill_method", &fill_obj))
    return NULL;
  if ( PyCallable_Check(fill_obj) != 1 && PyFile_Check(fill_obj) != 1) {
    PyErr_Format(PyExc_RuntimeError, "Fill method is not callable "
		 "and not a file.");
    return NULL;
  }

  if (self->fill_obj != 0) {
    Py_DECREF(self->fill_obj);
  }
  self->fill_obj = fill_obj;
  Py_INCREF(fill_obj);

  Py_INCREF(Py_None);
  return Py_None;
}

static PyObject *
lexer_state_get_all_state(PyObject *arg_self, PyObject *args)
{
  lexer_state_t *self;
  PyObject *result;

  assert(arg_self->ob_type == &lexer_state_type);
  self = (lexer_state_t *)arg_self;
  result = Py_BuildValue("(iiiiii)",
			 (int)self, (int)self->buf,
			 (int)self->start_of_token, (int)self->next_char_ptr,
			 self->chars_in_buf, self->size_of_buf);
  return result;
}

static PyObject *
lexer_state_add_to_buffer(PyObject *arg_self, PyObject *args)
{
  lexer_state_t *self;
  PyObject *obj_to_add;
  Py_ssize_t str_len;
  int space_left, new_size, space_needed;
  const char *txt;
  char *dst;

  assert(arg_self->ob_type == &lexer_state_type);
  self = (lexer_state_t *)arg_self;

#if PYTOKEN_DEBUG
  printf("lexer_state_add_to_buffer() -- called - starting\n");
  printf("buf=0x%x start_of_token=0x%x size_of_buf=%d "
	 "n_chars=%d next_char_ptr=0x%x\n",
	 (unsigned int)self->buf, (unsigned int)self->start_of_token,
	 self->size_of_buf, self->chars_in_buf,
	 (unsigned int)self->next_char_ptr);
#endif

  if (!PyArg_ParseTuple(args, "O", &obj_to_add))
    return NULL;

  space_left = self->start_of_token - self->buf;
#if PYTOKEN_DEBUG
  printf("lexer_state_add_to_buffer() -- %d bytes left\n", space_left);
#endif

  if ( ! PyString_Check(obj_to_add)) {
    PyErr_Format(PyExc_RuntimeError,
		 "add_to_buffer: only string objs can be used.");
    return NULL;
  }

  str_len = PyString_Size(obj_to_add);
  txt = PyString_AsString(obj_to_add);
  if (str_len <= 0) {
    PyErr_Format(PyExc_RuntimeError, "add_to_buffer: received empty string");
    return NULL;
  }

  if (str_len > space_left) {
    space_needed = str_len - space_left;
    new_size = self->size_of_buf + space_needed;
    if ( ! lexer_state_resize_buffer(self, new_size) ) {
      PyErr_Format(PyExc_RuntimeError, "add_to_buffer: resize failed");
      return NULL;
    }
  }
    
  dst = self->buf + self->chars_in_buf - 2;
  memcpy(dst, txt, str_len);

  self->chars_in_buf += str_len;
  self->buf[ self->chars_in_buf - 1] = '\0';
  self->buf[ self->chars_in_buf ] = '\0';

#if PYTOKEN_DEBUG
  printf("buf=0x%x start_of_token=0x%x size_of_buf=%d "
	 "n_chars=%d next_char_ptr=0x%x\n",
	 (unsigned int)self->buf, (unsigned int)self->start_of_token,
	 self->size_of_buf, self->chars_in_buf,
	 (unsigned int)self->next_char_ptr);
#endif

  Py_INCREF(Py_None);
  return Py_None;
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
    return NULL;
  ptr = lexer_state_get_char_ptr(obj_arg);
  if (ptr == 0)
    return NULL;
  if (!is_valid_ptr(self, ptr))
    return NULL;
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
    return NULL;
  ptr = lexer_state_get_word_ptr(obj_arg);
  if (ptr == 0)
    return NULL;
  if (!is_valid_word_ptr(self, ptr))
    return NULL;
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
    return NULL;
  dst_ptr = lexer_state_get_char_ptr(obj_arg);
  if (dst_ptr==0)
    return NULL;
  if (!is_valid_ptr(self, dst_ptr))
    return NULL;

  if (val<0 || val > 0xFF) {
    PyErr_Format(PyExc_RuntimeError, "val out of range to store in byte");
    return NULL;
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
    return NULL;
  dst_ptr = lexer_state_get_word_ptr(obj_arg);
  if (dst_ptr == 0)
    return NULL;
  if (!is_valid_word_ptr(self, dst_ptr))
    return NULL;
  
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
  return NULL;
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
  return NULL;
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

#if PYTOKEN_DEBUG
static void
lexer_state_print_buf(lexer_state_t *self, int n_to_print)
{
  int i, lim, remain;
  char ch;

  printf("lexer_state=0x%x buf=0x%x next_char=0x%x token_start=0x%x "
	 "size=%d n_in_buf=%d\n",
	 (unsigned int)self, (unsigned int)self->buf,
	 (unsigned int)self->next_char_ptr, (unsigned int)self->start_of_token,
	 self->size_of_buf, self->chars_in_buf);

  if (n_to_print > self->chars_in_buf)
    lim = self->chars_in_buf;
  else
    lim = n_to_print;

  printf("lexer buf:");
  for (i=0; i < lim; i++) {
    ch = self->buf[i];
    if (ch > ' ' && ch <= '~')
      printf("%c", ch);
    else
      printf("<%02x>", (unsigned int)ch);
  }
  printf("\n");

  remain = self->chars_in_buf - (self->start_of_token - self->buf);
  if (n_to_print > remain)
    lim = remain;
  else
    lim = n_to_print;
  printf("lexer token_start::");
  for (i=0; i < lim; i++) {
    ch = self->start_of_token[i];
    if (ch > ' ' && ch <= '~')
      printf("%c", ch);
    else
      printf("<%02x>", (unsigned int)ch);
  }
  printf("\n");
}
#endif

static PyObject *
lexer_state_repr(PyObject *self)
{
  lexer_state_t *ptr;
  PyObject *result;

  ptr = (lexer_state_t *)self;
  result = PyString_FromFormat("<lexer_state buf=0x%x next_char=0x%x "
			       "tok_start=0x%x fill=0x%x size_of_buf=%d "
			       "chars_in_buf=%d>",
			       (unsigned int)ptr->buf,
			       (unsigned int)ptr->next_char_ptr,
			       (unsigned int)ptr->start_of_token,
			       (unsigned int)ptr->fill_obj,
			       ptr->size_of_buf, ptr->chars_in_buf);
  return result;
}

static PyObject *
lexer_state_str(PyObject *self)
{
  PyObject *result;

  result = lexer_state_repr(self);
  return result;
}

/*******************************************/
/*                                         */
/* simple obj to allow easy python         */
/* manipulation of unsigned 32 bit objs    */
/*                                         */
/*******************************************/
typedef struct {
  PyObject_HEAD
  uint32_t     val;
} uval32_t;

static PyTypeObject uval32_type = {
  PyObject_HEAD_INIT(NULL)
};

static PyMethodDef uval32_methods[] = {
  {"get_string", (PyCFunction)uval32_get_str, METH_NOARGS,
   "Return uval32 as string."},

  {NULL}
};

static int
uval32_init(PyObject *arg_self, PyObject *args, PyObject *kwds)
{
  uval32_t *self;
  unsigned int val;

#if 0
  printf("calling uval32_init\n");
#endif

  if (!PyArg_ParseTuple(args, "I:uval32", &val)) {
    printf("unable to get an integer\n");
    return 1;
  }

  assert(arg_self->ob_type == &uval32_type);
  self = (uval32_t *)arg_self;
  self->val = (uint32_t)val;

#if 0
  {
    printf("creating uval32 obj val=%d (%x) \n", val, (unsigned int)val);
    printf("uint32 val = %u\n", (unsigned int)self->val);
  }
#endif

  return 0;
}

static void
uval32_dealloc(PyObject *arg_self)
{
  uval32_t *self;

  assert(arg_self->ob_type == &uval32_type);
  self = (uval32_t *)arg_self;
  self->val = 0;
  arg_self->ob_type->tp_free(arg_self);
}

static PyObject *
uval32_repr(PyObject *self)
{
  uval32_t *ptr;
  PyObject *result;

  ptr = (uval32_t *)self;
  result = PyString_FromFormat("<uval32=0x%x>", (unsigned int)ptr->val);
  return result;
}

static PyObject *
uval32_str(PyObject *self)
{
  uval32_t *ptr;
  PyObject *result;

  ptr = (uval32_t *)self;
  result = PyString_FromFormat("0x%x", (unsigned int)ptr->val);
#if 0
  {
    char *txt;

    txt = PyString_AsString(result);
    printf("uval32 string=>%s\n", txt);
  }
#endif
  return result;
}

static PyObject *
uval32_get_str(PyObject *self, PyObject *args)
{
  Py_INCREF(Py_None);
  return Py_None;
}

/***************************************************************/
/***************************************************************/
/***                                                         ***/
/*** the actual code objects - supports vcode - or actual    ***/
/*** machine code. vcode is designed to be interpreted by    ***/
/*** the python simulator function in pytoken.py             ***/
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
static PyObject *code_set_bytes(PyObject *, PyObject *);
static PyObject *code_get_start_addr(PyObject *, PyObject *);
static PyObject *code_get_code(PyObject *, PyObject *);

static PyObject *code_set_buf2(PyObject *, PyObject *);
static PyObject *code_get_token2(PyObject *, PyObject *);

static PyObject *code_get_fill_caller_addr(PyObject *, PyObject *);
static int code_call_lexer_state_fill_func(lexer_state_t *self);

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

  lexer_state_t *lstate;
} code_t;

static int code_grow(code_t *);
static int code_set_size(code_t *, size_t new_size);

static PyTypeObject code_type = {
  PyObject_HEAD_INIT(NULL)
};

static PyMethodDef code_methods[] = {
    {"get_token", (PyCFunction)code_get_token, METH_KEYWORDS,
     "Return the next token."},

    {"set_buf2", code_set_buf2, METH_VARARGS,
     "Set the buffer to be used with the get_token2() function."},

    {"get_token2", code_get_token2, METH_NOARGS,
     "Call a machine code get token function with a preset buffer."},

    {"set_type",  code_set_type,  METH_VARARGS,
     "Set type of code object to 'vcode' or 'mcode'."},

    {"append",    code_append,    METH_VARARGS,
     "Append a single chunk of data."},

    {"set_bytes", code_set_bytes, METH_VARARGS,
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
  self->size_of_buf   = 0;
  self->is_vcode      = 0;
  self->obj_size      = 1;
  self->u.buf         = 0;

  return 0;
}

static void
code_dealloc(PyObject *arg_self)
{
  code_t *self;
  int i, err_code;

  assert(arg_self->ob_type == &code_type);
  self = (code_t *)arg_self;

  if (self->is_vcode) {
    for (i=0; i<self->num_in_buf; i++)
      Py_DECREF(self->u.obuf[i]);
    free(self->u.obuf);
    self->u.obuf = 0;
  }
  else {
    err_code = munmap(self->u.buf, self->size_of_buf);
    assert (err_code == 0); /* how should a failure be handled ? */
  }

  self->num_in_buf    = 0;
  self->size_of_buf   = 0;
  self->obj_size      = 0;
  self->u.buf         = 0;

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
    return NULL;
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

  assert(arg_self->ob_type == &code_type);
  code_obj_ptr = (code_t *)arg_self;
  
  debug_flag = 0;
  if (!PyArg_ParseTupleAndKeywords(args, kwdict, "O!|i:get_token", kwlist,
				   &lexer_state_type, &lbuf, &debug_flag))
    return NULL;

  if (code_obj_ptr->is_vcode) {
    bool_db_flag = PyBool_FromLong(debug_flag);

    m = PyImport_ImportModule("pytoken");
    if (m==0)
      return NULL;
    d = PyModule_GetDict(m);
    Py_DECREF(m);
    if (d==0)
      return NULL;
    func = PyDict_GetItemString(d, "run_vcode_simulation");
    if (func == 0)
      return NULL;
    if (!PyFunction_Check(func)) {
      PyErr_Format(PyExc_RuntimeError, "run_vcode_simulation not a function");
      return NULL;
    }
    res = PyObject_CallFunctionObjArgs(func, arg_self, lbuf, bool_db_flag, 0);
    return res;
  }

  asm_func = (asm_func_t)(code_obj_ptr->u.buf);
  v = (*asm_func)(code_obj_ptr, (lexer_state_t*)lbuf);
  res = PyInt_FromLong(v);
  return res;
}

static PyObject *
code_set_buf2(PyObject *arg_self, PyObject *args)
{
  code_t *self;
  lexer_state_t *lbuf;

  assert(arg_self->ob_type == &code_type);
  self = (code_t *)arg_self;

  if (!PyArg_ParseTuple(args, "O!:", &lexer_state_type, &lbuf))
    return NULL;

  self->lstate = lbuf;

  Py_INCREF(Py_None);
  return Py_None;
}

static PyObject *
code_get_token2(PyObject *arg_self, PyObject *args)
{
  code_t *code_obj_ptr;
  typedef int (*asm_func_t)(code_t *, lexer_state_t *);
  asm_func_t asm_func;
  int v;
  PyObject *res;

  assert(arg_self->ob_type == &code_type);
  code_obj_ptr = (code_t *)arg_self;
  asm_func = (asm_func_t)(code_obj_ptr->u.buf);
  v = (*asm_func)(code_obj_ptr, code_obj_ptr->lstate);
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
    return NULL;
  }
  if (!PyArg_ParseTuple(args, "s:set_type", &type_name))
    return NULL;

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
    return NULL;
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
      return NULL;
    if (!PyTuple_Check(tup)) {
      PyErr_Format(PyExc_RuntimeError, "vcode code objects can only "
		   "append tuples.");
      return NULL;
    }

    if (self->num_in_buf == self->size_of_buf)
      if ( ! code_grow(self))
	return NULL;

    Py_INCREF(tup);
    self->u.obuf[ self->num_in_buf ] = tup;
    self->num_in_buf++;

    Py_INCREF(Py_None);
    return Py_None;
  }

  if (!PyArg_ParseTuple(args, "i:append", &ival))
    return NULL;

  if (self->num_in_buf == self->size_of_buf)
    if ( ! code_grow(self))
      return NULL;

  self->u.buf[ self->num_in_buf ] = (char)(ival & 0xFF);
  self->num_in_buf++;

  Py_INCREF(Py_None);
  return Py_None;
}

static PyObject *
code_set_bytes(PyObject *arg_self, PyObject *args)
{
  code_t *self;
  const char *sbuf;
  int i, slen;
  size_t page_size, desired_size;

  assert(arg_self->ob_type == &code_type);
  self = (code_t *)arg_self;
  assert(self->is_vcode == 0);

  if (!PyArg_ParseTuple(args, "s#:set_bytes", &sbuf, &slen))
    return NULL;

  page_size = sysconf(_SC_PAGESIZE);
  desired_size = page_size;
  while (desired_size < slen)
    desired_size = desired_size * 2;

  if (code_set_size(self, desired_size) != 1)
    return NULL;

  for (i=0; i<slen; i++)
    self->u.buf[i] = sbuf[i];
  self->num_in_buf = slen;

  Py_INCREF(Py_None);
  return Py_None;
}

static int
code_grow(code_t *self)
{
  char *tmp, msg[200];
  int err_code;

  if (self->is_vcode) {
    if (self->size_of_buf == 0) {
      self->size_of_buf = 1024;
      self->u.buf = malloc (self->size_of_buf * self->obj_size);
      if (self->u.buf == 0)
	{
	  PyErr_Format(PyExc_RuntimeError, "Unable to allocate memory");
	  return 0;
	}
      return 1;
    }
    self->size_of_buf = 2 * self->size_of_buf;
    self->u.buf         = realloc(self->u.buf,
				  self->size_of_buf * self->obj_size);
    if (self->u.buf == 0)
      {
	PyErr_Format(PyExc_RuntimeError, "Unable to allocate memory");
	return 0;
      }
    return 1;
  }

  if (self->size_of_buf == 0) {
    self->size_of_buf = sysconf(_SC_PAGESIZE);
    self->u.buf = mmap(0, self->size_of_buf,
		       PROT_READ | PROT_WRITE | PROT_EXEC,
		       MAP_PRIVATE | MAP_ANONYMOUS,
		       -1, 0);
    if (self->u.buf == MAP_FAILED) {
      msg[0] = '\0';
      strerror_r(errno, msg, sizeof(msg));
      PyErr_Format(PyExc_RuntimeError, "Could not mmap anonymous buffer: %d",
		   errno);
      return 0;
    }
    return 1;
  }

  self->size_of_buf = 2 * self->size_of_buf;
  tmp = mmap (0, self->size_of_buf, PROT_READ | PROT_WRITE | PROT_EXEC,
	      MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
  if (tmp == MAP_FAILED) {
      PyErr_Format(PyExc_RuntimeError, "Could not mmap anonymous 2nd buffer");
      return 0;
    }
    
  memcpy (tmp, self->u.buf, self->num_in_buf);
  err_code = munmap (self->u.buf, self->size_of_buf);
  if (err_code != 0) {
      PyErr_Format(PyExc_RuntimeError, "Could not munmap anonymous buffer");
      return 0;
    }

  self->u.buf = tmp;

  return 1;
}

static int
code_set_size(code_t *self, size_t new_size)
{
  int err_code;

  if (self->is_vcode) {
    PyErr_Format(PyExc_RuntimeError, "Cannot use code_set_size on vcode.");
    return 0;
  }

  if (self->size_of_buf != 0) {
    assert(self->u.buf != 0);
    err_code = munmap(self->u.buf, self->size_of_buf);
    if (err_code != 0) {
      PyErr_Format(PyExc_RuntimeError, "Unable to munmap code buffer.");
      return 0;
    }
  }

  self->u.buf = mmap(0, new_size, PROT_READ | PROT_WRITE | PROT_EXEC,
		     MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
  if (self->u.buf == 0 || self->u.buf == (void *)-1) {
    PyErr_Format(PyExc_RuntimeError, "Unable to mmap code buffer");
    return 0;
  }

  self->size_of_buf = new_size;
  return 1;
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

  addr = (long)&code_call_lexer_state_fill_func;
  result = PyInt_FromLong(addr);
  return result;
}

static int
code_call_lexer_state_fill_func(lexer_state_t *lstate)
{
  PyObject *fill_status, *arg_list;
  long n1, n2, s1, s2, n_avail, new_size, shift_amt, to_move;
  int res;

  /* return val:               */
  /* 1 = got more data         */
  /* 2 = no more data avail    */
  /* 3 = something went wrong  */

#if PYTOKEN_DEBUG
  printf("Doing fill\n");
#endif

  if (lstate == 0) {
    PyErr_Format(PyExc_RuntimeError, "null lexer state sent to fill runtime");
    return 3;
  }
  if (lstate->fill_obj == 0)
    return 2;

  n1 = lstate->chars_in_buf - (lstate->next_char_ptr - lstate->buf - 1);

  if (PyFile_Check(lstate->fill_obj)) {
    size_t n_read;
    FILE *fp;

#if PYTOKEN_DEBUG
    printf("  doing file fill\n");
    lexer_state_print_buf(lstate, 60);
#endif
    fp = PyFile_AsFile(lstate->fill_obj);
    assert(fp != 0);

    s1 = lstate->start_of_token - lstate->buf;
    s2 = lstate->size_of_buf - lstate->chars_in_buf;
    n_avail = s1 + s2;
    if (n_avail == 0) {
      new_size = lstate->size_of_buf * 2;
      if ( ! lexer_state_resize_buffer(lstate, new_size)) {
#if PYTOKEN_DEBUG
	printf("file fill unable to resize, newsize=%ld\n", new_size);
#endif
	return 3;
      }
      s1 = lstate->start_of_token - lstate->buf;
      s2 = lstate->size_of_buf - lstate->chars_in_buf;
      n_avail = s1 + s2;
    }
    else {
      shift_amt = lstate->start_of_token - lstate->buf;
      to_move = lstate->chars_in_buf - shift_amt;
      memmove(lstate->buf, lstate->start_of_token, to_move - 2);

      lstate->start_of_token -= shift_amt;
      lstate->next_char_ptr  -= shift_amt;
      lstate->chars_in_buf   -= shift_amt;
    }

    n_read = fread(lstate->next_char_ptr, 1, n_avail, fp);
    lstate->next_char_ptr[n_read] = '\0';
    lstate->next_char_ptr[n_read + 1] = '\0';

    lstate->chars_in_buf += n_read;

    if (n_read == 0)
      res = 2;
    else
      res = 1;
#if PYTOKEN_DEBUG
    lexer_state_print_buf(lstate, 60);
    printf("at end of file fill result=%d\n\n", res);
#endif
    return res;
  }
  else {
    assert(PyCallable_Check(lstate->fill_obj));
    arg_list = Py_BuildValue("(O)", lstate);
    if (arg_list == 0)
      return 3;

    fill_status = PyObject_Call(lstate->fill_obj, arg_list, 0);
    if (fill_status == 0)
      return 3;

    Py_DECREF(fill_status);

    n2 = lstate->chars_in_buf - (lstate->next_char_ptr - lstate->buf - 1);
    if (n2 > n1)
      return 1;
    return 2;
  }
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
    return NULL;
  if (strcmp(func_name, "PyObject_CallMethod")==0)
    func_ptr = &PyObject_CallMethod;
  else {
    PyErr_SetString(PyExc_RuntimeError, "Unknown function name");
    return NULL;
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
    return NULL;
  result = PyString_FromStringAndSize(ptr, n_bytes);
  return result;
}

void
escape_stop_here()
{
  escape_stop_here_counter++;
  return;
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
    return NULL;
  lval = llval;
  obj = (PyObject *)lval;
  if (obj->ob_type != &lexer_state_type) {
    PyErr_SetString(PyExc_RuntimeError, "Bad id - not lex_state obj.");
    return NULL;
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
escape_get_token_start_offset(PyObject *self, PyObject *args)
{
  lexer_state_t lstate;
  char *p1, *p2;
  int offset;
  PyObject *result;
  
  p1 = (char *)&lstate;
  p2 = (char *)&lstate.start_of_token;
  offset = p2 - p1;
  result = PyInt_FromLong(offset);
  return result;
}

static PyObject *
escape_get_fill_caller_addr(PyObject *self, PyObject *args)
{
  long addr;
  PyObject *r;

  addr = (long)&code_call_lexer_state_fill_func;
  r = PyInt_FromLong(addr);
  return r;
}

static PyObject *
escape_do_serialize(PyObject *self, PyObject *args)
{
  int op, reg[4];

  op = 0;
  asm volatile("pushl %%ebx      \n\t" /* save %ebx */
	       "cpuid            \n\t"
	       "movl %%ebx, %1   \n\t" /* save what cpuid just put in %ebx */
	       "popl %%ebx       \n\t" /* restore the old %ebx */
	       : "=a"(reg[0]), "=r"(reg[1]), "=c"(reg[2]), "=d"(reg[3])
	       : "a"(op)
	       : "cc");

  Py_INCREF(Py_None);
  return Py_None;
}

static PyObject *
escape_regtest01(PyObject *self, PyObject *args)
{
  PyObject *lbuf, *result;

  if (!PyArg_ParseTuple(args, "O!:", &lexer_state_type, &lbuf))
    return NULL;
  result = PyObject_CallMethod(lbuf, "get_cur_addr", 0);
  return result;
}

/****************************************************************/
/* table based dfa                                              */
/****************************************************************/
#define DFATABLE_N_ENTRIES_PER_STATE 256

typedef struct {
  PyObject_HEAD

  Py_ssize_t     n_states;
  Py_ssize_t    *states;
} dfatable_t;

static PyTypeObject dfatable_type = {
  PyObject_HEAD_INIT(NULL)
};

static PyObject *dfatable_set_num_states(PyObject *, PyObject *);
static PyObject *dfatable_get_num_states(PyObject *, PyObject *);
static PyObject *dfatable_set_state(PyObject *, PyObject *);
static PyObject *dfatable_get_state(PyObject *, PyObject *);

static PyMethodDef dfatable_methods[] = {
  {"set_num_states", dfatable_set_num_states, METH_VARARGS,
   PyDoc_STR("Set num states for a table based DFA.")},  

  {"get_num_states", dfatable_get_num_states, METH_NOARGS,
   PyDoc_STR("Get num states for a table based DFA.")},  

  {"set_state", dfatable_set_state, METH_VARARGS,
   PyDoc_STR("set_state(state_num, [next_state_num * 256])"
	     "Any sequence type can be passed as the second argument,"
	     "it must have length of exactly 256. Each entry of the"
	     "sequence must be a state number or None. These are the"
	     "out edges from this state.")},

  {"get_state", dfatable_get_state, METH_VARARGS,
   PyDoc_STR("get_state(state_num) returns a tuple of next state items."
	     " If an item is None then that char has no next state. "
	     "Otherwise the item will be a state number.")},

  {NULL, NULL, 0, NULL}
};

static void
dfatable_dealloc(PyObject *arg_self)
{
  dfatable_t *self;

  assert(arg_self->ob_type == &dfatable_type);
  self = (dfatable_t *)arg_self;

  if (self->states)
    free(self->states);
  self->n_states = 0;
  self->states = NULL;

  return;
}

static int
dfatable_init(PyObject *arg_self, PyObject *args, PyObject *kwds)
{
  dfatable_t *self;

  assert(arg_self->ob_type == &dfatable_type);
  self = (dfatable_t *)arg_self;

  self->n_states = 0;
  self->states = NULL;

  return 0;
}

static PyObject *
dfatable_set_num_states(PyObject *arg_self, PyObject *args)
{
  dfatable_t *self;
  Py_ssize_t n_states, n_bytes;

  assert(arg_self->ob_type == &dfatable_type);
  self = (dfatable_t *)arg_self;
  
  if (!PyArg_ParseTuple(args, "n:set_num_states", &n_states))
    return NULL;

  if (n_states <= 0) {
    PyErr_Format(PyExc_RuntimeError, "set_num_states: out of range");
    return NULL;
  }

  if (self->n_states != 0) {
    free(self->states);
    self->states = NULL;
    self->n_states = 0;
  }

  self->n_states = n_states;

  n_bytes = self->n_states
    * DFATABLE_N_ENTRIES_PER_STATE
    * sizeof(Py_ssize_t);

  self->states = calloc(1, n_bytes);

  if (self->states == NULL) {
    PyErr_Format(PyExc_RuntimeError, "out of memory");
    return NULL;
  }

  Py_INCREF(Py_None);
  return Py_None;
}

static PyObject *
dfatable_get_num_states(PyObject *arg_self, PyObject *args)
{
  dfatable_t *self;
  PyObject *result;

  assert(arg_self->ob_type == &dfatable_type);
  self = (dfatable_t *)arg_self;
  
  if (self->states == NULL) {
    Py_INCREF(Py_None);
    return Py_None;
  }
    
  result = PyLong_FromSsize_t(self->n_states);
  return result;
}

static PyObject *
dfatable_set_state(PyObject *arg_self, PyObject *args)
{
  dfatable_t *self;
  Py_ssize_t snum, *sptr, i, ssval;
  PyObject *seq, *next;
  long lval;

  assert(arg_self->ob_type == &dfatable_type);
  self = (dfatable_t *)arg_self;
  
  if (!PyArg_ParseTuple(args, "nO:set_state", &snum, &seq))
    return NULL;
  if (!PySequence_Check(seq)) {
    PyErr_Format(PyExc_RuntimeError, "set_state: second arg must be a seq.");
    return NULL;
  }
  if (PySequence_Length(seq) != DFATABLE_N_ENTRIES_PER_STATE) {
    PyErr_Format(PyExc_RuntimeError, "set_state: Got seq of length %d "
		 "expecting %d", (int)PySequence_Length(seq),
		 DFATABLE_N_ENTRIES_PER_STATE);
    return NULL;
  }
  if (snum < 0 || snum >= self->n_states) {
    PyErr_Format(PyExc_RuntimeError, "set_state: state num out of range");
    return NULL;
  }

  sptr = &self->states[snum * DFATABLE_N_ENTRIES_PER_STATE];
  for (i = 0; i < DFATABLE_N_ENTRIES_PER_STATE; i++) {
    next = PySequence_GetItem(seq, i);

    if (next == Py_None) {
      sptr[i] = -1;
      Py_DECREF(next);
      continue;
    }

    if (PyInt_CheckExact(next)) {
      lval = PyInt_AS_LONG(next);
      if (lval < 0 || lval > self->n_states) {
	PyErr_Format(PyExc_RuntimeError, "set_state: Failed to set state "
		     "%d at position %d: next state out of range",
		     (int)snum, i);
	return NULL;
      }
      sptr[i] = lval;
      Py_DECREF(next);
      continue;
    }


    if (PyLong_CheckExact(next)) {
      ssval = PyLong_AsSsize_t(next);
      if (ssval == -1 && PyErr_Occurred() != NULL) {
	return NULL;
      }
      if (ssval < 0 || ssval > self->n_states) {
	PyErr_Format(PyExc_RuntimeError, "set_state: Failed to set state "
		     "%d at position %d: next state out of range",
		     (int)snum, i);
	return NULL;
      }
      sptr[i] = ssval;
      Py_DECREF(next);
      continue;
    }

    Py_DECREF(next);
    PyErr_Format(PyExc_RuntimeError, "set_state: Failed to set state "
		     "%d at position %d: next state not int or long",
		     (int)snum, i);
    return NULL;
  }

  Py_INCREF(Py_None);
  return Py_None;
}

static PyObject *
dfatable_get_state(PyObject *arg_self, PyObject *args)
{
  dfatable_t *self;
  Py_ssize_t snum, next, *sptr;
  PyObject *result, *item;
  int i;

  assert(arg_self->ob_type == &dfatable_type);
  self = (dfatable_t *)arg_self;
  
  if (!PyArg_ParseTuple(args, "n:get_state", &snum))
    return NULL;
  if (snum < 0 || snum >= self->n_states) {
    PyErr_Format(PyExc_RuntimeError, "set_state: state num out of range");
    return NULL;
  }

  result = PyTuple_New(DFATABLE_N_ENTRIES_PER_STATE);
  if (result == NULL)
    return NULL;

  sptr = &self->states[snum * DFATABLE_N_ENTRIES_PER_STATE];
  for (i = 0; i < DFATABLE_N_ENTRIES_PER_STATE; i++) {
    next = sptr[i];
    if (next == -1) {
      Py_INCREF(Py_None);
      item = Py_None;
    }
    else {
      item = PyLong_FromSsize_t(next);
      if (item == NULL)
	return NULL;
    }
    if (PyTuple_SetItem(result, i, item) != 0)
      return NULL;
  }

  return result;
}

/****************************************************************/
/* top level                                                    */
/****************************************************************/
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
  {"get_token_start_offset", escape_get_token_start_offset, METH_NOARGS,
   PyDoc_STR("Return lex state offset for character pos ptr.")},

  {"get_fill_caller_addr", escape_get_fill_caller_addr, METH_NOARGS,
   PyDoc_STR("Get address of code_call_fill_ptr function.")},

  {"do_serialize", escape_do_serialize, METH_NOARGS,
   PyDoc_STR("Execute an x86 serializing instruction."
	     "Forces cache flushes to allow code written as data to be"
	     "loaded as instructions.")},

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
  lexer_state_type.tp_repr        = lexer_state_repr;
  lexer_state_type.tp_str         = lexer_state_str;
  code = PyType_Ready(&lexer_state_type);
  if (code < 0)
    return;
  Py_INCREF(&lexer_state_type);
  code = PyModule_AddObject(m, "lexer_state", (PyObject *)&lexer_state_type);
  if (code < 0)
    return;

  /****************************/
  /* uval32                   */
  /****************************/
  uval32_type.tp_name             = "escape.uval32";
  uval32_type.tp_basicsize        = sizeof(uval32_t);
  uval32_type.tp_new              = PyType_GenericNew;
  uval32_type.tp_dealloc          = uval32_dealloc;
  uval32_type.tp_methods          = uval32_methods;
  uval32_type.tp_flags            = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE;
  uval32_type.tp_doc              = "Simple unsigned 32 bit quantity.";
  uval32_type.tp_init             = uval32_init;
  uval32_type.tp_repr             = uval32_repr;
  uval32_type.tp_str              = uval32_str;
  code = PyType_Ready(&uval32_type);
  if (code < 0)
    return;
  Py_INCREF(&uval32_type);
  code = PyModule_AddObject(m, "uval32", (PyObject *)&uval32_type);
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

  /****************************/
  /* table based dfas         */
  /****************************/
  dfatable_type.tp_name        = "escape.dfatable";
  dfatable_type.tp_basicsize   = sizeof(dfatable_t);
  dfatable_type.tp_new         = PyType_GenericNew;
  dfatable_type.tp_dealloc     = dfatable_dealloc;
  dfatable_type.tp_methods     = dfatable_methods;
  dfatable_type.tp_flags       = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE;
  dfatable_type.tp_doc         = "Table based DFA.";
  dfatable_type.tp_init        = dfatable_init;

  code = PyType_Ready(&dfatable_type);
  if (code < 0)
    return;

  Py_INCREF(&dfatable_type);
  code = PyModule_AddObject(m, "dfatable", (PyObject *)&dfatable_type);
  if (code < 0)
    return;


  return;
}
