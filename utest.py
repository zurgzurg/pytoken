#!/usr/bin/env python
########################################################
##
## Copyright (c) 2008-2010, Ram Bhamidipaty
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
import bdb
import traceback
import random
import time

#sys.path.append("./build/lib.linux-i686-2.6")

import pytoken
import escape

from pytoken import DOT, LPAREN, RPAREN, LBRACKET, RBRACKET
from pytoken import PIPE, PLUS, QMARK, STAR, CCAT
from pytoken import IR_LABEL, IR_LDW, IR_LDB, IR_STW, IR_STB, \
     IR_CMP, IR_BEQ, IR_BNE, IR_NOP, IR_ADD, IR_RET

import escape

##########################################################
class lex_test(unittest.TestCase):

    def run(self, result=None):
        if result is None:
            result = self.defaultTestResult()
        result.startTest(self)
        testMethod = getattr(self, self._testMethodName)
        try:
            try:
                self.setUp()
            except KeyboardInterrupt:
                raise
            except:
                result.addError(self, self._exc_info())
                return

            ok = False
            try:
                testMethod()
                ok = True
            except self.failureException:
                result.addFailure(self, self._exc_info())
            except KeyboardInterrupt:
                raise
            except:
                print "Caught an exception"
                print ""
                info = sys.exc_info()
                print "Traceback:", info[0], info[1]
                print ""
                traceback.print_tb(info[2])
                print ""
                pdb.post_mortem(info[2])

                result.addError(self, self._exc_info())

            try:
                self.tearDown()
            except KeyboardInterrupt:
                raise
            except:
                result.addError(self, self._exc_info())
                ok = False
            if ok: result.addSuccess(self)
        finally:
            result.stopTest(self)
    
        return

    #####

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

    def walk_dfa(self, dfa, txt):
        cur = dfa.init_state
        for idx, ch in enumerate(txt):
            k = (cur, ch)
            try:
                slist = dfa.trans_tbl[k]
            except KeyError:
                raise RuntimeError, "mismatch at idx=%d" % idx
            assert len(slist) == 1
            cur = slist[0]
        return cur
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

class tokens16(lex_test):
    def runTest(self):
        obj = pytoken.lexer()
        act = obj.tokenize_pattern("ab*c")
        exp = ("a", CCAT, 'b', STAR, CCAT, "c")
        self.check_structure(act, exp)
        return
    pass

class tokens17(lex_test):
    def runTest(self):
        obj = pytoken.lexer()
        act = obj.tokenize_pattern("[0123456789]+")
        exp = (LPAREN, '0', PIPE, '1', PIPE, '2', PIPE, '3', PIPE, '4',
               PIPE,   '5', PIPE, '6', PIPE, '7', PIPE, '8', PIPE, '9',
               RPAREN, PLUS)
        self.check_structure(act, exp)
        return
    pass

class tokens18(lex_test):
    def runTest(self):
        obj = pytoken.lexer()
        act = obj.tokenize_pattern("a+")
        exp = ('a', PLUS)
        self.check_structure(act, exp)
        return
    pass

class tokens19(lex_test):
    def runTest(self):
        obj = pytoken.lexer()
        act = obj.tokenize_pattern("a?")
        exp = ('a', QMARK)
        self.check_structure(act, exp)
        return
    pass

class tokens20(lex_test):
    def runTest(self):
        ch = 'a'
        while ch <= 'z':
            obj = pytoken.lexer()
            act = obj.tokenize_pattern(ch)
            self.check_structure(act, (ch))
            ch = chr(ord(ch) + 1)
        ch = 'A'
        while ch <= 'Z':
            obj = pytoken.lexer()
            act = obj.tokenize_pattern(ch)
            self.check_structure(act, (ch))
            ch = chr(ord(ch) + 1)
        ch = '0'
        while ch <= '9':
            obj = pytoken.lexer()
            act = obj.tokenize_pattern(ch)
            self.check_structure(act, (ch))
            ch = chr(ord(ch) + 1)
        
        obj = pytoken.lexer()
        act = obj.tokenize_pattern("!")
        self.check_structure(act, ("!"))

        obj = pytoken.lexer()
        act = obj.tokenize_pattern("\"")
        self.check_structure(act, ("\""))

        obj = pytoken.lexer()
        act = obj.tokenize_pattern("#")
        self.check_structure(act, ("#"))

        obj = pytoken.lexer()
        act = obj.tokenize_pattern("%")
        self.check_structure(act, ("%"))

        obj = pytoken.lexer()
        act = obj.tokenize_pattern("&")
        self.check_structure(act, ("&"))

        obj = pytoken.lexer()
        act = obj.tokenize_pattern("\'")
        self.check_structure(act, ("\'"))

        obj = pytoken.lexer()
        act = obj.tokenize_pattern(",")
        self.check_structure(act, (","))

        obj = pytoken.lexer()
        act = obj.tokenize_pattern("-")
        self.check_structure(act, ("-"))

        obj = pytoken.lexer()
        act = obj.tokenize_pattern("/")
        self.check_structure(act, ("/"))

        obj = pytoken.lexer()
        act = obj.tokenize_pattern(":")
        self.check_structure(act, (":"))

        obj = pytoken.lexer()
        act = obj.tokenize_pattern(";")
        self.check_structure(act, (";"))

        obj = pytoken.lexer()
        act = obj.tokenize_pattern("<")
        self.check_structure(act, ("<"))

        obj = pytoken.lexer()
        act = obj.tokenize_pattern("=")
        self.check_structure(act, ("="))

        obj = pytoken.lexer()
        act = obj.tokenize_pattern(">")
        self.check_structure(act, (">"))

        obj = pytoken.lexer()
        act = obj.tokenize_pattern("_")
        self.check_structure(act, ("_"))

        obj = pytoken.lexer()
        act = obj.tokenize_pattern("`")
        self.check_structure(act, ("`"))

        obj = pytoken.lexer()
        act = obj.tokenize_pattern("~")
        self.check_structure(act, ("~"))

        obj = pytoken.lexer()
        act = obj.tokenize_pattern(" ")
        self.check_structure(act, (" "))

        return
    pass

class tokens21(lex_test):
    def runTest(self):
        obj = pytoken.lexer()
        act = obj.tokenize_pattern(".")
        exp = [LPAREN, '\0']
        for code in range(1,128):
            exp.append(CCAT)
            exp.append(chr(code))
        exp.append(RPAREN)
        self.check_structure(act, exp)
        act = obj.tokenize_pattern("[.]")
        self.check_structure(act, (LPAREN, ".", RPAREN))
        return
    pass

