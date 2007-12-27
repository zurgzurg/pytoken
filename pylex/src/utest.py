#!/usr/bin/env python
import os
import sys
import unittest
import pdb

import pylex

from pylex import LPAREN, RPAREN, LBRACKET, RBRACKET, PIPE, STAR, CCAT
from pylex import IFORM_LABEL, IFORM_LDW, IFORM_LDB, IFORM_STW, IFORM_STB, \
     IFORM_CMP, IFORM_BEQ, IFORM_BNE, IFORM_NOP, IFORM_ADD, IFORM_RET

sys.path.append("/home/ramb/src/pylex/src/build/lib.linux-i686-2.5")
import escape

class lex_test(unittest.TestCase):
    def setUp(self):
        if 1:
            return
        print "a test", self.__class__.__name__
        return

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
        lobj = pylex.lexer()
        code = pylex.iform_code(lobj)
        code.make_std_vars()
        code.add_iform_label("lab_main1")
        code.add_iform_set(code.data_var, 0)
        code.add_iform_ret(code.data_var)

        lstate = pylex.lexer_state()
        lstate.set_input("a")

        v = pylex.run_vcode_simulation(code, lstate)
        self.assert_(v == 0)
        return
    pass

class iform02(lex_test):
    def runTest(self):
        lobj = pylex.lexer()
        code = pylex.iform_code(lobj)
        code.make_std_vars()
        code.add_iform_label("lab_main1")
        code.add_iform_set(code.data_var, 2)
        code.add_iform_add(code.data_var, 12)
        code.add_iform_ret(code.data_var)

        lstate = pylex.lexer_state()
        lstate.set_input("a")

        v = pylex.run_vcode_simulation(code, lstate)
        self.assert_(v == 14)
        return
    pass

class iform03(lex_test):
    def runTest(self):
        lobj = pylex.lexer()
        code = pylex.iform_code(lobj)
        code.make_std_vars()
        code.add_iform_label("lab_main1")
        r2 = code.make_new_var()
        code.add_iform_set(code.data_var, 0xFF)
        code.add_iform_set(r2, code.data_var)
        code.add_iform_ret(r2)

        lstate = pylex.lexer_state()
        lstate.set_input("a")

        #sim = pylex.simulator(mem_size=2)
        #v = sim.do_sim(code)
        v = pylex.run_vcode_simulation(code, lstate)
        self.assert_(v == 0xFF)
        return
    pass

class iform04(lex_test):
    def runTest(self):
        lobj = pylex.lexer()
        code = pylex.iform_code(lobj)
        code.make_std_vars()
        code.add_iform_label("lab_main1")
        r2 = code.make_new_var()
        code.add_iform_set(code.data_var, 0xFFEEDDCC)
        code.add_iform_set(r2, code.data_var)
        code.add_iform_ret(r2)

        lstate = pylex.lexer_state()
        lstate.set_input("a")

        v = pylex.run_vcode_simulation(code, lstate)
        self.assert_(v == 0xFFEEDDCC)
        return
    pass

##############################################################
class asm01(lex_test):
    def runTest(self):
        obj = pylex.lexer()
        obj.add_pattern("a|b", None)
        nfa_obj = obj.build_nfa()
        dfa_obj = obj.build_dfa()
        iform   = obj.compile_to_intermediate_form()
        return
    pass

class asm02(lex_test):
    def runTest(self):
        obj = pylex.lexer()
        obj.add_pattern("a", 1)

        nfa_obj = obj.build_nfa()
        dfa_obj = obj.build_dfa()
        code    = obj.compile_to_intermediate_form()

        lstate = pylex.lexer_state()
        lstate.set_input("aa")

        v = pylex.run_vcode_simulation(code, lstate)
        self.assert_(obj.actions[v] == 1)
        return
    pass

class asm03(lex_test):
    def runTest(self):
        obj = pylex.lexer()
        obj.add_pattern("b", 2)

        nfa_obj = obj.build_nfa()
        dfa_obj = obj.build_dfa()
        code    = obj.compile_to_intermediate_form()

        lstate = pylex.lexer_state()
        lstate.set_input("bb")

        v = pylex.run_vcode_simulation(code, lstate)
        self.assert_(obj.actions[v]==2)
        return
    pass

