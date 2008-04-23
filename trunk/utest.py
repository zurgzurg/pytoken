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
import unittest
import pdb

import pytoken

from pytoken import LPAREN, RPAREN, LBRACKET, RBRACKET, PIPE, STAR, CCAT
from pytoken import IR_LABEL, IR_LDW, IR_LDB, IR_STW, IR_STB, \
     IR_CMP, IR_BEQ, IR_BNE, IR_NOP, IR_ADD, IR_RET

sys.path.append("/home/ramb/src/pylex/src/build/lib.linux-i686-2.5")
import escape

class lex_test(unittest.TestCase):
    def setUp(self):
        global verbose_mode
        if verbose_mode:
            print "a test", self.__class__.__name__
        return

    def check_token(self, obj, txt, exp):
        tok = obj.parse(txt)
        self.assert_(tok == exp)
        return

    def check_structure(self, act, exp):
        if pytoken.struct_equal(act, exp):
            return
        act_str = pytoken.make_string_from_token_list(act)
        exp_str = pytoken.make_string_from_token_list(exp)
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
        obj = pytoken.lexer()
        act = obj.tokenize_pattern("a")
        exp = ("a")
        self.check_structure(act, exp)
        return
    pass

class tokens02(lex_test):
    def runTest(self):
        obj = pytoken.lexer()
        act = obj.tokenize_pattern("ab")
        exp = ("a", CCAT, "b")
        self.check_structure(act, exp)
        return
    pass

class tokens03(lex_test):
    def runTest(self):
        obj = pytoken.lexer()
        act = obj.tokenize_pattern("abc")
        exp = ("a", CCAT, "b", CCAT, "c")
        self.check_structure(act, exp)
        return
    pass

class tokens04(lex_test):
    def runTest(self):
        obj = pytoken.lexer()
        act = obj.tokenize_pattern("abc")
        exp = ("a", CCAT, "b", CCAT, "c")
        self.check_structure(act, exp)
        return
    pass

class tokens04(lex_test):
    def runTest(self):
        obj = pytoken.lexer()
        act = obj.tokenize_pattern("a|b")
        exp = ("a", PIPE, "b")
        self.check_structure(act, exp)
        return
    pass

class tokens05(lex_test):
    def runTest(self):
        obj = pytoken.lexer()
        act = obj.tokenize_pattern("a|bc")
        exp = ("a", PIPE, "b", CCAT, "c")
        self.check_structure(act, exp)
        return
    pass

class tokens06(lex_test):
    def runTest(self):
        obj = pytoken.lexer()
        act = obj.tokenize_pattern("[ab]")
        exp = (LPAREN, "a", PIPE, "b", RPAREN)
        self.check_structure(act, exp)
        return
    pass

class tokens07(lex_test):
    def runTest(self):
        obj = pytoken.lexer()
        act = obj.tokenize_pattern("[a]")
        exp = (LPAREN, "a", RPAREN)
        self.check_structure(act, exp)
        return
    pass

class tokens08(lex_test):
    def runTest(self):
        obj = pytoken.lexer()
        act = obj.tokenize_pattern("a(b|c)")
        exp = ("a", CCAT, LPAREN, "b", PIPE, "c", RPAREN)
        self.check_structure(act, exp)
        return
    pass

class tokens09(lex_test):
    def runTest(self):
        obj = pytoken.lexer()
        act = obj.tokenize_pattern("a(bd|c)")
        exp = ("a", CCAT, LPAREN, "b", CCAT, "d", PIPE, "c", RPAREN)
        self.check_structure(act, exp)
        return
    pass

class tokens10(lex_test):
    def runTest(self):
        obj = pytoken.lexer()
        act = obj.tokenize_pattern("abd|c")
        exp = ("a", CCAT, "b", CCAT, "d", PIPE, "c")
        self.check_structure(act, exp)
        return
    pass

class tokens11(lex_test):
    def runTest(self):
        obj = pytoken.lexer()
        act = obj.tokenize_pattern("a[bc]")
        exp = ("a", CCAT, LPAREN, "b", PIPE, "c", RPAREN)
        self.check_structure(act, exp)
        return
    pass

class tokens12(lex_test):
    def runTest(self):
        obj = pytoken.lexer()
        act = obj.tokenize_pattern("a[c]b")
        exp = ("a", CCAT, LPAREN, "c", RPAREN, CCAT, "b")
        self.check_structure(act, exp)
        return
    pass

class tokens13(lex_test):
    def runTest(self):
        obj = pytoken.lexer()
        act = obj.tokenize_pattern("a(c)b")
        exp = ("a", CCAT, LPAREN, "c", RPAREN, CCAT, "b")
        self.check_structure(act, exp)
        return
    pass

class tokens14(lex_test):
    def runTest(self):
        obj = pytoken.lexer()
        act = obj.tokenize_pattern("ab*")
        exp = ("a", CCAT, "b", STAR)
        self.check_structure(act, exp)
        return
    pass

class tokens15(lex_test):
    def runTest(self):
        obj = pytoken.lexer()
        act = obj.tokenize_pattern("acb*")
        exp = ("a", CCAT, 'c', CCAT, "b", STAR)
        self.check_structure(act, exp)
        return
    pass

##############################################################
class postfix01(lex_test):
    def runTest(self):
        obj = pytoken.lexer()
        act = obj.parse_as_postfix("a")
        exp = ("a")
        self.check_structure(act, exp)
        return
    pass

class postfix02(lex_test):
    def runTest(self):
        obj = pytoken.lexer()
        act = obj.parse_as_postfix("ab")
        exp = ("a", "b", CCAT)
        self.check_structure(act, exp)
        return
    pass

class postfix03(lex_test):
    def runTest(self):
        obj = pytoken.lexer()
        act = obj.parse_as_postfix("abc")
        exp = ("a", "b", CCAT, "c", CCAT)
        self.check_structure(act, exp)
        return
    pass

class postfix04(lex_test):
    def runTest(self):
        obj = pytoken.lexer()
        act = obj.parse_as_postfix("abc")
        exp = ("a", "b", CCAT, "c", CCAT)
        self.check_structure(act, exp)
        return
    pass

class postfix05(lex_test):
    def runTest(self):
        obj = pytoken.lexer()
        act = obj.parse_as_postfix("abcd")
        exp = ("a", "b", CCAT, "c", CCAT, "d", CCAT)
        self.check_structure(act, exp)
        return
    pass

class postfix06(lex_test):
    def runTest(self):
        obj = pytoken.lexer()
        act = obj.parse_as_postfix("a|b")
        exp = ("a", "b", PIPE)
        self.check_structure(act, exp)
        return
    pass

class postfix07(lex_test):
    def runTest(self):
        obj = pytoken.lexer()
        act = obj.parse_as_postfix("a|bc")
        exp = ("a", "b", PIPE, "c", CCAT)
        self.check_structure(act, exp)
        return
    pass

class postfix08(lex_test):
    def runTest(self):
        obj = pytoken.lexer()
        act = obj.parse_as_postfix("a|bc")
        exp = ("a", "b", PIPE, "c", CCAT)
        self.check_structure(act, exp)
        return
    pass

class postfix09(lex_test):
    def runTest(self):
        obj = pytoken.lexer()
        act = obj.parse_as_postfix("(abc)")
        exp = ("a", "b", CCAT, "c", CCAT)
        self.check_structure(act, exp)
        return
    pass

class postfix10(lex_test):
    def runTest(self):
        obj = pytoken.lexer()
        act = obj.parse_as_postfix("(abc)|d")
        exp = ("a", "b", CCAT, "c", CCAT, "d", PIPE)
        self.check_structure(act, exp)
        return
    pass

class postfix11(lex_test):
    def runTest(self):
        obj = pytoken.lexer()
        act = obj.parse_as_postfix("(ab)|(cd)")
        exp = ("a", "b", CCAT, "c", "d", CCAT, PIPE)
        self.check_structure(act, exp)
        return
    pass