class tokens22(lex_test):
    def runTest(self):
        obj = pytoken.lexer()
        got_error = False
        try:
            obj.tokenize_pattern("[")
        except RuntimeError:
            got_error = True
        self.assert_(got_error == True)
        return
    pass

class tokens23(lex_test):
    def runTest(self):
        obj = pytoken.lexer()
        act = obj.tokenize_pattern("[^a]")
        exp = [LPAREN, '\0']
        for code in range(1,128):
            if code == ord("a"):
                continue
            exp.append(PIPE)
            exp.append(chr(code))
        exp.append(RPAREN)
        self.check_structure(act, exp)
        return
    pass

class tokens24(lex_test):
    def runTest(self):
        obj = pytoken.lexer()
        act = obj.tokenize_pattern("[0-9]+")
        exp = (LPAREN, '0', PIPE, '1', PIPE, '2', PIPE, '3', PIPE, '4',
               PIPE,   '5', PIPE, '6', PIPE, '7', PIPE, '8', PIPE, '9',
               RPAREN, PLUS)
        self.check_structure(act, exp)
        return
    pass

class tokens25(lex_test):
    def runTest(self):
        obj = pytoken.lexer()
        act = obj.tokenize_pattern("[0-9-]+")
        exp = (LPAREN, '0', PIPE, '1', PIPE, '2', PIPE, '3', PIPE, '4',
               PIPE,   '5', PIPE, '6', PIPE, '7', PIPE, '8', PIPE, '9',
               PIPE, '-', RPAREN, PLUS)
        self.check_structure(act, exp)
        return
    pass

class tokens26(lex_test):
    def runTest(self):
        obj = pytoken.lexer()
        act = obj.tokenize_pattern("[-0-9]+")
        exp = (LPAREN, '-', PIPE, '0', PIPE, '1', PIPE, '2', PIPE,
               '3', PIPE, '4',
               PIPE,   '5', PIPE, '6', PIPE, '7', PIPE, '8', PIPE, '9',
               RPAREN, PLUS)
        self.check_structure(act, exp)
        return
    pass

class tokens27(lex_test):
    def runTest(self):
        obj = pytoken.lexer()
        act = obj.tokenize_pattern(r'\n')
        exp = ("\n")
        self.check_structure(act, exp)
        act = obj.tokenize_pattern(r'\r')
        exp = ("\r")
        self.check_structure(act, exp)
        act = obj.tokenize_pattern(r'\t')
        exp = ("\t")
        self.check_structure(act, exp)
        return
    pass

class tokens28(lex_test):
    def runTest(self):
        obj = pytoken.lexer()
        act = obj.tokenize_pattern("[a-c0-2]*")
        exp = (LPAREN, 'a', PIPE, 'b', PIPE, 'c', PIPE, '0', PIPE,
               '1', PIPE, '2', RPAREN, STAR)
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
        exp = ("a", "b", "c", CCAT, PIPE)
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

class postfix17(lex_test):
    def runTest(self):
        obj = pytoken.lexer()
        act = obj.parse_as_postfix("[0123]+")
        exp = ("0", "1", PIPE, "2", PIPE, "3", PIPE, PLUS)
        self.check_structure(act, exp)
        return
    pass

class postfix18(lex_test):
    def runTest(self):
        ch = 'a'
        while ch <= 'z':
            obj = pytoken.lexer()
            act = obj.parse_as_postfix(ch)
            self.check_structure(act, (ch))
            ch = chr(ord(ch) + 1)
        ch = 'A'
        while ch <= 'Z':
            obj = pytoken.lexer()
            act = obj.parse_as_postfix(ch)
            self.check_structure(act, (ch))
            ch = chr(ord(ch) + 1)
        ch = '0'
        while ch <= '9':
            obj = pytoken.lexer()
            act = obj.parse_as_postfix(ch)
            self.check_structure(act, (ch))
            ch = chr(ord(ch) + 1)
        
        obj = pytoken.lexer()
        act = obj.parse_as_postfix("!")
        self.check_structure(act, ("!"))

        obj = pytoken.lexer()
        act = obj.parse_as_postfix("\"")
        self.check_structure(act, ("\""))

        obj = pytoken.lexer()
        act = obj.parse_as_postfix("#")
        self.check_structure(act, ("#"))

        obj = pytoken.lexer()
        act = obj.parse_as_postfix("%")
        self.check_structure(act, ("%"))

        obj = pytoken.lexer()
        act = obj.parse_as_postfix("&")
        self.check_structure(act, ("&"))

        obj = pytoken.lexer()
        act = obj.parse_as_postfix("\'")
        self.check_structure(act, ("\'"))

        obj = pytoken.lexer()
        act = obj.parse_as_postfix(",")
        self.check_structure(act, (","))

        obj = pytoken.lexer()
        act = obj.parse_as_postfix("-")
        self.check_structure(act, ("-"))

        obj = pytoken.lexer()
        act = obj.parse_as_postfix("/")
        self.check_structure(act, ("/"))

        obj = pytoken.lexer()
        act = obj.parse_as_postfix(":")
        self.check_structure(act, (":"))

        obj = pytoken.lexer()
        act = obj.parse_as_postfix(";")
        self.check_structure(act, (";"))

        obj = pytoken.lexer()
        act = obj.parse_as_postfix("<")
        self.check_structure(act, ("<"))

        obj = pytoken.lexer()
        act = obj.parse_as_postfix("=")
        self.check_structure(act, ("="))

        obj = pytoken.lexer()
        act = obj.parse_as_postfix(">")
        self.check_structure(act, (">"))

        obj = pytoken.lexer()
        act = obj.parse_as_postfix("_")
        self.check_structure(act, ("_"))

        obj = pytoken.lexer()
        act = obj.parse_as_postfix("`")
        self.check_structure(act, ("`"))

        obj = pytoken.lexer()
        act = obj.parse_as_postfix("~")
        self.check_structure(act, ("~"))

        obj = pytoken.lexer()
        act = obj.parse_as_postfix(" ")
        self.check_structure(act, (" "))

        return
    pass

class postfix19(lex_test):
    def runTest(self):
        obj = pytoken.lexer()
        act = obj.parse_as_postfix("a?")
        exp = ("a", QMARK)
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

class nfa08(lex_test):
    def runTest(self):
        obj = pytoken.lexer()
        postfix = ("a",QMARK)
        nfa_obj = obj.postfix_to_nfa(postfix)
        self.assert_(self.path_exists(nfa_obj, "a"))
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

