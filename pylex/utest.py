#!/usr/bin/env python
import os
import sys
import unittest
import pdb

import pylex

from pylex import LPAREN, RPAREN, LBRACKET, RBRACKET, PIPE, STAR, CCAT
from pylex import IFORM_LABEL, IFORM_LDW, IFORM_LDB, IFORM_STW, IFORM_STB, \
     IFORM_CMP, IFORM_BEQ, IFORM_BNE, IFORM_NOP, IFORM_ADD, IFORM_RET

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

    def follow_single_nfa_path(self, nfa, txt):
        cur = nfa.init_state
        for ch in txt:
            k = (cur, ch)
            if k not in nfa.trans_tbl:
                k2 = (cur, None)
                if k2 in nfa.trans_tbl:
                    slist = nfa.trans_tbl[k2]
                    self.assert_(len(slist)==1)
                    cur = slist[0]
                    k = (cur, ch)
            slist = nfa.trans_tbl[k]
            self.assert_(len(slist) == 1)
            cur = slist[0]
        return cur

    def path_exists(self, nfa, txt):
        self.search_stack = [(nfa.init_state, txt)]

        while self.search_stack:
            cur_state, txt = self.search_stack.pop()
            if len(txt)==0 and cur_state in nfa.accepting_states:
                return True
            self.path_exists_2(nfa, cur_state, txt)
            pass

        return False

    def path_exists_2(self, nfa, cur_state, txt):
        cur_state = cur_state
            
        k = (cur_state, None)
        if k in nfa.trans_tbl:
            slist = nfa.trans_tbl[k]
            for nxt_state in slist:
                self.search_stack.append((nxt_state, txt))

        if len(txt) == 0:
            return
        ch = txt[0]

        k = (cur_state, ch)
        if k in nfa.trans_tbl:
            slist = nfa.trans_tbl[k]
            for st2 in slist:
                self.search_stack.append((st2, txt[1:]))

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

class postfix10(lex_test):
    def runTest(self):
        obj = pylex.lexer()
        act = obj.parse_as_postfix("(abc)|d")
        exp = ("a", "b", CCAT, "c", CCAT, "d", PIPE)
        self.check_structure(act, exp)
        return
    pass

class postfix11(lex_test):
    def runTest(self):
        obj = pylex.lexer()
        act = obj.parse_as_postfix("(ab)|(cd)")
        exp = ("a", "b", CCAT, "c", "d", CCAT, PIPE)
        self.check_structure(act, exp)
        return
    pass

class postfix12(lex_test):
    def runTest(self):
        obj = pylex.lexer()
        act = obj.parse_as_postfix("((ab))")
        exp = ("a", "b", CCAT)
        self.check_structure(act, exp)
        return
    pass

class postfix13(lex_test):
    def runTest(self):
        obj = pylex.lexer()
        act = obj.parse_as_postfix("a*")
        exp = ("a", STAR)
        self.check_structure(act, exp)
        return
    pass

class postfix14(lex_test):
    def runTest(self):
        obj = pylex.lexer()
        act = obj.parse_as_postfix("ab*")
        exp = ("a", "b", STAR, CCAT)
        self.check_structure(act, exp)
        return
    pass

class postfix15(lex_test):
    def runTest(self):
        obj = pylex.lexer()
        act = obj.parse_as_postfix("abc*")
        exp = ("a", "b", CCAT, "c", STAR, CCAT)
        self.check_structure(act, exp)
        return
    pass

class postfix16(lex_test):
    def runTest(self):
        obj = pylex.lexer()
        act = obj.parse_as_postfix("a(b|c)*")
        exp = ("a", "b", "c", PIPE, STAR, CCAT)
        self.check_structure(act, exp)
        return
    pass

##############################################################
class nfa01(lex_test):
    def runTest(self):
        obj = pylex.lexer()
        postfix = ("a",)
        nfa_obj = obj.postfix_to_nfa(postfix)
        f = self.follow_single_nfa_path(nfa_obj, "a")
        self.assert_(f in nfa_obj.accepting_states)
        return
    pass

class nfa02(lex_test):
    def runTest(self):
        obj = pylex.lexer()
        postfix = ("a","b",CCAT)
        nfa_obj = obj.postfix_to_nfa(postfix)
        f = self.follow_single_nfa_path(nfa_obj, ["a", "b"])
        self.assert_(f in nfa_obj.accepting_states)
        return
    pass