class postfix12(lex_test):
    def runTest(self):
        obj = pytoken.lexer()
        act = obj.parse_as_postfix("((ab))")
        exp = ("a", "b", CCAT)
        self.check_structure(act, exp)
        return
    pass

class postfix13(lex_test):
    def runTest(self):
        obj = pytoken.lexer()
        act = obj.parse_as_postfix("a*")
        exp = ("a", STAR)
        self.check_structure(act, exp)
        return
    pass

class postfix14(lex_test):
    def runTest(self):
        obj = pytoken.lexer()
        act = obj.parse_as_postfix("ab*")
        exp = ("a", "b", STAR, CCAT)
        self.check_structure(act, exp)
        return
    pass

class postfix15(lex_test):
    def runTest(self):
        obj = pytoken.lexer()
        act = obj.parse_as_postfix("abc*")
        exp = ("a", "b", CCAT, "c", STAR, CCAT)
        self.check_structure(act, exp)
        return
    pass

class postfix16(lex_test):
    def runTest(self):
        obj = pytoken.lexer()
        act = obj.parse_as_postfix("a(b|c)*")
        exp = ("a", "b", "c", PIPE, STAR, CCAT)
        self.check_structure(act, exp)
        return
    pass

##############################################################
class nfa01(lex_test):
    def runTest(self):
        obj = pytoken.lexer()
        postfix = ("a",)
        nfa_obj = obj.postfix_to_nfa(postfix)
        f = self.follow_single_nfa_path(nfa_obj, "a")
        self.assert_(f in nfa_obj.accepting_states)
        return
    pass

class nfa02(lex_test):
    def runTest(self):
        obj = pytoken.lexer()
        postfix = ("a","b",CCAT)
        nfa_obj = obj.postfix_to_nfa(postfix)
        f = self.follow_single_nfa_path(nfa_obj, ["a", "b"])
        self.assert_(f in nfa_obj.accepting_states)
        return
    pass

class nfa03(lex_test):
    def runTest(self):
        obj = pytoken.lexer()
        postfix = ("a","b",PIPE)
        nfa_obj = obj.postfix_to_nfa(postfix)
        self.assert_(self.path_exists(nfa_obj, "a"))
        self.assert_(self.path_exists(nfa_obj, "b"))
        self.assert_(self.path_exists(nfa_obj, "aa") == False)
        return
    pass

class nfa04(lex_test):
    def runTest(self):
        obj = pytoken.lexer()
        postfix = ("a","b",CCAT)
        nfa_obj = obj.postfix_to_nfa(postfix)
        self.assert_(self.path_exists(nfa_obj, "ab"))
        return
    pass

class nfa05(lex_test):
    def runTest(self):
        obj = pytoken.lexer()
        postfix = ("a",STAR)
        nfa_obj = obj.postfix_to_nfa(postfix)
        self.assert_(self.path_exists(nfa_obj, "a"))
        return
    pass

class nfa06(lex_test):
    def runTest(self):
        obj = pytoken.lexer()
        postfix = ("a",STAR)
        nfa_obj = obj.postfix_to_nfa(postfix)
        self.assert_(self.path_exists(nfa_obj, "aa"))
        return
    pass

class nfa07(lex_test):
    def runTest(self):
        obj = pytoken.lexer()
        postfix = ("a",STAR)
        nfa_obj = obj.postfix_to_nfa(postfix)
        self.assert_(self.path_exists(nfa_obj, ""))
        return
    pass

##############################################################
class dfa01(lex_test):
    def runTest(self):
        obj = pytoken.lexer()
        postfix = ("a",)
        nfa_obj = obj.postfix_to_nfa(postfix)
        dfa_obj = nfa_obj.convert_to_dfa()
        self.assert_(isinstance(dfa_obj, pytoken.dfa))
        return
    pass

class dfa02(lex_test):
    def runTest(self):
        obj = pytoken.lexer()
        postfix = ("a","b",CCAT)
        nfa_obj = obj.postfix_to_nfa(postfix)
        dfa_obj = nfa_obj.convert_to_dfa()
        self.assert_(self.path_exists(dfa_obj, "ab"))
        return
    pass

class dfa03(lex_test):
    def runTest(self):
        obj = pytoken.lexer()
        p = obj.parse_as_postfix("abc")
        nfa_obj = obj.postfix_to_nfa(p)
        dfa_obj = nfa_obj.convert_to_dfa()
        self.assert_(self.path_exists(dfa_obj, "abc"))
        return
    pass

class dfa04(lex_test):
    def runTest(self):
        obj = pytoken.lexer()
        p = obj.parse_as_postfix("a|b")
        nfa_obj = obj.postfix_to_nfa(p)
        dfa_obj = nfa_obj.convert_to_dfa()
        self.assert_(self.path_exists(dfa_obj, "a"))
        self.assert_(self.path_exists(dfa_obj, "b"))
        return
    pass

class dfa05(lex_test):
    def runTest(self):
        obj = pytoken.lexer()
        p = obj.parse_as_postfix("a*")
        nfa_obj = obj.postfix_to_nfa(p)
        dfa_obj = nfa_obj.convert_to_dfa()
        self.assert_(self.path_exists(dfa_obj, "a"))
        self.assert_(self.path_exists(dfa_obj, "aa"))
        return
    pass
##############################################################
class ir01(lex_test):
    def runTest(self):
        lobj = pytoken.lexer()
        code = pytoken.ir_code(lobj)
        code.make_std_vars()
        code.add_ir_label("lab_main1")
        code.add_ir_set(code.data_var, 0)
        code.add_ir_ret(code.data_var)

        lstate = pytoken.lexer_state()
        lstate.set_input("a")

        v = pytoken.run_vcode_simulation(code, lstate)
        self.assert_(v == 0)
        return
    pass

class ir02(lex_test):
    def runTest(self):
        lobj = pytoken.lexer()
        code = pytoken.ir_code(lobj)
        code.make_std_vars()
        code.add_ir_label("lab_main1")
        code.add_ir_set(code.data_var, 2)
        code.add_ir_add(code.data_var, 12)
        code.add_ir_ret(code.data_var)

        lstate = pytoken.lexer_state()
        lstate.set_input("a")

        v = pytoken.run_vcode_simulation(code, lstate)
        self.assert_(v == 14)
        return
    pass

class ir03(lex_test):
    def runTest(self):
        lobj = pytoken.lexer()
        code = pytoken.ir_code(lobj)
        code.make_std_vars()
        code.add_ir_label("lab_main1")
        r2 = code.make_new_var()
        code.add_ir_set(code.data_var, 0xFF)
        code.add_ir_set(r2, code.data_var)
        code.add_ir_ret(r2)

        lstate = pytoken.lexer_state()
        lstate.set_input("a")

        #sim = pytoken.simulator(mem_size=2)
        #v = sim.do_sim(code)
        v = pytoken.run_vcode_simulation(code, lstate)
        self.assert_(v == 0xFF)
        return
    pass

class ir04(lex_test):
    def runTest(self):
        lobj = pytoken.lexer()
        code = pytoken.ir_code(lobj)
        code.make_std_vars()
        code.add_ir_label("lab_main1")
        r2 = code.make_new_var()
        code.add_ir_set(code.data_var, 0xFFEEDDCC)
        code.add_ir_set(r2, code.data_var)
        code.add_ir_ret(r2)

        lstate = pytoken.lexer_state()
        lstate.set_input("a")

        v = pytoken.run_vcode_simulation(code, lstate)
        self.assert_(v == 0xFFEEDDCC)
        return
    pass

##############################################################
class asm01(lex_test):
    def runTest(self):
        obj = pytoken.lexer()
        obj.add_pattern("a|b", None)
        nfa_obj = obj.build_nfa()
        dfa_obj = obj.build_dfa()
        ir   = obj.compile_to_ir()
        return
    pass

