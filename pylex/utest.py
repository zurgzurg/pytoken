#!/usr/bin/env python
import os
import sys
import unittest
import pdb

import pylex

from pylex import PIPE, STAR, CCAT

class lex_test(unittest.TestCase):
    def check_token(self, obj, txt, exp):
        tok = obj.parse(txt)
        self.assert_(tok == exp)
        return
    def check_structure(self, act, exp):
        self.assert_( pylex.struct_equal(act, exp),
                      str(act) + " != " + str(exp))
        return
    pass

class simple01(unittest.TestCase):
    def runTest(self):
        return True
    pass

class simple02(unittest.TestCase):
    def runTest(self):
        obj = pylex.lexer()
        self.assert_(obj is not None)
        return True
    pass

############################################

class simple16(lex_test):
    def runTest(self):
        obj = pylex.lexer()
        info = obj.tokenize_pattern("a")
        self.assert_(type(info) == list)
        self.assert_(len(info)==1 and info[0] == 'a')
        return
    pass

class simple17(lex_test):
    def runTest(self):
        obj = pylex.lexer()
        info = obj.tokenize_pattern("aa")
        self.assert_(type(info) == list)
        self.assert_(len(info)==1 and info[0] == 'aa')
        return
    pass

class simple18(lex_test):
    def runTest(self):
        obj = pylex.lexer()
        info = obj.tokenize_pattern("(aa)")
        self.assert_(info[0] == pylex.LPAREN)
        self.assert_(info[1] == 'aa')
        self.assert_(info[2] == pylex.RPAREN)
        return
    pass

class simple19(lex_test):
    def runTest(self):
        obj = pylex.lexer()
        info = obj.tokenize_pattern("[ab]")
        self.assert_(info[0] == pylex.LBRACKET)
        self.assert_(info[1] == 'ab')
        self.assert_(info[2] == pylex.RBRACKET)
        return
    pass

class simple20(lex_test):
    def runTest(self):
        obj = pylex.lexer()
        info = obj.tokenize_pattern("[abcd]")
        self.assert_(info[0] == pylex.LBRACKET)
        self.assert_(info[1] == 'abcd')
        self.assert_(info[2] == pylex.RBRACKET)
        return
    pass

class simple21(lex_test):
    def runTest(self):
        obj = pylex.lexer()
        info = obj.tokenize_pattern("[abcd]eee")
        self.assert_(info[0] == pylex.LBRACKET)
        self.assert_(info[1] == 'abcd')
        self.assert_(info[2] == pylex.RBRACKET)
        self.assert_(info[3] == 'eee')
        return
    pass

class simple22(lex_test):
    def runTest(self):
        obj = pylex.lexer()
        info = obj.tokenize_pattern("a|b")
        self.assert_(info[0] == 'a')
        self.assert_(info[1] == pylex.PIPE)
        self.assert_(info[2] == 'b')
        return
    pass

class simple23(lex_test):
    def runTest(self):
        obj = pylex.lexer()
        info = obj.tokenize_pattern("(aa)|(bb)")
        self.assert_(info[0] == pylex.LPAREN)
        self.assert_(info[1] == 'aa')
        self.assert_(info[2] == pylex.RPAREN)
        self.assert_(info[3] == pylex.PIPE)
        self.assert_(info[4] == pylex.LPAREN)
        self.assert_(info[5] == 'bb')
        self.assert_(info[6] == pylex.RPAREN)
        return
    pass

class simple24(lex_test):
    def runTest(self):
        obj = pylex.lexer()
        info = obj.tokenize_pattern("((aa)|(bb))")
        self.assert_(info[0] == pylex.LPAREN)
        self.assert_(info[1] == pylex.LPAREN)
        self.assert_(info[2] == 'aa')
        self.assert_(info[3] == pylex.RPAREN)
        self.assert_(info[4] == pylex.PIPE)
        self.assert_(info[5] == pylex.LPAREN)
        self.assert_(info[6] == 'bb')
        self.assert_(info[7] == pylex.RPAREN)
        self.assert_(info[8] == pylex.RPAREN)
        return
    pass

class simple25(lex_test):
    def runTest(self):
        obj = pylex.lexer()
        info = obj.tokenize_pattern("""\|a""")
        self.assert_(info[0] == """|a""")
        return
    pass

class simple26(lex_test):
    def runTest(self):
        obj = pylex.lexer()
        info = obj.tokenize_pattern("""a*""")
        self.assert_(info[0] == """a""")
        self.assert_(info[1] == pylex.STAR)
        return
    pass

class simple27(lex_test):
    def runTest(self):
        obj = pylex.lexer()
        info = obj.tokenize_pattern("""a\*""")
        self.assert_(info[0] == """a*""")
        return
    pass

##############################################################

if __name__=="__main__":
    unittest.main()

    