class dfa06(lex_test):
    def runTest(self):
        obj = pytoken.lexer()
        p = obj.parse_as_postfix("a?")
        nfa_obj = obj.postfix_to_nfa(p)
        dfa_obj = nfa_obj.convert_to_dfa()
        self.assert_(self.path_exists(dfa_obj, "a"))
        self.assert_(self.path_exists(dfa_obj, ""))
        return
    pass

class dfa07(lex_test):
    def runTest(self):
        obj = pytoken.lexer()
        p = obj.parse_as_postfix("[a-z]*\n")
        nfa_obj = obj.postfix_to_nfa(p)
        dfa_obj = nfa_obj.convert_to_dfa()
        self.assert_(self.path_exists(dfa_obj, "a\n"))
        self.assert_(self.path_exists(dfa_obj, "ab\n"))
        self.assert_(self.path_exists(dfa_obj, "abc\n"))
        self.assert_(self.path_exists(dfa_obj, "\n"))
        return
    pass

class dfa08(lex_test):
    def runTest(self):
        obj = pytoken.lexer()
        p = obj.parse_as_postfix("8\\\\")
        if 0:
            print p
        nfa_obj = obj.postfix_to_nfa(p)
        if 0:
            print "nfa="
            print nfa_obj
        dfa_obj = nfa_obj.convert_to_dfa()
        if 0:
            print "dfa="
            print dfa_obj
        s = self.walk_dfa(dfa_obj, "8\\")
        self.assert_(s in dfa_obj.accepting_states)
        return
    pass

class dfa09(lex_test):
    def runTest(self):
        obj = pytoken.lexer()
        p = obj.parse_as_postfix("foo|bar")
        if 0:
            print pytoken.make_string_from_token_list(p)
        nfa_obj = obj.postfix_to_nfa(p)
        if 0:
            print "nfa="
            print nfa_obj
        dfa_obj = nfa_obj.convert_to_dfa()
        if 0:
            print "dfa="
            print dfa_obj
        s = self.walk_dfa(dfa_obj, "foo")
        self.assert_(s in dfa_obj.accepting_states)
        s = self.walk_dfa(dfa_obj, "bar")
        self.assert_(s in dfa_obj.accepting_states)
        return
    pass

##############################################################
# dfa table / dfatable
##############################################################
class dfatable01(lex_test):
    def runTest(self):
        assert pytoken.dfatable is not None
        return
    pass

class dfatable02(lex_test):
    def runTest(self):
        assert pytoken.dfatable is not None
        obj = escape.dfatable()
        for i in xrange(10000):
            obj.set_num_states(5000)
        return
    pass

class dfatable03(lex_test):
    def runTest(self):
        self.assert_(pytoken.dfatable is not None)
        obj = escape.dfatable()
        obj.set_num_states(5000)
        self.assert_(obj.get_num_states() == 5000)
        return
    pass

##############################################################
##
## random regexs
##
##############################################################
class rre_component(object):
    def __init__(self, rgen):
        self.rgen = rgen
        return
    def gen_txt(self, lst):
        assert None, "gen_txt not defined by derived class"
        return
    def gen_regex(self):
        assert None, "gen_regex not defined by derived class"
        return
    # utils
    def make_regex_for_code(self, code):
        assert code >= ord(' ') and code <= ord('~')
        ch = chr(code)
        if ch not in ('(', ')', '[', ']', '|', '\\', '?', '+', '*', '.'):
            return ch
        return '\\' + ch
    def get_rand_char_code(self):
        code = self.rgen.randint(ord(' '), ord('~'))
        return code
    pass

class rre_atom(rre_component):
    def __init__(self, rgen):
        super(rre_atom, self).__init__(rgen)
        self.code = self.get_rand_char_code()
        return
    def gen_txt(self, lst):
        ch = chr(self.code)
        lst.append(ch)
        return
    def gen_regex(self):
        regex = self.make_regex_for_code(self.code)
        return regex
    pass

class rre_concat(rre_component):
    def __init__(self, rgen, lhs, rhs):
        super(rre_concat, self).__init__(rgen)
        self.lhs = lhs
        self.rhs = rhs
        return
    def gen_txt(self, lst):
        self.lhs.gen_txt(lst)
        self.rhs.gen_txt(lst)
        return
    def gen_regex(self):
        re_lhs = self.lhs.gen_regex()
        re_rhs = self.rhs.gen_regex()
        return re_lhs + re_rhs
    pass

class rre_alt(rre_component):
    def __init__(self, rgen, lhs, rhs):
        super(rre_alt, self).__init__(rgen)
        self.lhs = lhs
        self.rhs = rhs
        return
    def gen_txt(self, lst):
        r = self.rgen.randint(0,1)
        if r == 0:
            self.lhs.gen_txt(lst)
        else:
            self.rhs.gen_txt(lst)
        return
    def gen_regex(self):
        re_lhs = self.lhs.gen_regex()
        re_rhs = self.rhs.gen_regex()
        return "(" + re_lhs + ")" + "|" + "(" + re_rhs + ")"
    pass

class rre_star(rre_component):
    def __init__(self, rgen, other):
        super(rre_star, self).__init__(rgen)
        self.other = other
        return
    def gen_txt(self, lst):
        tmp = []
        self.other.gen_txt(tmp)
        n_repeats = self.rgen.randint(0, 20)
        for i in xrange(n_repeats):
            lst.extend(tmp)
        return
    def gen_regex(self):
        re_other = self.other.gen_regex()
        return "(" + re_other + ")*"
    pass

######################

class rand_dfa01(lex_test):
    def runTest(self):
        rgen = random.Random()
        rgen.seed(20)
        
        for i in xrange(200):
            robj = rre_atom(rgen)
            re_txt = robj.gen_regex()
            txt_list = []
            robj.gen_txt(txt_list)
            txt = "".join(txt_list)
            if 0:
                print "re=", re_txt
                print "txt=", txt

            lobj = pytoken.lexer()
            lobj.add_pattern(re_txt, 1)
            lobj.build_nfa()
            dfa_obj = lobj.build_dfa()

            state = self.walk_dfa(dfa_obj, txt)
            if 0:
                print "state=", state
                print "accepting=", dfa_obj.accepting_states
                if state in dfa_obj.accepting_states:
                    print "found"
                else:
                    print "not found"
            self.assert_(state in dfa_obj.accepting_states)
        return
    pass