class asm02(lex_test):
    def runTest(self):
        obj = pytoken.lexer()
        obj.add_pattern("a", 1)

        nfa_obj = obj.build_nfa()
        dfa_obj = obj.build_dfa()
        code    = obj.compile_to_ir()

        lstate = pytoken.lexer_state()
        lstate.set_input("aa")

        v = pytoken.run_vcode_simulation(code, lstate)
        self.assert_(obj.actions[v] == 1)
        return
    pass

class asm03(lex_test):
    def runTest(self):
        obj = pytoken.lexer()
        obj.add_pattern("b", 2)

        nfa_obj = obj.build_nfa()
        dfa_obj = obj.build_dfa()
        code    = obj.compile_to_ir()

        lstate = pytoken.lexer_state()
        lstate.set_input("bb")

        if 0:
            pytoken.print_instructions(code)

        v = pytoken.run_vcode_simulation(code, lstate)
        self.assert_(obj.actions[v]==2)
        return
    pass

class asm04(lex_test):
    def runTest(self):
        obj = pytoken.lexer()
        obj.add_pattern("ab", 2)

        nfa_obj = obj.build_nfa()
        dfa_obj = obj.build_dfa()
        code    = obj.compile_to_ir()

        lstate = pytoken.lexer_state()
        lstate.set_input("abab")

        v = pytoken.run_vcode_simulation(code, lstate)
        self.assert_(obj.actions[v] == 2)
        return
    pass

class asm05(lex_test):
    def runTest(self):
        obj = pytoken.lexer()
        obj.add_pattern("a|b", 2)

        nfa_obj = obj.build_nfa()
        dfa_obj = obj.build_dfa()
        code    = obj.compile_to_ir()

        lstate = pytoken.lexer_state()

        lstate.set_input("aa")
        v = pytoken.run_vcode_simulation(code, lstate)
        self.assert_(obj.actions[v] == 2)

        lstate.set_input("bb")
        v = pytoken.run_vcode_simulation(code, lstate)
        self.assert_(obj.actions[v] == 2)

        return
    pass

class asm06(lex_test):
    def runTest(self):
        obj = pytoken.lexer()
        obj.add_pattern("a*", 2)

        nfa_obj = obj.build_nfa()
        dfa_obj = obj.build_dfa()
        code    = obj.compile_to_ir()

        lstate = pytoken.lexer_state()

        lstate.set_input("ab")
        v = pytoken.run_vcode_simulation(code, lstate)
        self.assert_(obj.actions[v] == 2)

        lstate.set_input("aab")
        v = pytoken.run_vcode_simulation(code, lstate)
        self.assert_(obj.actions[v] == 2)

        return
    pass

class asm07(lex_test):
    def runTest(self):
        obj = pytoken.lexer()
        obj.add_pattern("a", 1)
        obj.add_pattern("b", 2)

        nfa_obj = obj.build_nfa()
        dfa_obj = obj.build_dfa()
        code    = obj.compile_to_ir()
        return
    pass

class asm08(lex_test):
    def runTest(self):
        obj = pytoken.lexer()
        obj.add_pattern("a", 1)
        obj.add_pattern("b", 2)

        nfa_obj = obj.build_nfa()
        dfa_obj = obj.build_dfa()
        code1   = obj.compile_to_ir()
        code2 = pytoken.compile_to_x86_32(code1)
        return
    pass

class asm09(lex_test):
    def runTest(self):
        obj = pytoken.lexer()
        obj.add_pattern("a", 1)
        obj.add_pattern("b", 2)

        nfa_obj = obj.build_nfa()
        dfa_obj = obj.build_dfa()
        code1   = obj.compile_to_ir()
        code2 = pytoken.compile_to_x86_32(code1)
        return
    pass

class asm10(lex_test):
    def runTest(self):
        obj = pytoken.lexer()
        obj.add_pattern("a", 1)
        obj.add_pattern("b", 2)

        nfa_obj = obj.build_nfa()
        dfa_obj = obj.build_dfa()
        code1   = obj.compile_to_ir()
        code2 = pytoken.compile_to_vcode(code1)
        return
    pass

class asm11(lex_test):
    def runTest(self):
        obj = pytoken.lexer()
        obj.add_pattern("a", 1)
        obj.add_pattern("b", 2)

        nfa_obj = obj.build_nfa()
        dfa_obj = obj.build_dfa()
        code1   = obj.compile_to_ir()
        code2 = pytoken.compile_to_vcode(code1)
        self.assert_(isinstance(code2, pytoken.code))
        return
    pass

class asm12(lex_test):
    def runTest(self):
        obj = pytoken.lexer()
        obj.add_pattern("a", 1)
        obj.add_pattern("b", 2)

        nfa_obj = obj.build_nfa()
        dfa_obj = obj.build_dfa()
        code1   = obj.compile_to_ir()
        code2 = pytoken.compile_to_vcode(code1)
        func = code2.get_token
        self.assert_(callable(func))
        return
    pass

class asm13(lex_test):
    def runTest(self):
        obj = pytoken.lexer()
        obj.add_pattern("a", 1)
        obj.add_pattern("b", 2)

        nfa_obj = obj.build_nfa()
        dfa_obj = obj.build_dfa()
        code1   = obj.compile_to_ir()
        code2 = pytoken.compile_to_vcode(code1)
        self.assert_(len(code2) >= 0)
        return
    pass

class asm14(lex_test):
    def runTest(self):
        obj = pytoken.lexer()
        obj.add_pattern("a", 1)
        obj.add_pattern("b", 2)

        nfa_obj = obj.build_nfa()
        dfa_obj = obj.build_dfa()
        code1   = obj.compile_to_ir()
        code2 = pytoken.compile_to_vcode(code1)
        self.assert_(len(code2) == len(code1.instructions))
        return
    pass

class asm15(lex_test):
    def runTest(self):
        obj = pytoken.lexer()
        obj.add_pattern("a", 1)
        obj.add_pattern("b", 2)

        nfa_obj = obj.build_nfa()
        dfa_obj = obj.build_dfa()
        code1   = obj.compile_to_ir()
        code2 = pytoken.compile_to_vcode(code1)
        
        lstate = pytoken.lexer_state()
        lstate.set_input("ac")

        r = code2.get_token(lstate)
        return
    pass

class asm16(lex_test):
    def runTest(self):
        obj = pytoken.lexer()
        obj.add_pattern("a", 1)
        obj.add_pattern("b", 2)

        nfa_obj = obj.build_nfa()
        dfa_obj = obj.build_dfa()
        code1   = obj.compile_to_ir()
        code2 = pytoken.compile_to_vcode(code1)
        
        lstate = pytoken.lexer_state();
        lstate.set_input("ac")

        r = code2.get_token(lstate)
        return
    pass

class asm17(lex_test):
    def runTest(self):
        lexer_obj = pytoken.lexer()
        lexer_obj.add_pattern("a", 1)
        lexer_obj.add_pattern("b", 2)

        nfa_obj = lexer_obj.build_nfa()
        dfa_obj = lexer_obj.build_dfa()
        code1   = lexer_obj.compile_to_ir()
        code2 = pytoken.compile_to_vcode(code1)
        
        lstate = pytoken.lexer_state();
        lstate.set_input("ab")

        tok = code2.get_token(lstate)
        self.assert_(lexer_obj.actions[tok] == 1)
        return
    pass

