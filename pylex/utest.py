#!/usr/bin/env python
import os
import sys
import unittest
import pdb

import pylex

from pylex import PIPE

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

class simple28(lex_test):
    def runTest(self):
        obj = pylex.lexer()
        info = obj.parse_pattern("""a""")
        self.assert_(info[0] == (pylex.TEXT, "a"))
        return
    pass

class simple29(lex_test):
    def runTest(self):
        obj = pylex.lexer()
        info = obj.parse_pattern("""ab""")
        self.assert_(info[0] == (pylex.TEXT, "ab"))
        return
    pass

class simple30(lex_test):
    def runTest(self):
        obj = pylex.lexer()
        info = obj.parse_pattern("""a|b""")
        self.assert_(info[0] == (pylex.PIPE, "a", (pylex.TEXT, "b")))
        return
    pass

class simple31(lex_test):
    def runTest(self):
        obj = pylex.lexer()
        #pdb.set_trace()
        info = obj.parse_pattern("""a|(bb)""")
        self.assert_(info[0] == (pylex.PIPE, "a", (pylex.TEXT, "bb")))
        return
    pass

class simple32(lex_test):
    def runTest(self):
        obj = pylex.lexer()
        info = obj.parse_pattern("""(aa)|(bb)""")
        self.assert_(info[0] == (pylex.PIPE,
                                 (pylex.TEXT, "aa"),
                                 (pylex.TEXT, "bb")))
        return
    pass

class simple33(lex_test):
    def runTest(self):
        obj = pylex.lexer()
        info = obj.parse_pattern("""[abc]|(cat)""")
        self.assert_(info[0] == (pylex.PIPE,
                                 (pylex.PIPE, "a", "b", "c"),
                                 (pylex.TEXT, "cat")))
        return
    pass

class simple34(lex_test):
    def runTest(self):
        obj = pylex.lexer()
        obj.define_token("""a""",  "tok1")
        obj.define_token("""aa""", "tok2")
        obj.compile_to_nfa()
        return
    pass

class simple35(lex_test):
    def runTest(self):
        obj = pylex.lexer()
        obj.define_token("""a""",  "tok1")
        obj.define_token("""aa""", "tok2")
        obj.compile_to_nfa()
        return
    pass

class simple36(lex_test):
    def runTest(self):
        obj = pylex.lexer()
        obj.define_token("""a""",  "tok1")
        obj.compile_to_nfa()
        self.assert_(obj.nfa_obj is not None)
        return
    pass

class simple37(lex_test):
    def runTest(self):
        obj = pylex.lexer()
        obj.define_token("""a""",  "tok1")
        obj.compile_to_nfa()
        k = (0, "a")
        self.assert_(k in obj.nfa_obj.trans_tbl)
        return
    pass

class simple38(lex_test):
    def runTest(self):
        obj = pylex.lexer()
        obj.define_token("""a""",  "tok1")
        obj.compile_to_nfa()

        s0 = obj.nfa_obj.init_state
        s1 = obj.nfa_obj.trans_tbl[(s0, "a")]
        self.assert_(s1[0] in obj.nfa_obj.accepting_states)
        return
    pass

class simple39(lex_test):
    def runTest(self):
        obj = pylex.lexer()
        obj.define_token("""ab""",  "tok1")
        obj.compile_to_nfa()

        s0 = obj.nfa_obj.init_state
        s1 = obj.nfa_obj.trans_tbl[(s0, "a")][0]
        s2 = obj.nfa_obj.trans_tbl[(s1, "b")][0]
        self.assert_(s2 in obj.nfa_obj.accepting_states)
        return
    pass

#class simple40(lex_test):
#    def runTest(self):
#        obj = pylex.lexer()
#        obj.define_token("""a|b""",  "tok1")
#        obj.compile_to_nfa()
#        s0 = obj.nfa_obj.init_state
#        s1 = obj.nfa_obj.trans_tbl[(s0, "a")]
#        s2 = obj.nfa_obj.trans_tbl[(s0, "b")]
#        self.assert_(len(s1) == 1)
#        self.assert_(len(s2) == 1)
#        return
#    pass

class simple40(lex_test):
    def runTest(self):
        obj = pylex.lexer()
        info = obj.parse_pattern_rpn("""a""")
        self.assert_( pylex.struct_equal(info, ("a",)) )
        return
    pass

class simple41(lex_test):
    def runTest(self):
        obj = pylex.lexer()
        info = obj.parse_pattern_rpn("""ab""")
        self.assert_( pylex.struct_equal(info, ("ab",)) )
        return
    pass

if __name__=="__main__":
    unittest.main()

    