class asm04(lex_test):
    def runTest(self):
        obj = pylex.lexer()
        obj.add_pattern("ab", 2)

        nfa_obj = obj.build_nfa()
        dfa_obj = obj.build_dfa()
        code    = obj.compile_to_intermediate_form()

        lstate = pylex.lexer_state()
        lstate.set_input("abab")

        v = pylex.run_vcode_simulation(code, lstate)
        self.assert_(obj.actions[v] == 2)
        return
    pass

class asm05(lex_test):
    def runTest(self):
        obj = pylex.lexer()
        obj.add_pattern("a|b", 2)

        nfa_obj = obj.build_nfa()
        dfa_obj = obj.build_dfa()
        code    = obj.compile_to_intermediate_form()

        lstate = pylex.lexer_state()

        lstate.set_input("aa")
        v = pylex.run_vcode_simulation(code, lstate)
        self.assert_(obj.actions[v] == 2)

        lstate.set_input("bb")
        v = pylex.run_vcode_simulation(code, lstate)
        self.assert_(obj.actions[v] == 2)

        return
    pass

class asm06(lex_test):
    def runTest(self):
        obj = pylex.lexer()
        obj.add_pattern("a*", 2)

        nfa_obj = obj.build_nfa()
        dfa_obj = obj.build_dfa()
        code    = obj.compile_to_intermediate_form()

        lstate = pylex.lexer_state()

        lstate.set_input("ab")
        v = pylex.run_vcode_simulation(code, lstate)
        self.assert_(obj.actions[v] == 2)

        lstate.set_input("aab")
        v = pylex.run_vcode_simulation(code, lstate)
        self.assert_(obj.actions[v] == 2)

        return
    pass

class asm07(lex_test):
    def runTest(self):
        obj = pylex.lexer()
        obj.add_pattern("a", 1)
        obj.add_pattern("b", 2)

        nfa_obj = obj.build_nfa()
        dfa_obj = obj.build_dfa()
        code    = obj.compile_to_intermediate_form()
        return
    pass

class asm08(lex_test):
    def runTest(self):
        obj = pylex.lexer()
        obj.add_pattern("a", 1)
        obj.add_pattern("b", 2)

        nfa_obj = obj.build_nfa()
        dfa_obj = obj.build_dfa()
        code1   = obj.compile_to_intermediate_form()
        code2 = pylex.compile_to_x86_32(code1)
        return
    pass

class asm09(lex_test):
    def runTest(self):
        obj = pylex.lexer()
        obj.add_pattern("a", 1)
        obj.add_pattern("b", 2)

        nfa_obj = obj.build_nfa()
        dfa_obj = obj.build_dfa()
        code1   = obj.compile_to_intermediate_form()
        code2 = pylex.compile_to_x86_32(code1)
        return
    pass

class asm10(lex_test):
    def runTest(self):
        obj = pylex.lexer()
        obj.add_pattern("a", 1)
        obj.add_pattern("b", 2)

        nfa_obj = obj.build_nfa()
        dfa_obj = obj.build_dfa()
        code1   = obj.compile_to_intermediate_form()
        code2 = pylex.compile_to_vcode(code1)
        return
    pass

class asm11(lex_test):
    def runTest(self):
        obj = pylex.lexer()
        obj.add_pattern("a", 1)
        obj.add_pattern("b", 2)

        nfa_obj = obj.build_nfa()
        dfa_obj = obj.build_dfa()
        code1   = obj.compile_to_intermediate_form()
        code2 = pylex.compile_to_vcode(code1)
        self.assert_(isinstance(code2, pylex.code))
        return
    pass

class asm12(lex_test):
    def runTest(self):
        obj = pylex.lexer()
        obj.add_pattern("a", 1)
        obj.add_pattern("b", 2)

        nfa_obj = obj.build_nfa()
        dfa_obj = obj.build_dfa()
        code1   = obj.compile_to_intermediate_form()
        code2 = pylex.compile_to_vcode(code1)
        func = code2.get_token
        self.assert_(callable(func))
        return
    pass

class asm13(lex_test):
    def runTest(self):
        obj = pylex.lexer()
        obj.add_pattern("a", 1)
        obj.add_pattern("b", 2)

        nfa_obj = obj.build_nfa()
        dfa_obj = obj.build_dfa()
        code1   = obj.compile_to_intermediate_form()
        code2 = pylex.compile_to_vcode(code1)
        self.assert_(len(code2) >= 0)
        return
    pass