class asm18(lex_test):
    def runTest(self):
        lexer_obj = pytoken.lexer()
        lexer_obj.add_pattern("a", 1)
        lexer_obj.add_pattern("b", 2)

        nfa_obj = lexer_obj.build_nfa()
        dfa_obj = lexer_obj.build_dfa()
        code1   = lexer_obj.compile_to_ir()
        code2 = pytoken.compile_to_vcode(code1)
        
        lstate = pytoken.lexer_state();
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
        lexer_obj = pytoken.lexer()
        lexer_obj.add_pattern("a", 1)

        nfa_obj = lexer_obj.build_nfa()
        dfa_obj = lexer_obj.build_dfa()
        code1   = lexer_obj.compile_to_ir()
        if 0:
            print "---------------"
            pytoken.print_instructions(code1)
            print "---------------"

        asm_list = pytoken.ir_to_asm_list_x86_32(code1)
        code_x86 = pytoken.asm_list_x86_32_to_code(asm_list, asm_mode="py",
                                                 print_asm_txt=False)
        
        lstate = pytoken.lexer_state();
        lstate.set_input("aa")

        tok = code_x86.get_token(lstate)
        self.assert_(lexer_obj.actions[tok] == 1)
        offset = lstate.get_cur_offset()
        self.assert_(offset == 1)

        return
    pass

class asm_full_02(lex_test):
    def runTest(self):
        lexer_obj = pytoken.lexer()
        lexer_obj.add_pattern("b", 22)

        nfa_obj = lexer_obj.build_nfa()
        dfa_obj = lexer_obj.build_dfa()
        code1   = lexer_obj.compile_to_ir()

        asm_list = pytoken.ir_to_asm_list_x86_32(code1)
        #pytoken.print_instructions(asm_list)
        code_x86 = pytoken.asm_list_x86_32_to_code(asm_list)
        
        lstate = pytoken.lexer_state();
        lstate.set_input("bb")

        tok = code_x86.get_token(lstate)
        self.assert_(lexer_obj.actions[tok] == 22)
        offset = lstate.get_cur_offset()
        self.assert_(offset == 1)

        return
    pass

class asm_full_03(lex_test):
    def runTest(self):
        lexer_obj = pytoken.lexer()
        lexer_obj.add_pattern("b", 22)
        lexer_obj.add_pattern("a", 44)

        nfa_obj = lexer_obj.build_nfa()
        dfa_obj = lexer_obj.build_dfa()
        code1   = lexer_obj.compile_to_ir()

        asm_list = pytoken.ir_to_asm_list_x86_32(code1)
        code_x86 = pytoken.asm_list_x86_32_to_code(asm_list)
        
        lstate = pytoken.lexer_state();
        lstate.set_input("abc")

        tok = code_x86.get_token(lstate)
        self.assert_(lexer_obj.actions[tok] == 44)
        tok = code_x86.get_token(lstate)
        self.assert_(lexer_obj.actions[tok] == 22)

        return
    pass

class asm_full_04(lex_test):
    def runTest(self):
        lexer_obj = pytoken.lexer()
        lexer_obj.add_pattern("a",  22)
        lexer_obj.add_pattern("ab", 44)

        nfa_obj = lexer_obj.build_nfa()
        dfa_obj = lexer_obj.build_dfa()
        code1   = lexer_obj.compile_to_ir()

        asm_list = pytoken.ir_to_asm_list_x86_32(code1)
        code_x86 = pytoken.asm_list_x86_32_to_code(asm_list)
        
        lstate = pytoken.lexer_state();
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
        lexer_obj = pytoken.lexer()
        lexer_obj.add_pattern("a",  22)

        nfa_obj = lexer_obj.build_nfa()
        dfa_obj = lexer_obj.build_dfa()
        if 0:
            print "----------"
            print "dfa:"
            print dfa_obj
        code1   = lexer_obj.compile_to_ir()
        if 0:
            print "----------"
            pytoken.print_instructions(code1)
            print "----------"
        code2   = lexer_obj.compile_to_machine_code()


        lstate = pytoken.lexer_state();
        lstate.set_input("aa")
        lstate.set_fill_method(self.do_fill)

        tok = lexer_obj.get_token(lstate)
        self.assert_(tok == 22)

        return
    pass

class asm_full_06(lex_test):
    def runTest(self):
        lexer_obj = pytoken.lexer()
        lexer_obj.add_pattern("a", 1)
        lexer_obj.add_pattern("b", 2)
        lexer_obj.compile_to_machine_code()

        buf = pytoken.lexer_state()
        buf.set_input("ab")

        if 0:
            print "FSA="
            print lexer_obj.dfa_obj
            print "------"

        tok = lexer_obj.get_token(buf)
        assert tok == 1
        tok = lexer_obj.get_token(buf)
        assert tok == 2
        return
    pass
        

##############################################################
class asm_full2_01(lex_test):
    def runTest(self):
        lexer_obj = pytoken.lexer()
        lexer_obj.add_pattern("a", 1)

        nfa_obj = lexer_obj.build_nfa()
        dfa_obj = lexer_obj.build_dfa()
        code1   = lexer_obj.compile_to_ir()
        if 0:
            print "---------------"
            pytoken.print_instructions(code1)
            print "---------------"

        asm_list = pytoken.ir_to_asm_list_x86_32(code1)
        if 0:
            pytoken.print_instructions(asm_list)
        code_x86 = pytoken.asm_list_x86_32_to_code(asm_list)
        
        lstate = pytoken.lexer_state();
        lstate.set_input("aa")

        if 0:
            tup = lstate.get_all_state()
            print "lstate=0x%x buf=0x%x size=%d next_char=0x%x eob=%d" % tup
            #escape.print_gdb_info()

        tok = code_x86.get_token(lstate)
        self.assert_(lexer_obj.actions[tok] == 1)
        offset = lstate.get_cur_offset()
        self.assert_(offset == 1)

        return
    pass

##############################################################
class manual_x86_01(lex_test):
    def runTest(self):
        lobj = pytoken.lexer()
        code_ir = pytoken.ir_code(lobj)
        code_ir.make_std_vars()
        code_ir.add_ir_set(code_ir.data_var, 0)
        code_ir.add_ir_ret(code_ir.data_var)

        l = pytoken.ir_to_asm_list_x86_32(code_ir)
        code_x86 = pytoken.asm_list_x86_32_to_code(l)

        lstate   = pytoken.lexer_state()
        v = code_x86.get_token(lstate)
        self.assert_(v == 0)
        return
    pass

class manual_x86_02(lex_test):
    def runTest(self):
        lobj = pytoken.lexer()
        code_ir = pytoken.ir_code(lobj)
        code_ir.make_std_vars()

        code_ir.add_ir_set(code_ir.data_var, 2)
        code_ir.add_ir_ret(code_ir.data_var)

        code_x86 = pytoken.compile_to_x86_32(code_ir)
        lstate   = pytoken.lexer_state()

        v = code_x86.get_token(lstate)
        self.assert_(v == 2)
        return
    pass

class manual_x86_03(lex_test):
    def runTest(self):
        lobj = pytoken.lexer()

        c = pytoken.ir_code(lobj)
        c.make_std_vars()

        c.add_ir_gparm(c.data_var, 1)
        c.add_ir_call(c.data_var, c.call_method_addr, c.data_var,
                         "get_cur_addr", None)
        c.add_ir_ret(c.data_var)

        asm_list = pytoken.ir_to_asm_list_x86_32(c)
        if 0:
            pytoken.print_instructions(asm_list)
        code_x86 = pytoken.asm_list_x86_32_to_code(asm_list)

        base = code_x86.get_start_addr()
        code_bytes = code_x86.get_code()

        lstate   = pytoken.lexer_state()
        lstate.set_input("a")


        v = code_x86.get_token(lstate)
        self.assert_(v is not None)
        return
    pass