class nfa03(lex_test):
    def runTest(self):
        obj = pylex.lexer()
        postfix = ("a","b",PIPE)
        nfa_obj = obj.postfix_to_nfa(postfix)
        self.assert_(self.path_exists(nfa_obj, "a"))
        self.assert_(self.path_exists(nfa_obj, "b"))
        self.assert_(self.path_exists(nfa_obj, "aa") == False)
        return
    pass

class nfa04(lex_test):
    def runTest(self):
        obj = pylex.lexer()
        postfix = ("a","b",CCAT)
        nfa_obj = obj.postfix_to_nfa(postfix)
        self.assert_(self.path_exists(nfa_obj, "ab"))
        return
    pass

class nfa05(lex_test):
    def runTest(self):
        obj = pylex.lexer()
        postfix = ("a",STAR)
        nfa_obj = obj.postfix_to_nfa(postfix)
        self.assert_(self.path_exists(nfa_obj, "a"))
        return
    pass

class nfa06(lex_test):
    def runTest(self):
        obj = pylex.lexer()
        postfix = ("a",STAR)
        nfa_obj = obj.postfix_to_nfa(postfix)
        self.assert_(self.path_exists(nfa_obj, "aa"))
        return
    pass

class nfa07(lex_test):
    def runTest(self):
        obj = pylex.lexer()
        postfix = ("a",STAR)
        nfa_obj = obj.postfix_to_nfa(postfix)
        self.assert_(self.path_exists(nfa_obj, ""))
        return
    pass

##############################################################
class dfa01(lex_test):
    def runTest(self):
        obj = pylex.lexer()
        postfix = ("a",)
        nfa_obj = obj.postfix_to_nfa(postfix)
        dfa_obj = nfa_obj.convert_to_dfa()
        self.assert_(isinstance(dfa_obj, pylex.dfa))
        return
    pass

class dfa02(lex_test):
    def runTest(self):
        obj = pylex.lexer()
        postfix = ("a","b",CCAT)
        nfa_obj = obj.postfix_to_nfa(postfix)
        dfa_obj = nfa_obj.convert_to_dfa()
        self.assert_(self.path_exists(dfa_obj, "ab"))
        return
    pass

class dfa03(lex_test):
    def runTest(self):
        obj = pylex.lexer()
        p = obj.parse_as_postfix("abc")
        nfa_obj = obj.postfix_to_nfa(p)
        dfa_obj = nfa_obj.convert_to_dfa()
        self.assert_(self.path_exists(dfa_obj, "abc"))
        return
    pass

class dfa04(lex_test):
    def runTest(self):
        obj = pylex.lexer()
        p = obj.parse_as_postfix("a|b")
        nfa_obj = obj.postfix_to_nfa(p)
        dfa_obj = nfa_obj.convert_to_dfa()
        self.assert_(self.path_exists(dfa_obj, "a"))
        self.assert_(self.path_exists(dfa_obj, "b"))
        return
    pass

class dfa05(lex_test):
    def runTest(self):
        obj = pylex.lexer()
        p = obj.parse_as_postfix("a*")
        nfa_obj = obj.postfix_to_nfa(p)
        dfa_obj = nfa_obj.convert_to_dfa()
        self.assert_(self.path_exists(dfa_obj, "a"))
        self.assert_(self.path_exists(dfa_obj, "aa"))
        return
    pass
##############################################################
class iform01(lex_test):
    def runTest(self):
        code = pylex.iform_code()
        code.make_std_registers()
        code.add_iform_set(code.data_reg, 0)
        code.add_iform_ret(code.data_reg)
        sim = pylex.simulator()
        v = sim.do_sim(code)
        self.assert_(v == 0)
        return
    pass

##############################################################
class asm01(lex_test):
    def runTest(self):
        obj = pylex.lexer()
        p = obj.parse_as_postfix("a|b")
        nfa_obj = obj.postfix_to_nfa(p)
        dfa_obj = nfa_obj.convert_to_dfa()
        iform = pylex.compile_to_intermediate_form(obj, dfa_obj)
        sim = pylex.simulator()
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