class asm14(lex_test):
    def runTest(self):
        obj = pylex.lexer()
        obj.add_pattern("a", 1)
        obj.add_pattern("b", 2)

        nfa_obj = obj.build_nfa()
        dfa_obj = obj.build_dfa()
        code1   = obj.compile_to_intermediate_form()
        code2 = pylex.compile_to_vcode(code1)
        self.assert_(len(code2) == len(code1.instructions))
        return
    pass

class asm15(lex_test):
    def runTest(self):
        obj = pylex.lexer()
        obj.add_pattern("a", 1)
        obj.add_pattern("b", 2)

        nfa_obj = obj.build_nfa()
        dfa_obj = obj.build_dfa()
        code1   = obj.compile_to_intermediate_form()
        code2 = pylex.compile_to_vcode(code1)
        
        lstate = pylex.lexer_state()
        lstate.set_input("ac")

        r = code2.get_token(lstate)
        return
    pass

class asm16(lex_test):
    def runTest(self):
        obj = pylex.lexer()
        obj.add_pattern("a", 1)
        obj.add_pattern("b", 2)

        nfa_obj = obj.build_nfa()
        dfa_obj = obj.build_dfa()
        code1   = obj.compile_to_intermediate_form()
        code2 = pylex.compile_to_vcode(code1)
        
        lstate = pylex.lexer_state();
        lstate.set_input("ac")

        r = code2.get_token(lstate)
        return
    pass

class asm17(lex_test):
    def runTest(self):
        lexer_obj = pylex.lexer()
        lexer_obj.add_pattern("a", 1)
        lexer_obj.add_pattern("b", 2)

        nfa_obj = lexer_obj.build_nfa()
        dfa_obj = lexer_obj.build_dfa()
        code1   = lexer_obj.compile_to_intermediate_form()
        code2 = pylex.compile_to_vcode(code1)
        
        lstate = pylex.lexer_state();
        lstate.set_input("ab")

        tok = code2.get_token(lstate)
        self.assert_(lexer_obj.actions[tok] == 1)
        return
    pass

class asm18(lex_test):
    def runTest(self):
        lexer_obj = pylex.lexer()
        lexer_obj.add_pattern("a", 1)
        lexer_obj.add_pattern("b", 2)

        nfa_obj = lexer_obj.build_nfa()
        dfa_obj = lexer_obj.build_dfa()
        code1   = lexer_obj.compile_to_intermediate_form()
        code2 = pylex.compile_to_vcode(code1)
        
        lstate = pylex.lexer_state();
        lstate.set_input("abc")

        tok = code2.get_token(lstate)
        self.assert_(lexer_obj.actions[tok] == 1)

        tok = code2.get_token(lstate)
        self.assert_(lexer_obj.actions[tok] == 2)

        return
    pass

##############################################################
class asm_full_01(lex_test):
    def runTest(self):
        lexer_obj = pylex.lexer()
        lexer_obj.add_pattern("a", 1)

        nfa_obj = lexer_obj.build_nfa()
        dfa_obj = lexer_obj.build_dfa()
        code1   = lexer_obj.compile_to_intermediate_form()
        if 0:
            print "---------------"
            pylex.print_instructions(code1)
            print "---------------"

        asm_list = pylex.iform_to_asm_list_x86_32(code1)
        code_x86 = pylex.asm_list_x86_32_to_code_obj(asm_list)
        
        lstate = pylex.lexer_state();
        lstate.set_input("aa")

        tok = code_x86.get_token(lstate)
        self.assert_(lexer_obj.actions[tok] == 1)
        offset = lstate.get_cur_offset()
        self.assert_(offset == 1)

        return
    pass

class asm_full_02(lex_test):
    def runTest(self):
        lexer_obj = pylex.lexer()
        lexer_obj.add_pattern("b", 22)

        nfa_obj = lexer_obj.build_nfa()
        dfa_obj = lexer_obj.build_dfa()
        code1   = lexer_obj.compile_to_intermediate_form()

        asm_list = pylex.iform_to_asm_list_x86_32(code1)
        #pylex.print_instructions(asm_list)
        code_x86 = pylex.asm_list_x86_32_to_code_obj(asm_list)
        
        lstate = pylex.lexer_state();
        lstate.set_input("bb")

        tok = code_x86.get_token(lstate)
        self.assert_(lexer_obj.actions[tok] == 22)
        offset = lstate.get_cur_offset()
        self.assert_(offset == 1)

        return
    pass