class manual_x86_04(lex_test):
    def runTest(self):
        lobj = pytoken.lexer()

        c = pytoken.ir_code(lobj)
        c.make_std_vars()

        c.add_ir_gparm(c.data_var, 1)
        c.add_ir_set(c.str_ptr_var, c.data_var)
        c.add_ir_add(c.str_ptr_var, c.char_ptr_offset)
        c.add_ir_ldw(c.str_ptr_var, c.make_indirect_var(c.str_ptr_var))
        c.add_ir_ret(c.str_ptr_var)

        asm_list = pytoken.ir_to_asm_list_x86_32(c)
        code_x86 = pytoken.asm_list_x86_32_to_code(asm_list, print_asm_txt=False)

        base = code_x86.get_start_addr()
        code_bytes = code_x86.get_code()

        lstate   = pytoken.lexer_state()
        lstate.set_input("a")

        v = code_x86.get_token(lstate)
        self.assert_(v is not None)
        return
    pass

class manual_x86_05(lex_test):
    def runTest(self):
        lobj = pytoken.lexer()

        c = pytoken.ir_code(lobj)
        c.make_std_vars()

        c.add_ir_gparm(c.data_var, 1)
        c.add_ir_set(c.str_ptr_var, c.data_var)
        c.add_ir_add(c.str_ptr_var, c.char_ptr_offset)
        c.add_ir_ldw(c.str_ptr_var, c.make_indirect_var(c.str_ptr_var))
        c.add_ir_ldb(c.data_var, c.make_indirect_var(c.str_ptr_var))
        c.add_ir_ret(c.data_var)

        asm_list = pytoken.ir_to_asm_list_x86_32(c)
        code_x86 = pytoken.asm_list_x86_32_to_code(asm_list)

        base = code_x86.get_start_addr()
        code_bytes = code_x86.get_code()

        lstate   = pytoken.lexer_state()
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
        lstate   = pytoken.lexer_state()
        lstate.set_input("a")
        lstate.set_fill_method(self.do_fill)

        lobj = pytoken.lexer()

        c = pytoken.ir_code(lobj)
        c.make_std_vars()

        # arg 0 = code obj ; 
        # arg 1 = lexer state
        c.add_ir_gparm(c.data_var, 1)
        c.add_ir_call(c.fill_status, c.fill_caller_addr, c.data_var)
        c.add_ir_ret(c.fill_status)

        asm_list = pytoken.ir_to_asm_list_x86_32(c)
        if 0:
            pytoken.print_instructions(asm_list)
            #escape.print_gdb_info()
        code_x86 = pytoken.asm_list_x86_32_to_code(asm_list)

        self.assert_(self.fill_called == False)
        v = code_x86.get_token(lstate)
        self.assert_(self.fill_called == True)
        return

    pass

##############################################################
class assembler01(lex_test):
    def runTest(self):
        asm_list = [
            (None, "ret", None)
            ]

        lstate   = pytoken.lexer_state()
        lstate.set_input("a")

        code = pytoken.asm_list_x86_32_to_code(asm_list)
        code.get_token(lstate)
        return
    pass

class assembler02(lex_test):
    def runTest(self):
        asm_list = [
            (None, "movl", "$42, %eax"),
            (None, "ret", None)
            ]

        lstate   = pytoken.lexer_state()
        lstate.set_input("a")

        code = pytoken.asm_list_x86_32_to_code(asm_list)
        code.get_token(lstate)
        return
    pass

class assembler03(lex_test):
    def runTest(self):
        asm_list = [
            (None, "movl", "%eax, 10(%eax)"),
            ]

        code = pytoken.asm_list_x86_32_to_code(asm_list)
        asm_bytes = code.get_code()
        self.assert_(len(asm_bytes) == 3)
        self.assert_(ord(asm_bytes[0]) == 0x89)
        self.assert_(ord(asm_bytes[1]) == 0x40)
        self.assert_(ord(asm_bytes[2]) == 0x0A)
        return
    pass

class assembler04(lex_test):
    def runTest(self):
        asm_list = [
            (None, "movl", "%eax, 10(%ebx)"),
            ]

        code = pytoken.asm_list_x86_32_to_code(asm_list)
        asm_bytes = code.get_code()
        self.assert_(len(asm_bytes) == 3)
        self.assert_(ord(asm_bytes[0]) == 0x89)
        self.assert_(ord(asm_bytes[1]) == 0x43)
        self.assert_(ord(asm_bytes[2]) == 0x0A)
        return
    pass

class assembler05(lex_test):
    def runTest(self):
        asm_list = [
            (None, "movl", "%eax, 10(%ecx)"),
            ]

        code = pytoken.asm_list_x86_32_to_code(asm_list)
        asm_bytes = code.get_code()
        self.assert_(len(asm_bytes) == 3)
        self.assert_(ord(asm_bytes[0]) == 0x89)
        self.assert_(ord(asm_bytes[1]) == 0x41)
        self.assert_(ord(asm_bytes[2]) == 0x0A)
        return
    pass

class assembler06(lex_test):
    def runTest(self):
        asm_list = [
            (None, "movl", "%ebx, 10(%eax)"),
            ]

        code = pytoken.asm_list_x86_32_to_code(asm_list)
        asm_bytes = code.get_code()
        self.assert_(len(asm_bytes) == 3)
        self.assert_(ord(asm_bytes[0]) == 0x89)
        self.assert_(ord(asm_bytes[1]) == 0x58)
        self.assert_(ord(asm_bytes[2]) == 0x0A)
        return
    pass

class assembler07(lex_test):
    def runTest(self):
        asm_list = [
            (None, "movl", "%ebx, 10(%ebx)"),
            ]

        code = pytoken.asm_list_x86_32_to_code(asm_list)
        asm_bytes = code.get_code()
        self.assert_(len(asm_bytes) == 3)
        self.assert_(ord(asm_bytes[0]) == 0x89)
        self.assert_(ord(asm_bytes[1]) == 0x5B)
        self.assert_(ord(asm_bytes[2]) == 0x0A)
        return
    pass

class assembler08(lex_test):
    def runTest(self):
        asm_list = [
            (None, "movl", "%ebx, 10(%ecx)"),
            ]

        code = pytoken.asm_list_x86_32_to_code(asm_list)
        asm_bytes = code.get_code()
        self.assert_(len(asm_bytes) == 3)
        self.assert_(ord(asm_bytes[0]) == 0x89)
        self.assert_(ord(asm_bytes[1]) == 0x59)
        self.assert_(ord(asm_bytes[2]) == 0x0A)
        return
    pass

class assembler09(lex_test):
    def runTest(self):
        asm_list = [
            (None, "movl", "%ecx, 10(%eax)"),
            ]

        code = pytoken.asm_list_x86_32_to_code(asm_list)
        asm_bytes = code.get_code()
        self.assert_(len(asm_bytes) == 3)
        self.assert_(ord(asm_bytes[0]) == 0x89)
        self.assert_(ord(asm_bytes[1]) == 0x48)
        self.assert_(ord(asm_bytes[2]) == 0x0A)
        return
    pass

class assembler10(lex_test):
    def runTest(self):
        asm_list = [
            (None, "movl", "%ecx, 10(%ebx)"),
            ]

        code = pytoken.asm_list_x86_32_to_code(asm_list)
        asm_bytes = code.get_code()
        self.assert_(len(asm_bytes) == 3)
        self.assert_(ord(asm_bytes[0]) == 0x89)
        self.assert_(ord(asm_bytes[1]) == 0x4B)
        self.assert_(ord(asm_bytes[2]) == 0x0A)
        return
    pass

class assembler11(lex_test):
    def runTest(self):
        asm_list = [
            (None, "movl", "%ecx, 10(%ecx)"),
            ]

        code = pytoken.asm_list_x86_32_to_code(asm_list)
        asm_bytes = code.get_code()
        self.assert_(len(asm_bytes) == 3)
        self.assert_(ord(asm_bytes[0]) == 0x89)
        self.assert_(ord(asm_bytes[1]) == 0x49)
        self.assert_(ord(asm_bytes[2]) == 0x0A)
        return
    pass

