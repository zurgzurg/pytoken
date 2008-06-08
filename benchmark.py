#!/usr/bin/env python
########################################################
##
## Copyright (c) 2008, Ram Bhamidipaty
## All rights reserved.
## 
## Redistribution and use in source and binary forms, with or without
## modification, are permitted provided that the following conditions are
## met:
## 
##     * Redistributions of source code must retain the above
##       copyright notice, this list of conditions and the
##       following disclaimer.
## 
##     * Redistributions in binary form must reproduce the above
##       copyright notice, this list of conditions and the following
##       disclaimer in the documentation and/or other materials
##       provided with the distribution.
## 
##     * Neither the name of Ram Bhamidipaty nor the names of its
##       contributors may be used to endorse or promote products
##       derived from this software without specific prior written permission.
## 
## THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
## "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
## LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
## A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
## OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
## SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
## LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
## DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
## THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
## (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
## OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
## 
########################################################
import os
import sys
import time

sys.path.append("./build/lib.linux-i686-2.5")
import bmark
import pytoken


######################################################
##
## flex based
##
######################################################
def t01_flex_setup():
    global n_toks
    txt = "foo bar " * n_toks
    bmark.set_buffer(txt)
    return

def t01_test_flex():
    global n_toks
    c1 = time.clock()
    for i in xrange(n_toks):
        tok = bmark.get_token()
        assert tok == 2
        tok = bmark.get_token()
        assert tok == 3
    c2 = time.clock()
    return c2 - c1

######################################################
##
## richer pytoken interface
##
######################################################
def t01_pytoken_setup():
    global py_tok_buf
    global scanner_obj
    global n_toks

    scanner_obj = pytoken.lexer()
    scanner_obj.add_pattern("foo", 2)
    scanner_obj.add_pattern("bar", 3)
    scanner_obj.add_pattern(" ",   4)
    scanner_obj.add_pattern("\n",  5)
    scanner_obj.compile_to_machine_code()

    txt = "foo bar " * n_toks
    py_tok_buf = pytoken.lexer_state()
    py_tok_buf.set_input(txt)

    return

def t01_test_pytoken():
    global n_toks
    global scanner_obj
    global py_tok_buf

    c1 = time.clock()
    for i in xrange(n_toks):
        #print "--->", i

        tok = scanner_obj.code_obj.get_token(py_token_buf)
        tok = scanner_obj.actions[tok]
        #print tok
        assert tok == 2

        tok = scanner_obj.code_obj.get_token(py_token_buf)
        tok = scanner_obj.actions[tok]
        #print tok
        assert tok == 4

        tok = scanner_obj.code_obj.get_token(py_token_buf)
        tok = scanner_obj.actions[tok]
        #print tok
        assert tok == 3

        tok = scanner_obj.code_obj.get_token(py_token_buf)
        tok = scanner_obj.actions[tok]
        #print tok
        assert tok == 4
    c2 = time.clock()
    return c2 - c1

######################################################
##
## minimal pytoken interface
##
######################################################
def t01_pytoken_setup2():
    global py_tok_buf
    global scanner_obj
    global n_toks

    scanner_obj = pytoken.lexer()
    scanner_obj.add_pattern("foo", 2)
    scanner_obj.add_pattern("bar", 3)
    scanner_obj.add_pattern(" ",   None)
    scanner_obj.add_pattern("\n",  None)
    scanner_obj.compile_to_machine_code()

    txt = "foo bar " * n_toks
    py_tok_buf = pytoken.lexer_state()
    py_tok_buf.set_input(txt)

    scanner_obj.code_obj.set_buf2(py_tok_buf)

    return

def t01_test_pytoken2():
    global n_toks
    global scanner_obj
    global py_tok_buf

    c1 = time.clock()
    for i in xrange(n_toks):
        tok = scanner_obj.code_obj.get_token2()
        assert tok == 4
        tok = scanner_obj.code_obj.get_token2()
        assert tok == 5
    c2 = time.clock()
    return c2 - c1

########################################################

py_tok_buf  = None
scanner_obj = None
n_toks      = 1000000

t01_flex_setup()
t1 = t01_test_flex()

t01_pytoken_setup2()
t2 = t01_test_pytoken2()

print "Flex=", t1, "pytoken=", t2

sys.exit(0)
