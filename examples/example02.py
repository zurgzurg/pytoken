#!/usr/bin/env python
########################################################
##
## Author: Ram Bhamidipaty
## 
## I hereby release this code into the public domain.
##
## THIS SOFTWARE IS PROVIDED ``AS IS'' AND WITHOUT ANY EXPRESS OR
## IMPLIED WARRANTIES, INCLUDING, WITHOUT LIMITATION, THE IMPLIED
## WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
## PURPOSE.
## 
## USE IT AT YOUR OWN RISK.
## 
########################################################

##
## Example of using pytoken
##
##
import sys
import os
import pytoken

########################################################
def doit(fname):
    lexer = pytoken.lexer()
    lexer.add_pattern("[0123456789]", 1)
    lexer.add_pattern(" ",  None)
    lexer.add_pattern("\n", None)

    lexer.compile_to_machine_code()

    fp = open(fname, "r")
    lex_buf = pytoken.lexer_state()
    lex_buf.set_input(fp)
    
    n_digits = 0
    while True:
        tok = lexer.get_token(lex_buf)
        if tok == "EOB":
            break
        n_digits += 1

    print "There were", n_digits, "digits in the file."
    return

########################################################
if len(sys.argv) != 2:
    print "Usage: example02 <infile>"
    print ""
    print "Counts the number of digits in the file"
    sys.exit(0)

fname = sys.argv[1]
doit(fname)