class rand_dfa02(lex_test):
    def runTest(self):
        rgen = random.Random()
        rgen.seed(20)
        
        for i in xrange(60):
            robj = rre_concat(rgen, rre_atom(rgen), rre_atom(rgen))
            re_txt = robj.gen_regex()
            txt_list = []
            robj.gen_txt(txt_list)
            txt = "".join(txt_list)
            if 0:
                print "re=", re_txt
                print "txt=", txt

            lobj = pytoken.lexer()
            lobj.add_pattern(re_txt, 1)
            lobj.build_nfa()
            dfa_obj = lobj.build_dfa()
            if 0:
                print "dfa obj"
                print dfa_obj

            state = self.walk_dfa(dfa_obj, txt)
            if 0:
                print "state=", state
                print "accepting=", dfa_obj.accepting_states
                if state in dfa_obj.accepting_states:
                    print "found"
                else:
                    print "not found"
            self.assert_(state in dfa_obj.accepting_states)
        return
    pass

class rand_dfa03(lex_test):
    def runTest(self):
        rgen = random.Random()
        rgen.seed(20)
        
        for i in xrange(60):
            robj = rre_concat(rgen,
                          rre_concat(rgen, rre_atom(rgen), rre_atom(rgen)),
                          rre_concat(rgen, rre_atom(rgen), rre_atom(rgen)))
            re_txt = robj.gen_regex()
            txt_list = []
            robj.gen_txt(txt_list)
            txt = "".join(txt_list)
            if 0:
                print "re=", re_txt
                print "txt=", txt

            lobj = pytoken.lexer()
            lobj.add_pattern(re_txt, 1)
            lobj.build_nfa()
            dfa_obj = lobj.build_dfa()
            if 0:
                print "dfa obj"
                print dfa_obj

            state = self.walk_dfa(dfa_obj, txt)
            if 0:
                print "state=", state
                print "accepting=", dfa_obj.accepting_states
                if state in dfa_obj.accepting_states:
                    print "found"
                else:
                    print "not found"
            self.assert_(state in dfa_obj.accepting_states)
        return
    pass

class rand_dfa04(lex_test):
    def runTest(self):
        rgen = random.Random()
        rgen.seed(20)
        
        for i in xrange(60):
            robj = rre_alt(rgen, rre_atom(rgen), rre_atom(rgen))
            re_txt = robj.gen_regex()
            txt_list = []
            robj.gen_txt(txt_list)
            txt = "".join(txt_list)
            if 0:
                print "re=", re_txt
                print "txt=", txt

            lobj = pytoken.lexer()
            lobj.add_pattern(re_txt, 1)
            lobj.build_nfa()
            dfa_obj = lobj.build_dfa()
            if 0:
                print "dfa obj"
                print dfa_obj

            state = self.walk_dfa(dfa_obj, txt)
            if 0:
                print "state=", state
                print "accepting=", dfa_obj.accepting_states
                if state in dfa_obj.accepting_states:
                    print "found"
                else:
                    print "not found"
            self.assert_(state in dfa_obj.accepting_states)
        return
    pass

class rand_dfa05(lex_test):
    def runTest(self):
        rgen = random.Random()
        rgen.seed(20)
        
        for i in xrange(60):
            robj = rre_star(rgen, rre_atom(rgen))
            re_txt = robj.gen_regex()
            txt_list = []
            robj.gen_txt(txt_list)
            txt = "".join(txt_list)
            if 0:
                print "re=", re_txt
                print "txt=", txt

            lobj = pytoken.lexer()
            lobj.add_pattern(re_txt, 1)
            lobj.build_nfa()
            dfa_obj = lobj.build_dfa()
            if 0:
                print "dfa obj"
                print dfa_obj

            state = self.walk_dfa(dfa_obj, txt)
            if 0:
                print "state=", state
                print "accepting=", dfa_obj.accepting_states
                if state in dfa_obj.accepting_states:
                    print "found"
                else:
                    print "not found"
            self.assert_(state in dfa_obj.accepting_states)
        return
    pass

class rand_dfa05b(lex_test):
    def runTest(self):
        rgen = random.Random()
        rgen.seed(20)
        
        for i in xrange(60):
            robj = rre_star(rgen, rre_atom(rgen))
            re_txt = robj.gen_regex()
            if 0:
                print "re=", re_txt
                print "txt=", txt

            lobj = pytoken.lexer()
            lobj.add_pattern(re_txt, 1)
            lobj.build_nfa()
            dfa_obj = lobj.build_dfa()
            if 0:
                print "dfa obj"
                print dfa_obj

            for i in xrange(40):
                txt_list = []
                robj.gen_txt(txt_list)
                txt = "".join(txt_list)

                state = self.walk_dfa(dfa_obj, txt)
                if 0:
                    print "state=", state
                    print "accepting=", dfa_obj.accepting_states
                    if state in dfa_obj.accepting_states:
                        print "found"
                    else:
                        print "not found"
                self.assert_(state in dfa_obj.accepting_states)
        return
    pass

class rand_dfa06(lex_test):
    def runTest(self):
        rgen = random.Random()
        rgen.seed(20)
        
        for i in xrange(60):
            robj = rre_star(rgen, rre_atom(rgen))
            re_txt = robj.gen_regex()
            txt_list = []
            robj.gen_txt(txt_list)
            txt = "".join(txt_list)
            if 0:
                print "re=", re_txt
                print "txt=", txt

            lobj = pytoken.lexer()
            lobj.add_pattern(re_txt, 1)
            lobj.build_nfa()
            dfa_obj = lobj.build_dfa()
            if 0:
                print "dfa obj"
                print dfa_obj

            state = self.walk_dfa(dfa_obj, txt)
            if 0:
                print "state=", state
                print "accepting=", dfa_obj.accepting_states
                if state in dfa_obj.accepting_states:
                    print "found"
                else:
                    print "not found"
            self.assert_(state in dfa_obj.accepting_states)
        return
    pass

##############################################################
##
## rre2 - rand regex 2
##
##############################################################
def rre2_code_2_regex(code):
    assert code >= ord(' ') and code <= ord('~')
    ch = chr(code)
    if ch not in ('(', ')', '[', ']', '|', '\\', '?', '+', '*', '.'):
        return ch
    return '\\' + ch

def rre2_get_rand_char_code(rgen):
    code = rgen.randint(ord(' '), ord('~'))
    return code

class rre2(object):
    def __init__(self, rgen):
        self.rgen = rgen
        self.children = []
        return
    pass
        
class rre2_atom_run(rre2):
    def __init__(self, rgen):
        super(rre2_atom_run, self).__init__(rgen)
        run_len = rgen.randint(1, 10)
        self.codes = [rre2_get_rand_char_code(rgen) for i in xrange(run_len)]
        return
    def get_regex(self):
        re_txt = "".join([rre2_code_2_regex(i) for i in self.codes])
        return re_txt
    def get_txt(self):
        txt = "".join([chr(i) for i in self.codes])
        return txt
    @staticmethod
    def make1(rgen):
        obj = rre2_atom_run(rgen)
        return obj
    pass