class assembler12(lex_test):
    def runTest(self):
        asm_list = [
            (None, "movl", "%eax, 0x12345678(%eax)"),
            ]

        code = pytoken.asm_list_x86_32_to_code(asm_list)
        asm_bytes = code.get_code()
        self.assert_(len(asm_bytes) == 6)
        self.assert_(ord(asm_bytes[0]) == 0x89)
        self.assert_(ord(asm_bytes[1]) == 0x80)
        self.assert_(ord(asm_bytes[2]) == 0x78)
        self.assert_(ord(asm_bytes[3]) == 0x56)
        self.assert_(ord(asm_bytes[4]) == 0x34)
        self.assert_(ord(asm_bytes[5]) == 0x12)
        return
    pass

class assembler13(lex_test):
    def runTest(self):
        asm_list = [
            (None, "movl", "%eax, 0x12345678(%ebx)"),
            ]

        code = pytoken.asm_list_x86_32_to_code(asm_list)
        asm_bytes = code.get_code()
        self.assert_(len(asm_bytes) == 6)
        self.assert_(ord(asm_bytes[0]) == 0x89)
        self.assert_(ord(asm_bytes[1]) == 0x83)
        self.assert_(ord(asm_bytes[2]) == 0x78)
        self.assert_(ord(asm_bytes[3]) == 0x56)
        self.assert_(ord(asm_bytes[4]) == 0x34)
        self.assert_(ord(asm_bytes[5]) == 0x12)
        return
    pass

class assembler14(lex_test):
    def runTest(self):
        asm_list = [
            (None, "movl", "%eax, 0x12345678(%ecx)"),
            ]

        code = pytoken.asm_list_x86_32_to_code(asm_list)
        asm_bytes = code.get_code()
        self.assert_(len(asm_bytes) == 6)
        self.assert_(ord(asm_bytes[0]) == 0x89)
        self.assert_(ord(asm_bytes[1]) == 0x81)
        self.assert_(ord(asm_bytes[2]) == 0x78)
        self.assert_(ord(asm_bytes[3]) == 0x56)
        self.assert_(ord(asm_bytes[4]) == 0x34)
        self.assert_(ord(asm_bytes[5]) == 0x12)
        return
    pass

class assembler15(lex_test):
    def runTest(self):
        asm_list = [
            (None, "movl", "%ebx, 0x12345678(%eax)"),
            ]

        code = pytoken.asm_list_x86_32_to_code(asm_list)
        asm_bytes = code.get_code()
        self.assert_(len(asm_bytes) == 6)
        self.assert_(ord(asm_bytes[0]) == 0x89)
        self.assert_(ord(asm_bytes[1]) == 0x98)
        self.assert_(ord(asm_bytes[2]) == 0x78)
        self.assert_(ord(asm_bytes[3]) == 0x56)
        self.assert_(ord(asm_bytes[4]) == 0x34)
        self.assert_(ord(asm_bytes[5]) == 0x12)
        return
    pass

class assembler16(lex_test):
    def runTest(self):
        asm_list = [
            (None, "movl", "%ebx, 0x12345678(%ebx)"),
            ]

        code = pytoken.asm_list_x86_32_to_code(asm_list)
        asm_bytes = code.get_code()
        self.assert_(len(asm_bytes) == 6)
        self.assert_(ord(asm_bytes[0]) == 0x89)
        self.assert_(ord(asm_bytes[1]) == 0x9B)
        self.assert_(ord(asm_bytes[2]) == 0x78)
        self.assert_(ord(asm_bytes[3]) == 0x56)
        self.assert_(ord(asm_bytes[4]) == 0x34)
        self.assert_(ord(asm_bytes[5]) == 0x12)
        return
    pass

class assembler17(lex_test):
    def runTest(self):
        asm_list = [
            (None, "movl", "%ebx, 0x12345678(%ecx)"),
            ]

        code = pytoken.asm_list_x86_32_to_code(asm_list)
        asm_bytes = code.get_code()
        self.assert_(len(asm_bytes) == 6)
        self.assert_(ord(asm_bytes[0]) == 0x89)
        self.assert_(ord(asm_bytes[1]) == 0x99)
        self.assert_(ord(asm_bytes[2]) == 0x78)
        self.assert_(ord(asm_bytes[3]) == 0x56)
        self.assert_(ord(asm_bytes[4]) == 0x34)
        self.assert_(ord(asm_bytes[5]) == 0x12)
        return
    pass

class assembler18(lex_test):
    def runTest(self):
        asm_list = [
            (None, "movl", "%ecx, 0x12345678(%eax)"),
            ]

        code = pytoken.asm_list_x86_32_to_code(asm_list)
        asm_bytes = code.get_code()
        self.assert_(len(asm_bytes) == 6)
        self.assert_(ord(asm_bytes[0]) == 0x89)
        self.assert_(ord(asm_bytes[1]) == 0x88)
        self.assert_(ord(asm_bytes[2]) == 0x78)
        self.assert_(ord(asm_bytes[3]) == 0x56)
        self.assert_(ord(asm_bytes[4]) == 0x34)
        self.assert_(ord(asm_bytes[5]) == 0x12)
        return
    pass

class assembler19(lex_test):
    def runTest(self):
        asm_list = [
            (None, "movl", "%ecx, 0x12345678(%ebx)"),
            ]

        code = pytoken.asm_list_x86_32_to_code(asm_list)
        asm_bytes = code.get_code()
        self.assert_(len(asm_bytes) == 6)
        self.assert_(ord(asm_bytes[0]) == 0x89)
        self.assert_(ord(asm_bytes[1]) == 0x8B)
        self.assert_(ord(asm_bytes[2]) == 0x78)
        self.assert_(ord(asm_bytes[3]) == 0x56)
        self.assert_(ord(asm_bytes[4]) == 0x34)
        self.assert_(ord(asm_bytes[5]) == 0x12)
        return
    pass

class assembler20(lex_test):
    def runTest(self):
        asm_list = [
            (None, "movl", "%ecx, 0x12345678(%ecx)"),
            ]

        code = pytoken.asm_list_x86_32_to_code(asm_list)
        asm_bytes = code.get_code()
        self.assert_(len(asm_bytes) == 6)
        self.assert_(ord(asm_bytes[0]) == 0x89)
        self.assert_(ord(asm_bytes[1]) == 0x89)
        self.assert_(ord(asm_bytes[2]) == 0x78)
        self.assert_(ord(asm_bytes[3]) == 0x56)
        self.assert_(ord(asm_bytes[4]) == 0x34)
        self.assert_(ord(asm_bytes[5]) == 0x12)
        return
    pass

class assembler21(lex_test):
    def runTest(self):
        asm_list = [
            (None, "movl", "10(%eax), %eax"),
            ]

        code = pytoken.asm_list_x86_32_to_code(asm_list)
        asm_bytes = code.get_code()
        self.assert_(len(asm_bytes) == 3)
        self.assert_(ord(asm_bytes[0]) == 0x8B)
        self.assert_(ord(asm_bytes[1]) == 0x40)
        self.assert_(ord(asm_bytes[2]) == 0x0A)
        return
    pass

class assembler22(lex_test):
    def runTest(self):
        asm_list = [
            (None, "movl", "10(%ebx), %eax"),
            ]

        code = pytoken.asm_list_x86_32_to_code(asm_list)
        asm_bytes = code.get_code()
        self.assert_(len(asm_bytes) == 3)
        self.assert_(ord(asm_bytes[0]) == 0x8B)
        self.assert_(ord(asm_bytes[1]) == 0x43)
        self.assert_(ord(asm_bytes[2]) == 0x0A)
        return
    pass