class asm_full_03(lex_test):
    def runTest(self):
        lexer_obj = pylex.lexer()
        lexer_obj.add_pattern("b", 22)
        lexer_obj.add_pattern("a", 44)

        nfa_obj = lexer_obj.build_nfa()
        dfa_obj = lexer_obj.build_dfa()
        code1   = lexer_obj.compile_to_intermediate_form()

        asm_list = pylex.iform_to_asm_list_x86_32(code1)
        code_x86 = pylex.asm_list_x86_32_to_code_obj(asm_list)
        
        lstate = pylex.lexer_state();
        lstate.set_input("abc")

        tok = code_x86.get_token(lstate)
        self.assert_(lexer_obj.actions[tok] == 44)
        tok = code_x86.get_token(lstate)
        self.assert_(lexer_obj.actions[tok] == 22)

        return
    pass

class asm_full_04(lex_test):
    def runTest(self):
        lexer_obj = pylex.lexer()
        lexer_obj.add_pattern("a",  22)
        lexer_obj.add_pattern("ab", 44)

        nfa_obj = lexer_obj.build_nfa()
        dfa_obj = lexer_obj.build_dfa()
        code1   = lexer_obj.compile_to_intermediate_form()

        asm_list = pylex.iform_to_asm_list_x86_32(code1)
        code_x86 = pylex.asm_list_x86_32_to_code_obj(asm_list)
        
        lstate = pylex.lexer_state();
        lstate.set_input("abc")

        tok = code_x86.get_token(lstate)
        self.assert_(lexer_obj.actions[tok] == 44)

        return
    pass

class asm_full_05(lex_test):
    def do_fill(self, lstate):
        self.fill_called = True
        return 0
    def runTest(self):
        lexer_obj = pylex.lexer()
        lexer_obj.add_pattern("a",  22)

        nfa_obj = lexer_obj.build_nfa()
        dfa_obj = lexer_obj.build_dfa()
        if 0:
            print "----------"
            print "dfa:"
            print dfa_obj
        code1   = lexer_obj.compile_to_intermediate_form()
        if 0:
            print "----------"
            pylex.print_instructions(code1)
            print "----------"
        code2   = lexer_obj.compile_to_machine_code()


        lstate = pylex.lexer_state();
        lstate.set_input("aa")
        lstate.set_fill_method(self.do_fill)

        tok = lexer_obj.get_token(lstate)
        self.assert_(tok == 22)

        return
    pass


##############################################################
class manual_x86_01(lex_test):
    def runTest(self):
        lobj = pylex.lexer()
        code_iform = pylex.iform_code(lobj)
        code_iform.make_std_vars()
        code_iform.add_iform_set(code_iform.data_var, 0)
        code_iform.add_iform_ret(code_iform.data_var)

        l = pylex.iform_to_asm_list_x86_32(code_iform)
        code_x86 = pylex.asm_list_x86_32_to_code_obj(l)

        lstate   = pylex.lexer_state()
        v = code_x86.get_token(lstate)
        self.assert_(v == 0)
        return
    pass

class manual_x86_02(lex_test):
    def runTest(self):
        lobj = pylex.lexer()
        code_iform = pylex.iform_code(lobj)
        code_iform.make_std_vars()

        code_iform.add_iform_set(code_iform.data_var, 2)
        code_iform.add_iform_ret(code_iform.data_var)

        code_x86 = pylex.compile_to_x86_32(code_iform)
        lstate   = pylex.lexer_state()

        v = code_x86.get_token(lstate)
        self.assert_(v == 2)
        return
    pass