class rre2_alt_set(rre2):
    def get_regex(self):
        tmp = [i.get_regex() for i in self.children]
        tmp = ["(%s)" % i for i in tmp]
        tmp = "|".join(tmp)
        return tmp
    def get_txt(self):
        idx = self.rgen.randint(0, len(self.children) - 1)
        txt = self.children[idx].get_txt()
        return txt
    @staticmethod
    def make1(rgen):
        "Alternations of atom_run."
        obj = rre2_alt_set(rgen)
        n_children = rgen.randint(1, 8)
        for i in xrange(n_children):
            child = rre2_atom_run.make1(rgen)
            obj.children.append(child)
        return obj
    pass

class rre2_star(rre2):
    def get_regex(self):
        tmp1 = self.children[0].get_regex()
        tmp2 = "(" + tmp1 + ")*"
        return tmp2
    def get_txt(self):
        n = self.rgen.randint(0, 5)
        tmp = self.children[0].get_txt()
        return tmp * n
        return
    @staticmethod
    def make1(rgen):
        "star on top of alt"
        obj = rre2_star(rgen)
        child = rre2_alt_set.make1(rgen)
        obj.children.append(child)
        return obj
    pass

def rre2_do_test(rgen, robj_maker, n1, n2, tc_obj):
    for i in xrange(n1):
        robj = robj_maker(rgen)
        re_txt = robj.get_regex()
        if 0:
            print "re=", re_txt

        lobj = pytoken.lexer()
        lobj.add_pattern(re_txt, 1)
        lobj.build_nfa()
        dfa_obj = lobj.build_dfa()
        if 0:
            print "dfa obj"
            print dfa_obj

        for j in xrange(n2):
            txt = robj.get_txt()
            if 0:
                print "txt=", txt
            state = tc_obj.walk_dfa(dfa_obj, txt)
            if 0:
                print "state=", state
                print "accepting=", dfa_obj.accepting_states
                if state in dfa_obj.accepting_states:
                    print "found"
                else:
                    print "not found"
            tc_obj.assert_(state in dfa_obj.accepting_states)
    return

########

class rre2_dfa01(lex_test):
    def runTest(self):
        rgen = random.Random()
        rgen.seed(100)
        rre2_do_test(rgen, rre2_alt_set.make1, 60, 30, self)
        return
    pass

class rre2_dfa02(lex_test):
    def runTest(self):
        rgen = random.Random()
        rgen.seed(101)
        rre2_do_test(rgen, rre2_star.make1, 60, 30, self)
        return
    pass

##############################################################
class uval01(lex_test):
    def runTest(self):
        v = escape.uval32(8)
        self.assert_(v is not None)
        s = str(v)
        self.assert_(s == "0x8")
        return
    pass

class uval02(lex_test):
    def runTest(self):
        v = escape.uval32(0xffffffff)
        #print "v is ", str(v)
        self.assert_(v is not None)
        s = str(v)
        self.assert_(s == "0xffffffff")
        return
    pass

class uval03(lex_test):
    def runTest(self):
        v = escape.uval32(-1)
        #print "v is ", str(v)
        s = str(v)
        self.assert_(s == "0xffffffff")
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

        v = pytoken.run_vcode_simulation(code, lstate, debug_flag=False)
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
        #escape.print_gdb_info()
        if 0:
            pytoken.print_instructions(code1)
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
        
        if 0:
            pytoken.print_instructions(code2)

        lstate = pytoken.lexer_state();
        lstate.set_input("abc")

        tok = code2.get_token(lstate)
        self.assert_(lexer_obj.actions[tok] == 1)

        if 0:
            print lstate

        tok = code2.get_token(lstate)
        if 0:
            print "tok is -->", tok

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
        self.assert_(tok == 1)

        if 0:
            print "lexer state"
            print buf

        tok = lexer_obj.get_token(buf)
        #print "Returned tok", tok
        self.assert_(tok == 2)
        return
    pass

class asm_full_07(lex_test):
    def runTest(self):
        lexer_obj = pytoken.lexer()
        lexer_obj.add_pattern("ab", 1)
        lexer_obj.compile_to_machine_code(debug=False)

        if 0:
            pytoken.print_instructions(lexer_obj.ir)

        def fill_func(lbuf):
            lbuf.add_to_buffer("b")
            return

        # escape.print_gdb_info()

        buf = pytoken.lexer_state()
        buf.set_input("a")

        buf.set_fill_method(fill_func)


        tok = lexer_obj.get_token(buf)
        return
    pass

class asm_full_08(lex_test):
    def runTest(self):
        lexer_obj = pytoken.lexer()
        lexer_obj.add_pattern("ab", 1)
        lexer_obj.compile_to_machine_code(debug=False)

        buf = pytoken.lexer_state()
        buf.set_input("ab")

        tok = lexer_obj.get_token(buf)
        self.assert_(tok == 1)
        tok = lexer_obj.get_token(buf)
        self.assert_(tok == "EOB")
        return
    pass

class asm_full_09(lex_test):
    def runTest(self):
        lexer_obj = pytoken.lexer()
        lexer_obj.add_pattern("ab", 1)
        lexer_obj.compile_to_machine_code(debug=False)

        buf = pytoken.lexer_state()
        buf.set_input("ababab")

        tok = lexer_obj.get_token(buf)
        self.assert_(tok == 1)
        tok = lexer_obj.get_token(buf)
        self.assert_(tok == 1)
        tok = lexer_obj.get_token(buf)
        self.assert_(tok == 1)
        tok = lexer_obj.get_token(buf)
        self.assert_(tok == "EOB")
        return
    pass

class asm_full_10(lex_test):
    def runTest(self):
        lexer_obj = pytoken.lexer()
        lexer_obj.add_pattern("ab", 1)
        lexer_obj.add_pattern("ac", 2)
        lexer_obj.compile_to_machine_code(debug=False)

        buf = pytoken.lexer_state()

        buf.set_input("ab")
        tok = lexer_obj.get_token(buf)
        self.assert_(tok == 1)

        buf.set_input("ac")
        tok = lexer_obj.get_token(buf)
        self.assert_(tok == 2)

        return
    pass