class assembler23(lex_test):
    def runTest(self):
        asm_list = [
            (None, "movl", "10(%ecx), %eax"),
            ]

        code = pytoken.asm_list_x86_32_to_code(asm_list)
        asm_bytes = code.get_code()
        self.assert_(len(asm_bytes) == 3)
        self.assert_(ord(asm_bytes[0]) == 0x8B)
        self.assert_(ord(asm_bytes[1]) == 0x41)
        self.assert_(ord(asm_bytes[2]) == 0x0A)
        return
    pass

class assembler24(lex_test):
    def runTest(self):
        asm_list = [
            (None, "movl", "10(%eax), %ebx"),
            ]

        code = pytoken.asm_list_x86_32_to_code(asm_list)
        asm_bytes = code.get_code()
        self.assert_(len(asm_bytes) == 3)
        self.assert_(ord(asm_bytes[0]) == 0x8B)
        self.assert_(ord(asm_bytes[1]) == 0x58)
        self.assert_(ord(asm_bytes[2]) == 0x0A)
        return
    pass

class assembler25(lex_test):
    def runTest(self):
        asm_list = [
            (None, "movl", "10(%ebx), %ebx"),
            ]

        code = pytoken.asm_list_x86_32_to_code(asm_list)
        asm_bytes = code.get_code()
        self.assert_(len(asm_bytes) == 3)
        self.assert_(ord(asm_bytes[0]) == 0x8B)
        self.assert_(ord(asm_bytes[1]) == 0x5B)
        self.assert_(ord(asm_bytes[2]) == 0x0A)
        return
    pass

class assembler26(lex_test):
    def runTest(self):
        asm_list = [
            (None, "movl", "10(%ecx), %ebx"),
            ]

        code = pytoken.asm_list_x86_32_to_code(asm_list)
        asm_bytes = code.get_code()
        self.assert_(len(asm_bytes) == 3)
        self.assert_(ord(asm_bytes[0]) == 0x8B)
        self.assert_(ord(asm_bytes[1]) == 0x59)
        self.assert_(ord(asm_bytes[2]) == 0x0A)
        return
    pass

class assembler27(lex_test):
    def runTest(self):
        asm_list = [
            (None, "movl", "10(%eax), %ecx"),
            ]

        code = pytoken.asm_list_x86_32_to_code(asm_list)
        asm_bytes = code.get_code()
        self.assert_(len(asm_bytes) == 3)
        self.assert_(ord(asm_bytes[0]) == 0x8B)
        self.assert_(ord(asm_bytes[1]) == 0x48)
        self.assert_(ord(asm_bytes[2]) == 0x0A)
        return
    pass

class assembler28(lex_test):
    def runTest(self):
        asm_list = [
            (None, "movl", "10(%ebx), %ecx"),
            ]

        code = pytoken.asm_list_x86_32_to_code(asm_list)
        asm_bytes = code.get_code()
        self.assert_(len(asm_bytes) == 3)
        self.assert_(ord(asm_bytes[0]) == 0x8B)
        self.assert_(ord(asm_bytes[1]) == 0x4B)
        self.assert_(ord(asm_bytes[2]) == 0x0A)
        return
    pass

class assembler29(lex_test):
    def runTest(self):
        asm_list = [
            (None, "movl", "10(%ecx), %ecx"),
            ]

        code = pytoken.asm_list_x86_32_to_code(asm_list)
        asm_bytes = code.get_code()
        self.assert_(len(asm_bytes) == 3)
        self.assert_(ord(asm_bytes[0]) == 0x8B)
        self.assert_(ord(asm_bytes[1]) == 0x49)
        self.assert_(ord(asm_bytes[2]) == 0x0A)
        return
    pass

class assembler30(lex_test):
    def runTest(self):
        asm_list = [
            (None, "movb", "10(%eax), %al"),
            ]

        code = pytoken.asm_list_x86_32_to_code(asm_list)
        asm_bytes = code.get_code()
        self.assert_(len(asm_bytes) == 3)
        self.assert_(ord(asm_bytes[0]) == 0x8A)
        self.assert_(ord(asm_bytes[1]) == 0x40)
        self.assert_(ord(asm_bytes[2]) == 0x0A)
        return
    pass

class assembler31(lex_test):
    def runTest(self):
        asm_list = [
            (None, "movb", "10(%eax), %bl"),
            ]

        code = pytoken.asm_list_x86_32_to_code(asm_list)
        asm_bytes = code.get_code()
        self.assert_(len(asm_bytes) == 3)
        self.assert_(ord(asm_bytes[0]) == 0x8A)
        self.assert_(ord(asm_bytes[1]) == 0x58)
        self.assert_(ord(asm_bytes[2]) == 0x0A)
        return
    pass

class assembler32(lex_test):
    def runTest(self):
        asm_list = [
            (None, "movb", "10(%eax), %cl"),
            ]

        code = pytoken.asm_list_x86_32_to_code(asm_list)
        asm_bytes = code.get_code()
        self.assert_(len(asm_bytes) == 3)
        self.assert_(ord(asm_bytes[0]) == 0x8A)
        self.assert_(ord(asm_bytes[1]) == 0x48)
        self.assert_(ord(asm_bytes[2]) == 0x0A)
        return
    pass

class assembler33(lex_test):
    def runTest(self):
        asm_list = [
            (None, "movl", "-4(%ebp), %eax"),
            ]

        code = pytoken.asm_list_x86_32_to_code(asm_list)
        asm_bytes = code.get_code()
        self.assert_(len(asm_bytes) == 3)
        self.assert_(ord(asm_bytes[0]) == 0x8B)
        self.assert_(ord(asm_bytes[1]) == 0x45)
        self.assert_(ord(asm_bytes[2]) == 0xFC)
        return
    pass

class assembler34(lex_test):
    def runTest(self):
        asm_list = [
            (None, "addl", "-4(%ebp), %eax"),
            ]

        code = pytoken.asm_list_x86_32_to_code(asm_list)
        asm_bytes = code.get_code()
        self.assert_(len(asm_bytes) == 3)
        self.assert_(ord(asm_bytes[0]) == 0x03)
        self.assert_(ord(asm_bytes[1]) == 0x45)
        self.assert_(ord(asm_bytes[2]) == 0xFC)
        return
    pass

class assembler35(lex_test):
    def runTest(self):
        asm_list = [
            (None, "cmpl", "$0x10, %eax"),
            ]

        code = pytoken.asm_list_x86_32_to_code(asm_list)
        asm_bytes = code.get_code()
        self.assert_(len(asm_bytes) == 3)
        self.assert_(ord(asm_bytes[0]) == 0x83)
        self.assert_(ord(asm_bytes[1]) == 0xF8)
        self.assert_(ord(asm_bytes[2]) == 0x10)
        return
    pass

class assembler36(lex_test):
    def runTest(self):
        asm_list = [
            (None, "cmpl", "4(%ebp), %eax"),
            ]

        code = pytoken.asm_list_x86_32_to_code(asm_list)
        asm_bytes = code.get_code()
        self.assert_(len(asm_bytes) == 3)
        self.assert_(ord(asm_bytes[0]) == 0x3B)
        self.assert_(ord(asm_bytes[1]) == 0x45)
        self.assert_(ord(asm_bytes[2]) == 0x04)
        return
    pass

class assembler37(lex_test):
    def runTest(self):
        asm_list = [
            ("l1", "nop", None),
            (None, "jne", "l1")
            ]

        code = pytoken.asm_list_x86_32_to_code(asm_list)
        asm_bytes = code.get_code()
        self.assert_(len(asm_bytes) == 3)
        self.assert_(ord(asm_bytes[0]) == 0x90)
        self.assert_(ord(asm_bytes[1]) == 0x75)
        self.assert_(ord(asm_bytes[2]) == 0xFD)
        return
    pass