class manual_x86_03(lex_test):
    def runTest(self):
        lobj = pylex.lexer()

        c = pylex.iform_code(lobj)
        c.make_std_vars()

        c.add_iform_gparm(c.data_var, 1)
        c.add_iform_call(c.data_var, c.call_method_addr, c.data_var,
                         "get_cur_addr", None)
        c.add_iform_ret(c.data_var)

        asm_list = pylex.iform_to_asm_list_x86_32(c)
        code_x86 = pylex.asm_list_x86_32_to_code_obj(asm_list, print_asm_txt=False)

        base = code_x86.get_start_addr()
        code_bytes = code_x86.get_code()

        lstate   = pylex.lexer_state()
        lstate.set_input("a")


        v = code_x86.get_token(lstate)
        self.assert_(v is not None)
        return
    pass

class manual_x86_04(lex_test):
    def runTest(self):
        lobj = pylex.lexer()

        c = pylex.iform_code(lobj)
        c.make_std_vars()

        c.add_iform_gparm(c.data_var, 1)
        c.add_iform_set(c.str_ptr_var, c.data_var)
        c.add_iform_add(c.str_ptr_var, c.char_ptr_offset)
        c.add_iform_ldw(c.str_ptr_var, c.make_indirect_var(c.str_ptr_var))
        c.add_iform_ret(c.str_ptr_var)

        asm_list = pylex.iform_to_asm_list_x86_32(c)
        code_x86 = pylex.asm_list_x86_32_to_code_obj(asm_list, print_asm_txt=False)

        base = code_x86.get_start_addr()
        code_bytes = code_x86.get_code()

        lstate   = pylex.lexer_state()
        lstate.set_input("a")

        v = code_x86.get_token(lstate)
        self.assert_(v is not None)
        return
    pass

class manual_x86_05(lex_test):
    def runTest(self):
        lobj = pylex.lexer()

        c = pylex.iform_code(lobj)
        c.make_std_vars()

        c.add_iform_gparm(c.data_var, 1)
        c.add_iform_set(c.str_ptr_var, c.data_var)
        c.add_iform_add(c.str_ptr_var, c.char_ptr_offset)
        c.add_iform_ldw(c.str_ptr_var, c.make_indirect_var(c.str_ptr_var))
        c.add_iform_ldb(c.data_var, c.make_indirect_var(c.str_ptr_var))
        c.add_iform_ret(c.data_var)

        asm_list = pylex.iform_to_asm_list_x86_32(c)
        code_x86 = pylex.asm_list_x86_32_to_code_obj(asm_list)

        base = code_x86.get_start_addr()
        code_bytes = code_x86.get_code()

        lstate   = pylex.lexer_state()
        lstate.set_input("a")

        v = code_x86.get_token(lstate)
        self.assert_(v == ord('a'))
        return
    pass

class manual_x86_06(lex_test):
    def do_fill(self, lstate):
        self.fill_called = True
        return 0

    def runTest(self):
        self.fill_called = False
        lstate   = pylex.lexer_state()
        lstate.set_input("a")
        lstate.set_fill_method(self.do_fill)

        lobj = pylex.lexer()

        c = pylex.iform_code(lobj)
        c.make_std_vars()

        # arg 0 = code obj ; 
        # arg 1 = lexer state
        c.add_iform_gparm(c.data_var, 1)
        c.add_iform_call(c.fill_status, c.fill_caller_addr, c.data_var)
        c.add_iform_ret(c.fill_status)

        asm_list = pylex.iform_to_asm_list_x86_32(c)
        if 0:
            pylex.print_instructions(asm_list)
            #escape.print_gdb_info()
        code_x86 = pylex.asm_list_x86_32_to_code_obj(asm_list)

        v = code_x86.get_token(lstate)
        return

    pass

####################
class regtest01(lex_test):
    def runTest(self):
        lbuf = escape.lexer_state()
        lbuf.set_input("a")
        obj = escape.regtest01(lbuf)
        self.assert_(obj is not None)
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
class looper(lex_test):
    def runTest(self):
        sym_tab = globals()
        for n, sym in sym_tab.iteritems():
            if type(sym) is not type or n in ("looper", "lex_test"):
                continue
            if 0:
                print "starting on", n
            tc = sym()
            nrefs = sys.gettotalrefcount()
            for i in range(3):
                if 0:
                    print "testing num", i
                tc.runTest()
                nrefs2 = sys.gettotalrefcount()
                self.assert_(nrefs2 - nrefs2 <= 3)
        return
    pass

##############################################################

if __name__=="__main__":
    unittest.main()