class asm_full_11(lex_test):
    def setUp(self):
        tmp = self.id().split(".")
        self.fname = tmp[1] + ".tmp"
        fp = open(self.fname, "w")
        fp.write("a")
        fp.close()
        return

    def tearDown(self):
        os.unlink(self.fname)
        return

    def runTest(self):
        lo = pytoken.lexer()
        lo.add_pattern("a", 1)
        lo.compile_to_machine_code(debug=False)

        fp2 = open(self.fname)
        buf = pytoken.lexer_state()
        buf.set_input(fp2)

        tok = lo.get_token(buf)
        self.assert_(tok == 1)

        fp2.close()

        return
    pass

class asm_full_12(lex_test):
    def runTest(self):
        lexer_obj = pytoken.lexer()
        lexer_obj.add_pattern("ab", 1)
        lexer_obj.add_pattern(" ", None)
        lexer_obj.compile_to_machine_code(debug=False)

        buf = pytoken.lexer_state()
        buf.set_input("ab ab")

        tok = lexer_obj.get_token(buf)
        self.assert_(tok == 1)

        tok = lexer_obj.get_token(buf)
        self.assert_(tok == 1)

        tok = lexer_obj.get_token(buf)
        self.assert_(tok == "EOB")
        return
    pass

class asm_full_13(lex_test):
    def action(self, lstate):
        self.n_calls += 1
        return "foobar"

    def runTest(self):
        self.n_calls = 0

        lexer_obj = pytoken.lexer()
        lexer_obj.add_pattern("ab", self.action)
        lexer_obj.add_pattern(" ", None)
        lexer_obj.compile_to_machine_code(debug=False)

        buf = pytoken.lexer_state()
        buf.set_input("ab ab")

        tok = lexer_obj.get_token(buf)
        self.assert_(tok == "foobar")

        tok = lexer_obj.get_token(buf)
        self.assert_(tok == "foobar")

        tok = lexer_obj.get_token(buf)
        self.assert_(tok == "EOB")

        self.assert_(self.n_calls == 2)
        return
    pass

class asm_full_14(lex_test):
    def action(self, txt):
        self.n_calls += 1
        self.txt += txt
        return "foobar"

    def runTest(self):
        self.n_calls = 0
        self.txt = ""

        lexer_obj = pytoken.lexer()
        lexer_obj.add_pattern("ab", self.action)
        lexer_obj.add_pattern(" ", None)
        lexer_obj.compile_to_machine_code(debug=False)

        buf = pytoken.lexer_state()
        buf.set_input("ab ab")

        tok = lexer_obj.get_token(buf)
        self.assert_(tok == "foobar")

        tok = lexer_obj.get_token(buf)
        self.assert_(tok == "foobar")

        tok = lexer_obj.get_token(buf)
        self.assert_(tok == "EOB")

        self.assert_(self.n_calls == 2)
        self.assert_(self.txt == "abab")
        return
    pass

class asm_full_15(lex_test):
    def setUp(self):
        tmp = self.id().split(".")
        self.fname = tmp[1] + ".tmp"
        fp = open(self.fname, "w")
        for i in xrange(4):
            print >>fp, "foobar "
        fp.close()

        if 0:
            fp = open(self.fname, "r")
            txt = fp.read()
            fp.close
            print txt
        return

    def tearDown(self):
        os.unlink(self.fname)
        return

    def runTest(self):
        lo = pytoken.lexer()
        lo.add_pattern("foobar", 1)
        lo.add_pattern(" ",  None)
        lo.add_pattern("\n", None)
        lo.compile_to_machine_code(debug=False)

        if 0:
            pytoken.print_instructions(lo.ir)

        fp2 = open(self.fname)
        buf = pytoken.lexer_state()
        buf.set_input(fp2)

        #escape.print_gdb_info()

        for i in xrange(4):
            tok = lo.get_token(buf)
            #print "got a token", i, tok
            #print "state -->", buf.get_all_state()
            self.assert_(tok == 1)

        tok = lo.get_token(buf)
        self.assert_(tok == "EOB")

        fp2.close()
        return
    pass

class asm_full_16(lex_test):
    def setUp(self):
        tmp = self.id().split(".")
        self.fname = tmp[1] + ".tmp"
        fp = open(self.fname, "w")
        for i in xrange(4096):
            print >>fp, "foobar "
            print >>fp, "12345678901234567"
        fp.close()
        return

    def tearDown(self):
        os.unlink(self.fname)
        return

    def runTest(self):
        lo = pytoken.lexer()
        lo.add_pattern("foobar ", 1)
        lo.add_pattern("12345678901234567", 2)
        lo.add_pattern("\n", None)
        lo.compile_to_machine_code(debug=False)

        fp2 = open(self.fname)
        buf = pytoken.lexer_state()
        buf.set_input(fp2)

        for i in xrange(4096):
            tok = lo.get_token(buf)
            self.assert_(tok == 1)
            tok = lo.get_token(buf)
            self.assert_(tok == 2)

        tok = lo.get_token(buf)
        self.assert_(tok == "EOB")

        fp2.close()
        return
    pass

class asm_full_17(lex_test):
    def setUp(self):
        tmp = self.id().split(".")
        self.fname = tmp[1] + ".tmp"

        txt = "a" + "b" * 2000 + "c"
        fp = open(self.fname, "w")
        fp.write(txt)
        fp.close()

        return

    def action(self, t1):
        return t1

    def tearDown(self):
        os.unlink(self.fname)
        return

    def runTest(self):
        lo = pytoken.lexer()
        lo.add_pattern("ab*c", self.action)
        lo.add_pattern("\n", None)
        lo.compile_to_machine_code(debug=False)

        fp2 = open(self.fname)
        buf = pytoken.lexer_state()
        buf.set_input(fp2)

        txt2 = "a" + "b" * 2000 + "c"

        tok = lo.get_token(buf)
        self.assert_(tok == txt2)

        tok = lo.get_token(buf)
        self.assert_(tok == "EOB")

        fp2.close()
        return
    pass

class asm_full_18(lex_test):
    def runTest(self):
        lexer_obj = pytoken.lexer()
        lexer_obj.add_pattern("a", 1)
        lexer_obj.add_pattern(" ", None)
        lexer_obj.compile_to_machine_code(debug=False)

        if 0:
            print lexer_obj.dfa_obj
            pytoken.print_instructions(lexer_obj.ir)

        buf = pytoken.lexer_state()
        buf.set_input("a a")

        lexer_obj.gettoken_obj.set_buf2(buf)

        t1 = lexer_obj.gettoken_obj.get_token2()
        t2 = lexer_obj.gettoken_obj.get_token2()
        self.assert_(t1 == t2)

        return
    pass