class assembler38(lex_test):
    def runTest(self):
        asm_list = [
            ("l1", "nop", None),
            (None, "nop", None),
            (None, "je", "l1")
            ]

        code = pytoken.asm_list_x86_32_to_code(asm_list)
        asm_bytes = code.get_code()
        self.assert_(len(asm_bytes) == 4)
        self.assert_(ord(asm_bytes[0]) == 0x90)
        self.assert_(ord(asm_bytes[1]) == 0x90)
        self.assert_(ord(asm_bytes[2]) == 0x74)
        self.assert_(ord(asm_bytes[3]) == 0xFC)
        return
    pass

class assembler39(lex_test):
    def runTest(self):
        asm_list = [
            ("l1", "nop", None),
            (None, "nop", None),
            (None, "jne", "l1")
            ]

        code = pytoken.asm_list_x86_32_to_code(asm_list)
        asm_bytes = code.get_code()
        self.assert_(len(asm_bytes) == 4)
        self.assert_(ord(asm_bytes[0]) == 0x90)
        self.assert_(ord(asm_bytes[1]) == 0x90)
        self.assert_(ord(asm_bytes[2]) == 0x75)
        self.assert_(ord(asm_bytes[3]) == 0xFC)
        return
    pass

class assembler40(lex_test):
    def runTest(self):
        asm_list = [
            ("l1", "nop", None),
            (None, "call", "l1")
            ]

        code = pytoken.asm_list_x86_32_to_code(asm_list)
        asm_bytes = code.get_code()
        self.assert_(len(asm_bytes) == 6)
        self.assert_(ord(asm_bytes[0]) == 0x90)
        self.assert_(ord(asm_bytes[1]) == 0xE8)
        self.assert_(ord(asm_bytes[2]) == 0xFA)
        self.assert_(ord(asm_bytes[3]) == 0xFF)
        self.assert_(ord(asm_bytes[4]) == 0xFF)
        self.assert_(ord(asm_bytes[5]) == 0xFF)
        return
    pass

class assembler41(lex_test):
    def runTest(self):
        asm_list = [
            (None, "add", "$0, %esp")
            ]

        code = pytoken.asm_list_x86_32_to_code(asm_list)
        asm_bytes = code.get_code()
        self.assert_(len(asm_bytes) == 3)
        self.assert_(ord(asm_bytes[0]) == 0x83)
        self.assert_(ord(asm_bytes[1]) == 0xC4)
        self.assert_(ord(asm_bytes[2]) == 0x00)
        return
    pass

class assembler42(lex_test):
    def runTest(self):
        asm_list = [
            (None, "call", "*%eax")
            ]

        code = pytoken.asm_list_x86_32_to_code(asm_list)
        asm_bytes = code.get_code()
        self.assert_(len(asm_bytes) == 2)
        self.assert_(ord(asm_bytes[0]) == 0xFF)
        self.assert_(ord(asm_bytes[1]) == 0xD0)
        return
    pass

class assembler43(lex_test):
    def runTest(self):
        asm_list = [
            (None, "addl", "$10, %eax")
            ]

        code = pytoken.asm_list_x86_32_to_code(asm_list)
        asm_bytes = code.get_code()
        self.assert_(len(asm_bytes) == 3)
        self.assert_(ord(asm_bytes[0]) == 0x83)
        self.assert_(ord(asm_bytes[1]) == 0xC0)
        self.assert_(ord(asm_bytes[2]) == 0x0A)
        return
    pass

class assembler44(lex_test):
    def runTest(self):
        asm_list = [
            (None, "movl", "$10, 4(%ebp)")
            ]

        code = pytoken.asm_list_x86_32_to_code(asm_list)
        asm_bytes = code.get_code()
        self.assert_(len(asm_bytes) == 7)
        self.assert_(ord(asm_bytes[0]) == 0xC7)

        self.assert_(ord(asm_bytes[1]) == 0x45)
        self.assert_(ord(asm_bytes[2]) == 0x04)

        self.assert_(ord(asm_bytes[3]) == 0x0A)
        self.assert_(ord(asm_bytes[4]) == 0x00)
        self.assert_(ord(asm_bytes[5]) == 0x00)
        self.assert_(ord(asm_bytes[6]) == 0x00)
        return
    pass

##############################################################
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
        obj = pytoken.lexer()
        self.assertRaises( RuntimeError, obj.tokenize_pattern, "[")
        return
    pass

class errtest02(lex_test):
    def runTest(self):
        obj = pytoken.lexer()
        self.assertRaises( RuntimeError, obj.tokenize_pattern, "(")
        return
    pass

##############################################################
class looper(lex_test):
    def runTest(self):
        global verbose_mode
        sym_tab = globals()
        for n, sym in sym_tab.iteritems():
            if type(sym) is not type or n in ("looper", "lex_test"):
                continue
            if verbose_mode:
                print "starting on", n
            tc = sym()
            nrefs = sys.gettotalrefcount()
            for i in range(10):
                if verbose_mode:
                    print "testing num", i
                tc.runTest()
                nrefs2 = sys.gettotalrefcount()
                self.assert_(nrefs2 - nrefs2 <= 3)
        return
    pass

##############################################################
##############################################################
##
## usage
##
##
##  utest.py [-v] [test] ... [test]
##  utest.py [-v] -loop <num> <test>
##
##  -v : verbose_mode
##
##
##############################################################
##############################################################
test_groups = ["tokens", "postfix", "nfa", "dfa", "ir",
               "asm", "asm_full_", "asm_full2_", "manual_x86_",
               "assembler", 
               "errtest", "regtest"]
tests_tbl = {}

def get_all_objs_by_name_prefix(p):
    "Return the class objs that have names that match the prefix p."
    symtab = globals()
    plen = len(p)
    all_names = symtab.keys()
    matching_names = []
    for n in all_names:
        if len(n) <= plen or not n.startswith(p):
            continue
        tail = n[plen:]
        if not tail.isdigit():
            continue
        matching_names.append(n)
    matching_names.sort()
    result = [symtab[n] for n in matching_names]
    return result

def get_all_tests():
    "Return a list of all test case class objects"
    symtab = globals()

    all_tests = []
    for g in test_groups:
        tests_tbl[g] = get_all_objs_by_name_prefix(g)
        all_tests.extend(tests_tbl[g])
    all_tests.append(symtab['looper'])

    for sym, obj in symtab.items():
        match = False
        if type(obj) is not type:
            continue
        for gname in test_groups:
            if sym.startswith(gname):
                match = True
        if sym == "looper" or sym=="lex_test":
            match = True
        assert match

    return all_tests

def make_suite(tlist):
    symtab = globals()
    suite = unittest.TestSuite()
    for tname in tlist:
        if tname in test_groups:
            tmp = get_all_objs_by_name_prefix(tname)
            for cls_obj in tmp:
                t_obj = cls_obj()
                suite.addTest(t_obj)
        elif type(tname) is str:
            cls_obj = symtab[tname]
            t_obj = cls_obj()
            suite.addTest(t_obj)
        else:
            cls_obj = tname
            t_obj = cls_obj()
            suite.addTest(t_obj)
    return suite

if __name__=="__main__":
    print "args=", sys.argv
    verbose_mode = False
    if len(sys.argv) > 1 and sys.argv[1] == "-v":
        verbose_mode = True
        sys.argv.pop(1)

    if len(sys.argv) > 1 and sys.argv[1] == "-loop":
        symtab = globals()
        suite = make_suite([sys.argv[3]])
        ntests = int(sys.argv[2])
        for c in xrange(ntests):
            print "on iter", c
            print "fill_addr = 0x%x" % escape.get_fill_caller_addr()
            if c == 5:
                escape.print_gdb_info()
            runner = unittest.TextTestRunner()
            runner.run(suite)

        print "Done"
    else:
        if len(sys.argv) > 1:
            suite = make_suite(sys.argv[1:])
        else:
            tmp = get_all_tests()
            suite = make_suite(tmp)
        runner = unittest.TextTestRunner()
        runner.run(suite)
