#!/usr/bin/env python
import os
import sys
import unittest
import pdb

import pylex

from pylex import LPAREN, RPAREN, LBRACKET, RBRACKET, PIPE, STAR, CCAT

class lex_test(unittest.TestCase):
    def check_token(self, obj, txt, exp):
        tok = obj.parse(txt)
        self.assert_(tok == exp)
        return
    def check_structure(self, act, exp):
        if pylex.struct_equal(act, exp):
            return
        act_str = pylex.make_string_from_token_list(act)
        exp_str = pylex.make_string_from_token_list(exp)
        self.assert_(False, act_str + " != " + exp_str)
        return
    pass

################################################################
## token tests
################################################################
class tokens01(lex_test):
    def runTest(self):
        obj = pylex.lexer()
        act = obj.tokenize_pattern("a")
        exp = ("a")
        self.check_structure(act, exp)
        return
    pass

class tokens02(lex_test):
    def runTest(self):
        obj = pylex.lexer()
        act = obj.tokenize_pattern("ab")
        exp = ("a", CCAT, "b")
        self.check_structure(act, exp)
        return
    pass

class tokens03(lex_test):
    def runTest(self):
        obj = pylex.lexer()
        act = obj.tokenize_pattern("abc")
        exp = ("a", CCAT, "b", CCAT, "c")
        self.check_structure(act, exp)
        return
    pass

class tokens04(lex_test):
    def runTest(self):
        obj = pylex.lexer()
        act = obj.tokenize_pattern("abc")
        exp = ("a", CCAT, "b", CCAT, "c")
        self.check_structure(act, exp)
        return
    pass

class tokens04(lex_test):
    def runTest(self):
        obj = pylex.lexer()
        act = obj.tokenize_pattern("a|b")
        exp = ("a", PIPE, "b")
        self.check_structure(act, exp)
        return
    pass

class tokens05(lex_test):
    def runTest(self):
        obj = pylex.lexer()
        act = obj.tokenize_pattern("a|bc")
        exp = ("a", PIPE, "b", CCAT, "c")
        self.check_structure(act, exp)
        return
    pass

class tokens06(lex_test):
    def runTest(self):
        obj = pylex.lexer()
        act = obj.tokenize_pattern("[ab]")
        exp = (LPAREN, "a", PIPE, "b", RPAREN)
        self.check_structure(act, exp)
        return
    pass

class tokens07(lex_test):
    def runTest(self):
        obj = pylex.lexer()
        act = obj.tokenize_pattern("[a]")
        exp = (LPAREN, "a", RPAREN)
        self.check_structure(act, exp)
        return
    pass

class tokens08(lex_test):
    def runTest(self):
        obj = pylex.lexer()
        act = obj.tokenize_pattern("a(b|c)")
        exp = ("a", CCAT, LPAREN, "b", PIPE, "c", RPAREN)
        self.check_structure(act, exp)
        return
    pass

class tokens09(lex_test):
    def runTest(self):
        obj = pylex.lexer()
        act = obj.tokenize_pattern("a(bd|c)")
        exp = ("a", CCAT, LPAREN, "b", CCAT, "d", PIPE, "c", RPAREN)
        self.check_structure(act, exp)
        return
    pass

class tokens10(lex_test):
    def runTest(self):
        obj = pylex.lexer()
        act = obj.tokenize_pattern("abd|c")
        exp = ("a", CCAT, "b", CCAT, "d", PIPE, "c")
        self.check_structure(act, exp)
        return
    pass

class tokens11(lex_test):
    def runTest(self):
        obj = pylex.lexer()
        act = obj.tokenize_pattern("a[bc]")
        exp = ("a", CCAT, LPAREN, "b", PIPE, "c", RPAREN)
        self.check_structure(act, exp)
        return
    pass

class tokens12(lex_test):
    def runTest(self):
        obj = pylex.lexer()
        act = obj.tokenize_pattern("a[c]b")
        exp = ("a", CCAT, LPAREN, "c", RPAREN, CCAT, "b")
        self.check_structure(act, exp)
        return
    pass

class tokens13(lex_test):
    def runTest(self):
        obj = pylex.lexer()
        act = obj.tokenize_pattern("a(c)b")
        exp = ("a", CCAT, LPAREN, "c", RPAREN, CCAT, "b")
        self.check_structure(act, exp)
        return
    pass

class tokens14(lex_test):
    def runTest(self):
        obj = pylex.lexer()
        act = obj.tokenize_pattern("ab*")
        exp = ("a", CCAT, "b", STAR)
        self.check_structure(act, exp)
        return
    pass

class tokens15(lex_test):
    def runTest(self):
        obj = pylex.lexer()
        act = obj.tokenize_pattern("acb*")
        exp = ("a", CCAT, 'c', CCAT, "b", STAR)
        self.check_structure(act, exp)
        return
    pass

##############################################################
class postfix01(lex_test):
    def runTest(self):
        obj = pylex.lexer()
        act = obj.parse_as_postfix("a")
        exp = ("a")
        self.check_structure(act, exp)
        return
    pass

class postfix02(lex_test):
    def runTest(self):
        obj = pylex.lexer()
        act = obj.parse_as_postfix("ab")
        exp = ("a", "b", CCAT)
        self.check_structure(act, exp)
        return
    pass

class postfix03(lex_test):
    def runTest(self):
        obj = pylex.lexer()
        act = obj.parse_as_postfix("abc")
        exp = ("a", "b", CCAT, "c", CCAT)
        self.check_structure(act, exp)
        return
    pass

class postfix04(lex_test):
    def runTest(self):
        obj = pylex.lexer()
        act = obj.parse_as_postfix("abc")
        exp = ("a", "b", CCAT, "c", CCAT)
        self.check_structure(act, exp)
        return
    pass

class postfix05(lex_test):
    def runTest(self):
        obj = pylex.lexer()
        act = obj.parse_as_postfix("abcd")
        exp = ("a", "b", CCAT, "c", CCAT, "d", CCAT)
        self.check_structure(act, exp)
        return
    pass

class postfix06(lex_test):
    def runTest(self):
        obj = pylex.lexer()
        act = obj.parse_as_postfix("a|b")
        exp = ("a", "b", PIPE)
        self.check_structure(act, exp)
        return
    pass

class postfix07(lex_test):
    def runTest(self):
        obj = pylex.lexer()
        act = obj.parse_as_postfix("a|bc")
        exp = ("a", "b", PIPE, "c", CCAT)
        self.check_structure(act, exp)
        return
    pass

class postfix08(lex_test):
    def runTest(self):
        obj = pylex.lexer()
        act = obj.parse_as_postfix("a|bc")
        exp = ("a", "b", PIPE, "c", CCAT)
        self.check_structure(act, exp)
        return
    pass

class postfix09(lex_test):
    def runTest(self):
        obj = pylex.lexer()
        act = obj.parse_as_postfix("(abc)")
        exp = ("a", "b", CCAT, "c", CCAT)
        self.check_structure(act, exp)
        return
    pass

##############################################################
class errtest01(lex_test):
    def runTest(self):
        obj = pylex.lexer()
        self.assertRaises( RuntimeError, obj.tokenize_pattern, "[")
        return
    pass

class errtest02(lex_test):
    def runTest(self):
        obj = pylex.lexer()
        self.assertRaises( RuntimeError, obj.tokenize_pattern, "(")
        return
    pass

##############################################################

if __name__=="__main__":
    unittest.main()