class asm_full_19(lex_test):
    def runTest(self):
        lexer_obj = pytoken.lexer()
        lexer_obj.add_pattern("[01]+", 1)
        lexer_obj.add_pattern(" ", None)
        lexer_obj.compile_to_machine_code(debug=False)

        if 0:
            print "NFA:"
            print lexer_obj.nfa_obj
            print "DFA:"
            print lexer_obj.dfa_obj
            #pytoken.print_instructions(lexer_obj.ir)

        buf = pytoken.lexer_state()
        buf.set_input("00 11")

        tok = lexer_obj.get_token(buf)
        self.assert_(tok==1)
        tok = lexer_obj.get_token(buf)
        self.assert_(tok == 1)

        return
    pass

class asm_full_20(lex_test):
    def runTest(self):
        lexer_obj = pytoken.lexer()
        lexer_obj.add_pattern("a", 1)
        lexer_obj.add_pattern(" ")
        lexer_obj.compile_to_machine_code(debug=False)

        if 0:
            print "NFA:"
            print lexer_obj.nfa_obj
            print "DFA:"
            print lexer_obj.dfa_obj
            #pytoken.print_instructions(lexer_obj.ir)

        buf = pytoken.lexer_state()
        buf.set_input("   a")

        tok = lexer_obj.get_token(buf)
        self.assert_(tok==1)
        return
    pass

class asm_full_21(lex_test):
    def runTest(self):
        lexer_obj = pytoken.lexer()
        lexer_obj.add_pattern("[0123456789]+", int)
        lexer_obj.add_pattern(" ")
        lexer_obj.compile_to_machine_code(debug=False)

        if 0:
            print "NFA:"
            print lexer_obj.nfa_obj
            print "DFA:"
            print lexer_obj.dfa_obj
            #pytoken.print_instructions(lexer_obj.ir)

        buf = pytoken.lexer_state()
        buf.set_input("   10 20 40")

        tok = lexer_obj.get_token(buf)
        self.assert_(tok==10)
        tok = lexer_obj.get_token(buf)
        self.assert_(tok==20)
        tok = lexer_obj.get_token(buf)
        self.assert_(tok==40)

        return
    pass

class asm_full_22(lex_test):
    def runTest(self):
        lexer_obj = pytoken.lexer()
        lexer_obj.add_pattern("b?", 1)
        lexer_obj.compile_to_machine_code(debug=False)

        if 0:
            print "NFA:"
            print lexer_obj.nfa_obj
            print "DFA:"
            print lexer_obj.dfa_obj
            #pytoken.print_instructions(lexer_obj.ir)

        buf = pytoken.lexer_state()
        buf.set_input("b")

        tok = lexer_obj.get_token(buf)
        self.assert_(tok==1)

        return
    pass

##############################################################

class full_directed01(lex_test):
    def runTest(self):
        obj = pytoken.lexer()
        obj.add_pattern(chr(244), 244)
        
        if 0:
            obj.compile_to_machine_code(debug=True)
        else:
            obj.build_nfa()
            if 0:
                print "NFA"
                print obj.nfa_obj
            obj.build_dfa()
            if 0:
                print "DFA"
                print obj.dfa_obj
            obj.compile_to_ir()
            if 0:
                print "IR"
                pytoken.print_instructions(obj.ir)
            if 0:
                l = pytoken.ir_to_asm_list_x86_32(obj.ir)
                print "ASM"
                pytoken.print_instructions(l)
                r = pytoken.asm_list_x86_32_to_code(l)
                obj.gettoken_obj = r
            else:
                debug_compile = False
                obj.gettoken_obj = pytoken.compile_to_x86_32(obj.ir, debug_compile)

        buf = pytoken.lexer_state()
        buf.set_input(chr(244))
        tok = obj.get_token(buf)
        self.assert_(tok == 244)
        return
    pass

class full_directed02(lex_test):
    def runTest(self):
        obj = pytoken.lexer()
        obj.add_pattern(chr(244), 244)
        
        if 0:
            obj.compile_to_machine_code(debug=True)
        else:
            obj.build_nfa()
            if 0:
                print "NFA"
                print obj.nfa_obj
            obj.build_dfa()
            if 0:
                print "DFA"
                print obj.dfa_obj
            obj.compile_to_ir()
            tmp = []
            for tup in obj.ir.instructions:
                tmp.append(tup)
                for n in range(500):
                    tmp.append((pytoken.IR_NOP,))
            obj.ir.instructions = tmp
            if 0:
                print "IR"
                pytoken.print_instructions(obj.ir)
            if 0:
                l = pytoken.ir_to_asm_list_x86_32(obj.ir)
                print "ASM"
                pytoken.print_instructions(l)
                r = pytoken.asm_list_x86_32_to_code(l)
                obj.gettoken_obj = r
            else:
                debug_compile = False
                obj.gettoken_obj = pytoken.compile_to_x86_32(obj.ir, debug_compile)

        buf = pytoken.lexer_state()
        buf.set_input(chr(244))
        tok = obj.get_token(buf)
        self.assert_(tok == 244)
        return
    pass

class full_directed03(lex_test):
    def runTest(self):
        #escape.print_gdb_info()
        #time.sleep(10)
        for n_nops in (0, 256, 512, 1024, 4096):
            sys.stdout.flush()
            obj = pytoken.lexer()
            for code in range(1, 255):
                if chr(code) in (".", "(", ")", "[", "]", "*", "?",
                                 "+", "\\", "|"):
                    regex = "\\" + chr(code)
                    obj.add_pattern(regex, code)
                else:
                    obj.add_pattern(chr(code), code)
        
            sys.stdout.flush()
            obj.build_nfa()
            sys.stdout.flush()
            if 0:
                print "NFA"
                print obj.nfa_obj
            obj.build_dfa()
            sys.stdout.flush()
            if 0:
                print "DFA"
                print obj.dfa_obj
            obj.compile_to_ir()
            sys.stdout.flush()
            for n in range(n_nops):
                obj.ir.instructions.insert(0, ((pytoken.IR_NOP, None, None)))
            if 0:
                print "IR"
                pytoken.print_instructions(obj.ir)
            debug_compile = False
            obj.gettoken_obj = pytoken.compile_to_x86_32(obj.ir, debug_compile)
            sys.stdout.flush()
            addr = obj.gettoken_obj.get_start_addr()
            sys.stdout.flush()

            for targ in range(1, 255):
                #print "targ byte=%d" % targ
                #sys.stdout.flush()
                buf = pytoken.lexer_state()
                buf.set_input(chr(targ))
                tok = obj.get_token(buf)
                self.assert_(tok == targ)
        return
    pass

