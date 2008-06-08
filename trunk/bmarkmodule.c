/*

Copyright (c) 2008, Ram Bhamidipaty
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
#include <limits.h>

extern int bmarklex(void);
extern void *bmark_scan_string(const char *);

static void *cur_buf;

static PyObject *
bmark_set_buffer(PyObject *self, PyObject *args)
{
  char *buf;

  if (!PyArg_ParseTuple(args, "s:set_buffer", &buf))
    return 0;

  cur_buf = bmark_scan_string(buf);
  Py_INCREF(Py_None);
  return Py_None;
}

static PyObject *
bmark_get_token(PyObject *self, PyObject *args)
{
  int tok;
  PyObject *result;

  tok = bmarklex();
  result = PyInt_FromLong(tok);
  return result;
}

static PyMethodDef bmark_methods[] = {
  {"set_buffer",  bmark_set_buffer,     METH_VARARGS, 0},
  {"get_token",   bmark_get_token,      METH_VARARGS, 0},
  {NULL,     NULL}
};

PyMODINIT_FUNC
initbmark(void)
{
  (void)Py_InitModule("bmark", bmark_methods);
  return;
}
