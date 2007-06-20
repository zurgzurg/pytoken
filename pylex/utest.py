#!/usr/bin/env python
import os
import sys
import unittest
import pdb

import pylex

class lex_test(unittest.TestCase):
    def check_token(self, obj, txt, exp):
        tok = obj.parse(txt)
        self.assert_(tok == exp)
        return

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

class simple03(unittest.TestCase):
    def runTest(self):
        obj = pylex.lexer()
        obj.define_token("hello", 1)
        obj.compile()
        return True
    pass

class simple04(unittest.TestCase):
    def runTest(self):
        obj = pylex.lexer()
        obj.define_token("hello", 1)
        obj.compile()
        val = obj.parse("hello")
        self.assert_(val == 1)
        return True
    pass

class simple05(unittest.TestCase):
    def runTest(self):
        obj = pylex.lexer()
        obj.define_token("hello", 1)
        obj.define_token(" ", None)
        obj.define_token("world", 2)
        obj.compile()

        toks = obj.parse("hello world")
        self.assert_(toks[0] == 1)
        self.assert_(toks[1] == 2)
        return True
    pass

class simple06(unittest.TestCase):
    def runTest(self):
        obj = pylex.lexer()
        obj.define_token("a", 1)
        obj.define_token("aa", 2)
        obj.compile()

        tok = obj.parse("a")
        self.assert_(tok == 1)

        tok = obj.parse("aa")
        self.assert_(tok == 2)

        return True
    pass

class simple07(unittest.TestCase):
    def runTest(self):
        obj = pylex.lexer()
        obj.define_token("[abcd]", 1)
        obj.compile()

        tok = obj.parse("a")
        self.assert_(tok == 1)
        tok = obj.parse("b")
        self.assert_(tok == 1)
        tok = obj.parse("c")
        self.assert_(tok == 1)
        tok = obj.parse("d")
        self.assert_(tok == 1)

        return True
    pass

class simple08(unittest.TestCase):
    def runTest(self):
        obj = pylex.lexer()
        obj.define_token("[abcd]", 1)
        obj.define_token("g", 2)
        obj.compile()

        tok = obj.parse("a")
        self.assert_(tok == 1)
        tok = obj.parse("b")
        self.assert_(tok == 1)
        tok = obj.parse("c")
        self.assert_(tok == 1)
        tok = obj.parse("d")
        self.assert_(tok == 1)
        tok = obj.parse("g")
        self.assert_(tok == 2)

        return True
    pass

class simple09(unittest.TestCase):
    def runTest(self):
        obj = pylex.lexer()
        obj.define_token("ab", 1)
        obj.define_token("a|b", 2)
        obj.compile()
        
        tok = obj.parse("ab")
        self.assert_(tok == 1)
        tok = obj.parse("b")
        self.assert_(tok == 2)

        return True

class simple10(lex_test):
    def runTest(self):
        obj = pylex.lexer()
        obj.define_token("ab", 1)
        obj.define_token("a|b", 2)
        obj.compile()
        
        self.check_token(obj, "a", 2)
        self.check_token(obj, "ab", 1)
        self.check_token(obj, "b", 2)
        return True

class simple11(lex_test):
    def runTest(self):
        obj = pylex.lexer()
        obj.define_token("a|b", 2)
        obj.compile()
        
        self.check_token(obj, "a", 2)
        self.check_token(obj, "b", 2)

        return True

class simple12(lex_test):
    def runTest(self):
        obj = pylex.lexer()
        obj.define_token("ca|ot", 2)
        obj.compile()
        
        self.check_token(obj, "cat", 2)
        self.check_token(obj, "cot", 2)

        return True

class simple13(lex_test):
    def runTest(self):
        obj = pylex.lexer()
        obj.define_token("ca|ot", 2)
        obj.compile()
        self.assert_(obj.start.num_out_edges() == 1)
        return

class simple14(lex_test):
    def runTest(self):
        obj = pylex.lexer()
        obj.define_token("ca|ot", 2)
        obj.compile()
        self.assert_(obj.start.num_out_edges() == 1)
        return

class simple15(lex_test):
    def runTest(self):
        obj = pylex.lexer()
        obj.define_token("ca|ot", 2)
        obj.compile()
        n2 = obj.start.maybe_get_next_node('c')
        self.assert_(n2.num_out_edges() == 2)
        return

class simple16(lex_test):
    def runTest(self):
        obj = pylex.lexer()
        obj.define_token("(cat)", 2)
        obj.compile()
        self.check_token(obj, "cat", 2)
        return

if __name__=="__main__":
    unittest.main()

    