class full_directed04(lex_test):
    def runTest(self):
        obj = pytoken.lexer()
        buf_list = []
        for code in range(ord('a'), ord('z')+1):
            obj.add_pattern(chr(code), code)
            buf = pytoken.lexer_state()
            buf.set_input(chr(code))
            buf_list.append(buf)
        obj.compile_to_machine_code()
        
        exp = 'a'
        for buf in buf_list:
            tok = obj.get_token(buf)
            self.assert_(tok == ord(exp))
            exp = chr(ord(exp) + 1)
        return
    pass

class full_rand01(lex_test):
    def runTest(self):
        obj = pytoken.lexer()
        for code in range(ord('a'), ord('z') + 1):
            ch = chr(code)
            obj.add_pattern(ch, code)
        obj.compile_to_machine_code()

        rgen = random.Random()
        rgen.seed(42)
        
        txt_len = 1000
        txt = [chr(ord('a') + rgen.randint(0,25)) for idx in range(txt_len)]
        txt = "".join(txt)
        
        buf = pytoken.lexer_state()
        buf.set_input(txt)
        
        for idx in range(txt_len):
            tok = obj.get_token(buf)
            ch = txt[idx]
            self.assert_(tok == ord(ch))

        return
    pass

class full_rand02(lex_test):
    def runTest(self):
        obj = pytoken.lexer()
        for code in range(1, 256):
            ch = chr(code)
            if ch in ('(', ')', '[', ']', '\\', '*', '?', '+', '.', '|'):
                regex = '\\' + ch
            elif ch == '\n':
                regex = '\\n'
            elif ch == '\t':
                regex = '\\t'
            elif ch == '\r':
                regex = '\\r'
            else:
                regex = ch
            #print repr(regex), "-->", code
            obj.add_pattern(regex, code)
        obj.compile_to_machine_code()

        rgen = random.Random()
        rgen.seed(2)
        
        txt_len = 1000
        txt = [chr(rgen.randint(1,255)) for idx in range(txt_len)]
        txt = "".join(txt)
        
        buf = pytoken.lexer_state()
        buf.set_input(txt)
        
        for idx in range(txt_len):
            tok = obj.get_token(buf)
            ch = txt[idx]
            self.assert_(tok == ord(ch))

        return
    pass

class full_rand03(lex_test):
    def runTest(self):
        obj = pytoken.lexer()
        for ch_code in range(ord('a'), ord('z') + 1):
            pat = 'a' + chr(ch_code)
            obj.add_pattern(pat, ch_code)
        obj.compile_to_machine_code()

        rgen = random.Random()
        rgen.seed(10)
        expected = []
        txt = []
        for tnum in range(500):
            rand_char = rgen.randint(ord('a'), ord('z'))
            txt.append('a' + chr(rand_char))
            expected.append(rand_char)
        txt = "".join(txt)

        buf = pytoken.lexer_state()
        buf.set_input(txt)
        
        while expected:
            tok = obj.get_token(buf)
            exp = expected.pop(0)
            self.assert_(tok == exp)

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
            print "lstate=0x%x buf=0x%x size=%d next_char=0x%x" % tup
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

class assembler45(lex_test):
    def runTest(self):
        asm_list = [
            ("l1", "nop", None),
            (None, "jmp", "l1")
            ]

        code = pytoken.asm_list_x86_32_to_code(asm_list)
        asm_bytes = code.get_code()
        self.assert_(len(asm_bytes) == 3)
        self.assert_(ord(asm_bytes[0]) == 0x90)

        self.assert_(ord(asm_bytes[1]) == 0xEB)
        self.assert_(ord(asm_bytes[2]) == 0xFD)

        return
    pass

class assembler46(lex_test):
    def runTest(self):
        asm_list = [
            ("l1", "nop", None),
            (None, "nop", None),
            (None, "nop", None),
            (None, "jmp", "l1")
            ]

        code = pytoken.asm_list_x86_32_to_code(asm_list)
        asm_bytes = code.get_code()
        self.assert_(len(asm_bytes) == 5)
        self.assert_(ord(asm_bytes[0]) == 0x90)
        self.assert_(ord(asm_bytes[1]) == 0x90)
        self.assert_(ord(asm_bytes[2]) == 0x90)

        self.assert_(ord(asm_bytes[3]) == 0xEB)
        self.assert_(ord(asm_bytes[4]) == 0xFB)

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
class interface01(lex_test):
    def runTest(self):
        obj = pytoken.lexer()
        obj.add_pattern("a", 1)
        obj.compile_to_machine_code()
        
        got_exception = False
        try:
            tok = obj.get_token()
        except Exception:
            got_exception = True
        self.assert_(got_exception == True)
        return
    pass
        

##############################################################
class looper(lex_test):
    def runTest(self):
        print ""
        print "Starting long running looper test"

        sym_tab = globals()
        work = sym_tab.items()
        tnum = 0
        for n, sym in work:
            tnum += 1
            if type(sym) is not type:
                continue
            if not issubclass(sym, lex_test):
                continue
            if n in ("looper", "lex_test"):
                continue
            if 1:
                print "starting on %s (%d/%d)" % (n, tnum, len(work))
            tc = sym()
            try:
                nrefs = sys.gettotalrefcount()
            except AttributeError:
                nres = 0
            for i in range(10):
                if verbose_mode:
                    print "testing num", i
                if hasattr(tc, "setUp"):
                    tc.setUp()
                tc.runTest()
                if hasattr(tc, "tearDown"):
                    tc.tearDown()
                try:
                    nrefs2 = sys.gettotalrefcount()
                except AttributeError:
                    nrefs2 = 0
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
               "assembler", "full_rand", "full_directed",
               "errtest", "regtest", "uval", "rand_dfa", "rre2_dfa"]
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
        assert match != None

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

def run_some_tests(argv):
    global verbose_mode

    if len(argv) > 1 and argv[1] == "-v":
        verbose_mode = True
        argv.pop(1)

    if len(argv) > 1 and argv[1] == "-loop":
        symtab = globals()
        suite = make_suite([argv[3]])
        ntests = int(argv[2])
        for c in xrange(ntests):
            print "on iter", c
            print "fill_addr = 0x%x" % escape.get_fill_caller_addr()
            if c == 5:
                escape.print_gdb_info()
            runner = unittest.TextTestRunner()
            runner.run(suite)

        print "Done"
    else:
        if len(argv) > 1:
            suite = make_suite(argv[1:])
        else:
            tmp = get_all_tests()
            suite = make_suite(tmp)
        runner = unittest.TextTestRunner()
        runner.run(suite)
    return

if __name__=="__main__":
    verbose_mode = False
    run_some_tests(sys.argv)
