#!/usr/bin/env python
import os
import sys
import unittest
import pdb

import pylex

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
        obj.token("hello", 1)
        obj.compile()
        return True
    pass

class simple04(unittest.TestCase):
    def runTest(self):
        obj = pylex.lexer()
        obj.token("hello", 1)
        obj.compile()
        val = obj.parse("hello")
        self.assert_(val == 1)
        return True
    pass

class simple05(unittest.TestCase):
    def runTest(self):
        obj = pylex.lexer()
        obj.token("hello", 1)
        obj.token(" ", None)
        obj.token("world", 2)
        obj.compile()

        toks = obj.parse("hello world")
        self.assert_(toks[0] == 1)
        self.assert_(toks[1] == 2)
        return True
    pass

class simple06(unittest.TestCase):
    def runTest(self):
        obj = pylex.lexer()
        obj.token("a", 1)
        obj.token("aa", 2)
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
        obj.token("[abcd]", 1)
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
        obj.token("[abcd]", 1)
        obj.token("g", 2)
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

if __name__=="__main__":
    unittest.main()

    
