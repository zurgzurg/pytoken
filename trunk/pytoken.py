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
import sys
import os
import os.path
import re
import dl
import pdb

import escape

code        = escape.code
lexer_state = escape.lexer_state

##########################################################################
class fsa(object):
    def __init__(self, lexer):
        self.init_state       = lexer.get_new_state()
        self.trans_tbl        = {}
        self.states           = [self.init_state]
        self.lexer            = lexer
        self.accepting_states = []
        return

    def get_new_state(self):
        result = self.lexer.get_new_state()
        self.states.append(result)
        return result

    def add_edge(self, cur_state, ch, next_state):
        k = (cur_state, ch) 
        if k not in self.trans_tbl:
            self.trans_tbl[k] = []
        l = self.trans_tbl[k]
        if next_state not in l:
            l.append(next_state)
        return

    def set_accepting_state(self, state):
        if state not in self.accepting_states:
            self.accepting_states.append(state)
        return

    ##
    ## debug routines
    ##
    def __str__(self):
        result = "init=%s\n" % str(self.init_state)
        for k,v in self.trans_tbl.iteritems():
            result = result + str(k) + "->" + str(v) + "\n"
        result = result + "accepting=" + str(self.accepting_states) + "\n"
        return result

    pass

##########################################################################
class nfa(fsa):
    def __init__(self, lexer, txt=None):
        super(nfa, self).__init__(lexer)

        if txt is not None:
            assert len(txt) == 1
            s2 = self.get_new_state()
            self.add_edge(self.init_state, txt, s2)
            self.set_accepting_state(s2)

        pass

    ##
    ## merge related funcs
    ##
    def copy_edges(self, other_nfa):
        for (st, ch), v in other_nfa.trans_tbl.iteritems():
            for dst in v:
                self.add_edge(st, ch, dst)
        return

    ##
    ## dfa construction support
    ##
    def e_closure(self, start_list):
        if type(start_list) not in (list, tuple):
            result = self.e_closure_1(start_list)
        else:
            result = []
            for s in start_list:
                tmp = self.e_closure_1(s)
                for s2 in tmp:
                    if s2 not in result:
                        result.append(s2)
        result.sort()
        return tuple(result)

    def e_closure_1(self, start):
        result = []
        todo = [start]
        while todo:
            st = todo.pop()
            if st in result:
                continue
            result.append(st)
            try:
                slist = self.trans_tbl[(st, None)]
            except KeyError:
                slist = []
            todo.extend(slist)
        return result

    ###
    def move(self, st_list, ch):
        if type(st_list) is not list and type(st_list) is not tuple:
            result = self.move_1(st_list, ch)
        else:
            result = []
            for s in st_list:
                tmp = self.move_1(s, ch)
                for s2 in tmp:
                    if s2 not in result:
                        result.append(s2)
        result.sort()
        return tuple(result)

    def move_1(self, st, ch):
        result = []
        try:
            slist = self.trans_tbl[(st, ch)]
        except KeyError:
            slist = []
        for s in slist:
            if s not in result:
                result.append(s)
            tmp = self.e_closure_1(s)
            for s2 in tmp:
                if s2 not in result:
                    result.append(s2)
        return result

    ##
    ## The Subset Construction Algorithm
    ## 
    ## 1. Create the start state of the DFA by taking the e-closure
    ##    of the start state of the NFA.
    ##
    ## 2. Perform the following for the new DFA state:
    ##
    ##    For each possible input symbol:
    ##    1. Apply move to the newly-created state and the input symbol;
    ##       this will return a set of states.
    ##    2. Apply the e-closure to this set of states, possibly resulting
    ##       in a new set.
    ##
    ##    This set of NFA states will be a single state in the DFA.
    ##
    ## 3. Each time we generate a new DFA state, we must apply
    ##    step 2 to it. The process is complete when applying step 2
    ##    does not yield any new states.
    ## 4. The finish states of the DFA are those which contain
    ##    any of the finish states of the NFA.
    ##
    def maybe_mark_nfa_accepting_state(self, state_list, nfa, nfa_state):
        slist = [s for s in self.accepting_states if s in state_list]
        if len(slist) == 0:
            return

        the_state = slist.pop(0)
        for s in slist:
            if s.priority < the_state.priority:
                the_state = s

        nfa_state.priority = the_state.priority
        nfa_state.user_action = the_state.user_action
        nfa.set_accepting_state(nfa_state)
        return

    def convert_to_dfa(self):
        result = dfa(self.lexer)
        all_ch = [chr(i) for i in range(127)]

        seen = {}
        start = self.e_closure(self.init_state)
        work = [start]
        seen[start] = result.init_state

        self.maybe_mark_nfa_accepting_state(start, result, result.init_state)

        while work:
            s = work.pop()
            cur_state = seen[s]
            for ch in all_ch:
                s2 = self.move(s, ch)
                s2 = self.e_closure(s2)

                if not s2 or len(s2)==0:
                    continue

                if s2 not in seen:
                    dst = result.get_new_state()
                    seen[s2] = dst
                    work.append(s2)
                    self.maybe_mark_nfa_accepting_state(s2, result, dst)
                else:
                    dst = seen[s2]

                result.add_edge(cur_state, ch, dst)
                cur_state.out_chars.append(ch)
                    
        return result
        

    pass

##########################################################################
class dfa(fsa):
    def __init__(self, lexer):
        super(dfa, self).__init__(lexer)
        self.has_end_of_buf_edges = False
        return
    pass

##########################################################################
def do_nfa_ccat(lexer, nfa1, nfa2):
    result = nfa(lexer)
    result.copy_edges(nfa1)
    result.copy_edges(nfa2)

    result.add_edge(result.init_state, None, nfa1.init_state)

    for s1 in nfa1.accepting_states:
        result.add_edge(s1, None, nfa2.init_state)

    for s2 in nfa2.accepting_states:
        result.set_accepting_state(s2)

    return result

def do_nfa_pipe(lexer, nfa1, nfa2):
    result = nfa(lexer)
    result.copy_edges(nfa1)
    result.copy_edges(nfa2)

    for s1 in nfa1.accepting_states:
        result.set_accepting_state(s1)
    for s2 in nfa2.accepting_states:
        result.set_accepting_state(s2)

    result.add_edge(result.init_state, None, nfa1.init_state)
    result.add_edge(result.init_state, None, nfa2.init_state)
    return result


###################################################################
###################################################################
LPAREN   = 1
RPAREN   = 2
LBRACKET = 3
RBRACKET = 4
PIPE     = 5
PLUS     = 6
STAR     = 7
TEXT     = 8
CCAT     = 9

char2sym = {
    '('  : LPAREN,
    ')'  : RPAREN,
    '['  : LBRACKET,
    ']'  : RBRACKET,
    '|'  : PIPE,
    '+'  : PLUS,
    '*'  : STAR
    }

sym2name = {
    LPAREN   : "LP",
    RPAREN   : "RP",
    LBRACKET : "LB",
    RBRACKET : "RB",
    PIPE     : "PIPE",
    PLUS     : "PLUS",
    STAR     : "STAR",
    TEXT     : "TEXT",
    CCAT     : "CCAT"
    }

sym2char = {
    LPAREN   : "(",
    RPAREN   : ")",
    LBRACKET : "[",
    RBRACKET : "]",
    PIPE     : "|",
    PLUS     : "+",
    STAR     : "*",
    TEXT     : None,
    CCAT     : None
    }

# larger numbers have higher precendence
sym2prec = {
    CCAT   : 1,
    PIPE   : 1,
    STAR   : 2,
    LPAREN : 3,
    RPAREN : 3
    }
    

all_special_syms = (LPAREN, RPAREN, LBRACKET, RBRACKET, PIPE,
                    PLUS, STAR, CCAT)

class fsa_state(object):
    def __init__(self, lexer):
        self.lexer         = lexer
        self.num           = lexer.next_avail_state
        self.out_chars     = []
        self.label         = None
        self.is_accepting  = False
        self.user_action   = None
        self.priority      = None
        lexer.next_avail_state += 1
        pass
    def __str__(self):
        return self.__repr__()
    def __repr__(self):
        if self.user_action:
            return "state_%d_action=%d" % (self.num, self.user_action)
        return "state_%d" % self.num
    pass

class lexer(object):
    ACTION_FOUND_UNEXP    = 0
    ACTION_FOUND_EOB      = 1
    ACTION_ERR_IN_FILL    = 2
    ACTION_BAD_FILL_RET   = 3

    FILL_RESULT_NO_NEW_DATA    = 0
    FILL_RESULT_NEW_DATA_READY = 1
    FILL_RESULT_ERROR          = 2

    def __init__(self):
        self.pats             = []
        self.actions          = [self.runtime_fill_buffer,
                                 self.runtime_unhandled_input,
                                 "EOB",
                                 self.runtime_internal_error]

        self.next_avail_state = 1

        self.nfa_obj          = None
        self.dfa_obj          = None
        self.ir               = None
        self.code_obj         = None

        return

    #######################################
    #######################################
    #######################################
    ##
    ## main user interface
    ##
    #######################################
    #######################################
    #######################################
    def add_pattern(self, pat, action):
        """Add a pattern to the lexer.
        The pattern is a regular expression, currently the only
        meta characters supported are * [] and |. The action argument
        can be anything. If action is None then those tokens are discarded
        by the lexer. If the action is a non-callable then when that
        pattern is found it will be returned, for callable actions, the
        action will be called (args??) and the return value from the
        callable will be returned."""
        idx = len(self.actions)
        self.actions.append(action)
        self.pats.append((pat, idx))
        return

    def build_nfa(self):
        priority = 1
        nfa_list = []
        for p, a in self.pats:
            postfix = self.parse_as_postfix(p)
            nfa_obj = self.postfix_to_nfa(postfix)
            for st in nfa_obj.accepting_states:
                st.user_action = a
                st.priority    = priority
            nfa_list.append(nfa_obj)
            priority += 1

        the_nfa = nfa_list.pop(0)
        while nfa_list:
            tmp = nfa_list.pop(0)
            the_nfa = do_nfa_pipe(self, the_nfa, tmp)
        self.nfa_obj = the_nfa
        return the_nfa

    def build_dfa(self):
        self.dfa_obj = self.nfa_obj.convert_to_dfa()
        return self.dfa_obj

    def compile_to_machine_code(self, debug=False):
        self.build_nfa()
        self.build_dfa()
        self.compile_to_ir()
        self.code_obj = compile_to_x86_32(self.ir, debug)
        return self.code_obj

    def get_token(self, lstate):
        assert self.code_obj is not None
        idx = self.code_obj.get_token(lstate)
        assert type(idx) is int and idx >= 0 and idx < len(self.actions)
        action = self.actions[idx]
        if callable(action):
            r = action(lstate)
        else:
            r = action
        return r

    ####################################################
    ####################################################
    ##
    ## intermediate representation generator
    ##
    ## The code object should be called like this
    ## code_obj_addr(code_obj, lex_state)
    ##
    ## ----------------------------------------
    ## return value protocol = int
    ##
    ##  0 --> unhandled input
    ##  1 --> end of buffer
    ##  2 --> error in fill
    ##  3 --> bad return code from fill
    ##  3 --> user action
    ##  4 --> user action
    ##  5 --> ...
    ##
    ## The return value from the lexer is always an integer, which
    ## is used as an index into the self.actions list to find out
    ## what actual action to perform. The first two entries in the
    ## actions list are fill buffer and unhandled input. Therefore
    ## if the lexer returns 0 a fill buffer operation is performed
    ## and a 1 indicates an unmatched input.
    ##
    ##
    ## end of buffer func -- the fill function
    ## ---------------------------------------
    ## called when NUL chars are found
    ##
    ## return values:
    ##
    ## 1 = got new data, pointers have been adjusted
    ##     and the buffer may have moved
    ##
    ## 2 = no new data available, all pointers are unchanged
    ##
    ## 3 = error happened
    ##
    ##   ???? where is a real NUL char in the user data
    ##        handled?
    ##
    ####################################################
    ####################################################
    def compile_to_ir(self):
        self.ir = ir_code(self)
        ir = self.ir
        ir.make_std_vars()
        for i, s in enumerate(self.dfa_obj.states):
            s.label = "lab_%d" % i

        ## initial code sequence
        ##
        ##   load second arg
        ##   add offset to get address of lex_state->next_char_ptr
        ##   deref ptr to get actual next_char_ptr
        ##
        ir.add_ir_com("main")
        ir.add_ir_gparm(ir.lstate_ptr, 1)
        ir.add_ir_set(ir.saved_valid, 0)

        ir.add_ir_com("get string ptr")
        ir.add_ir_set(ir.tmp_var, ir.lstate_ptr)
        ir.add_ir_add(ir.tmp_var, ir.char_ptr_offset)
        ir.add_ir_ldw(ir.str_ptr_var, ir.make_indirect_var(ir.tmp_var))

        ir.add_ir_com("handle token start")
        ir.add_ir_set(ir.token_start_ptr, ir.lstate_ptr)
        ir.add_ir_add(ir.token_start_ptr, ir.token_start_offset)
        ir.add_ir_stw(ir.make_indirect_var(ir.token_start_ptr), ir.str_ptr_var)

        for s in self.dfa_obj.states:
            tmp = self.compile_one_node(s)
            ir.instructions.extend(tmp)

        return self.ir

    def compile_one_node(self, state):
        ir = self.ir
        lst = []

        ir.ladd_ir_com(lst, "begin " + str(state))
        ir.ladd_ir_label(lst, state.label)
        
        ## 1. if this is an accepting state
        ##      save the char pointer
        ##      save return value
        ##      set saved data valid flag
        if state.user_action:
            ir.ladd_ir_com(lst, "accepting state")
            ir.ladd_ir_com(lst, "save the char pointer")
            ir.ladd_ir_set(lst, ir.saved_ptr, ir.str_ptr_var)
            ir.ladd_ir_com(lst, "save the return value")
            ir.ladd_ir_set(lst, ir.saved_result, state.user_action)
            ir.ladd_ir_com(lst, "set saved data flag")
            ir.ladd_ir_set(lst, ir.saved_valid, 1)

        ## 2. load cur char
        ##    advance and save char pointer
        ir.ladd_ir_ldb(lst, ir.data_var, ir.make_indirect_var(ir.str_ptr_var))
        ir.ladd_ir_add(lst, ir.str_ptr_var, 1)
        
        ## 3. branch to appopriate state based on char
        ##
        for ch in state.out_chars:
            k = (state, ch)
            dst = self.dfa_obj.trans_tbl[k]
            assert len(dst) == 1
            dst = dst[0]
            ir.ladd_ir_cmp(lst, ir.data_var, ord(ch))
            ir.ladd_ir_beq(lst, dst.label)

        ## 4. if control flow reaches this point then the current
        ##    char does not match any next state - so either we
        ##    have an error (illegal input char) or we hit EOB
        ##
        ## XXX - not handling case of user patterns
        ## matching EOB chars
        lab_eob = state.label + "_found_eob"
        lab_bad_char       = state.label + "_bad_char"
        lab_fill_err       = state.label + "_fill_err"
        lab_fill_bad_ret   = state.label + "_fill_bad_ret"
        lab_real_eob       = state.label + "_real_eob"
        lab_fill_no_data   = state.label + "_fill_no_data"

        ## if NULL then do EOB work
        ir.ladd_ir_com(lst, "no match on cur char")
        ir.ladd_ir_cmp(lst, ir.data_var, 0)
        ir.ladd_ir_beq(lst, lab_eob)
        
        ##  the current char is unmatched -- and is not NULL
        ##
        ##  if token_found_flag is set
        ##    set token end ptr to saved value
        ##    save cur char pointer
        ##    return saved result
        ##  else
        ##    return error condition
        ##
        ir.ladd_ir_com(lst, "unmatched char")
        ir.ladd_ir_cmp(lst, ir.saved_valid, 1)
        ir.ladd_ir_bne(lst, lab_bad_char)

        ir.ladd_ir_com(lst, "unmatched char, but earlier match")
        ir.ladd_ir_set(lst, ir.str_ptr_var, ir.saved_ptr)
        ir.ladd_ir_set(lst, ir.tmp_var, ir.lstate_ptr)
        ir.ladd_ir_add(lst, ir.tmp_var, ir.char_ptr_offset)
        ir.ladd_ir_stw(lst, ir.make_indirect_var(ir.tmp_var),
                       ir.str_ptr_var)
        ir.ladd_ir_ret(lst, ir.saved_result)

        ir.ladd_ir_com(lst, "hit unmatched char")
        ir.ladd_ir_label(lst, lab_bad_char)
        ir.ladd_ir_ret(lst, lexer.ACTION_FOUND_UNEXP)

        # cur char is NULL - call fill routine
        # but save char pointer and reload on return
        # since the fill routine might reallocate the buffer
        # undo pointer increment so pointer points to the first null char
        ir.ladd_ir_label(lst, lab_eob)
        ir.ladd_ir_com(lst, "found eob char")
        ir.ladd_ir_add(lst, ir.str_ptr_var, -1)
        ir.ladd_ir_set(lst, ir.tmp_var, ir.lstate_ptr)
        ir.ladd_ir_add(lst, ir.tmp_var, ir.char_ptr_offset)
        ir.ladd_ir_stw(lst, ir.make_indirect_var(ir.tmp_var), ir.str_ptr_var)
        ir.ladd_ir_call(lst, ir.fill_status, ir.fill_caller_addr,ir.lstate_ptr)

        # 1 = got more data
        # need to update various lexer state pointers
        ir.ladd_ir_cmp(lst, ir.fill_status, 1)
        ir.ladd_ir_bne(lst, lab_fill_no_data)

        ir.ladd_ir_com(lst, "after fill - got more data")
        ir.ladd_ir_set(lst, ir.tmp_var, ir.lstate_ptr)
        ir.ladd_ir_add(lst, ir.tmp_var, ir.char_ptr_offset)
        ir.ladd_ir_ldw(lst, ir.str_ptr_var, ir.make_indirect_var(ir.tmp_var))

        ir.ladd_ir_set(lst, ir.token_start_ptr, ir.lstate_ptr)
        ir.ladd_ir_add(lst, ir.token_start_ptr, ir.token_start_offset)

        ir.ladd_ir_ldb(lst, ir.data_var, ir.make_indirect_var(ir.str_ptr_var))
        ir.ladd_ir_br(lst, state.label)


        # 2 = no more data avail
        ir.ladd_ir_label(lst, lab_fill_no_data)
        ir.ladd_ir_cmp(lst, ir.fill_status, 2)
        ir.ladd_ir_bne(lst, lab_fill_err)
        ir.ladd_ir_cmp(lst, ir.saved_valid, 1)
        ir.ladd_ir_bne(lst, lab_real_eob)

        ir.ladd_ir_com(lst, "no data after fill - but have valid result")
        ir.ladd_ir_set(lst, ir.str_ptr_var, ir.saved_ptr)
        ir.ladd_ir_ret(lst, ir.saved_result)
        
        ir.ladd_ir_com(lst, "no data after fill - no valid result")
        ir.ladd_ir_label(lst, lab_real_eob)
        ir.ladd_ir_ret(lst, lexer.ACTION_FOUND_EOB)

        # 3 = something went wrong in fill
        ir.ladd_ir_label(lst, lab_fill_err)
        ir.ladd_ir_cmp(lst, ir.fill_status, 3)
        ir.ladd_ir_bne(lst, lab_fill_bad_ret)
        ir.ladd_ir_ret(lst, lexer.ACTION_ERR_IN_FILL)

        # 4 = last case = fill returns illegal val
        ir.ladd_ir_label(lst, lab_fill_bad_ret)
        ir.ladd_ir_ret(lst, lexer.ACTION_BAD_FILL_RET)

        return lst

    #######################################
    ##
    ## runtime support
    ##
    #######################################
    def runtime_fill_buffer(self, lstate):
        return

    def runtime_unhandled_input(self, lstate):
        raise RuntimeError, "no rule to match input"

    def runtime_internal_error(self, lstate):
        raise RuntimeError, "got error code from code object"

    #######################################
    ##
    ## helpers / utils
    ##
    #######################################
    def get_new_state(self):
        return fsa_state(self)

    ######################################
    ##
    ## NFA stuff
    ##
    ######################################
    def postfix_to_nfa(self, postfix_expr):
        stack = []
        for sym in postfix_expr:
            if type(sym) is str:
                nfa1 = nfa(self, sym)
                stack.append(nfa1)
            elif sym is CCAT:
                nfa2 = stack.pop()
                nfa1 = stack.pop()
                nfa3 = do_nfa_ccat(self, nfa1, nfa2)
                stack.append(nfa3)
            elif sym is PIPE:
                nfa2 = stack.pop()
                nfa1 = stack.pop()
                nfa3 = do_nfa_pipe(self, nfa1, nfa2)
                stack.append(nfa3)
            elif sym is STAR:
                nfa1 = stack.pop()
                for st in nfa1.accepting_states:
                    nfa1.add_edge(st, None, nfa1.init_state)
                    nfa1.add_edge(nfa1.init_state, None, st)
                stack.append(nfa1)
            else:
                assert None, "Bad sym" + str(sym)
        return stack[0]

    #######################################
    ## 
    ## postfix creator
    ## 
    ## Dijkstras shunting yard algorithm
    ##
    ## while there are tokens
    ##   read a token
    ##
    ##   if token is a letter add to output
    ##
    ##   If the token is an operator, o1, then:
    ##
    ##      while there is an op, o2, at the top of the stack, and either
    ##            o1 is associative or left-associative and its precedence
    ##            is less than (lower precedence) or equal to that of o2,
    ##            or
    ##            o1 is right-associative and its precedence is less than
    ##            (lower precedence) that of o2,
    ##
    ##        pop o2 off the stack, onto the output queue;
    ##
    ##      push o1 onto the operator stack.
    ##
    ##   if token is left paren push onto operator stack
    ## 
    ##   if token is right paren
    ##
    ##     until token at top of operator stack is a left paren pop
    ##     ops off the stack and to output
    ##
    ##     pop left paren off stack but not onto output
    ##
    ##     if stack runs out then parens were unbalanced
    ##
    ## when no more tokens
    ##
    ##  if op on top of stack is a paren then parens were mismatched
    ##
    ##  pop ops off the stack and onto output
    ##
    #######################################
    def pop_op(self, op1, op2):
        assert op1 is not None
        assert op2 is not None
        if op2 == LPAREN:
            return False
        if op1 in (CCAT,PIPE) and sym2prec[op1] <= sym2prec[op2]:
            return True
        return False

    def parse_as_postfix(self, pat):
        result  = []
        operators = []
        tok_list = self.tokenize_pattern(pat)
        while tok_list:
            tok = tok_list.pop(0)
            if type(tok) is str:
                result.append(tok)
            elif tok == RPAREN:
                while True:
                    if len(operators) == 0:
                        raise RuntimeError, "Unbalanced parens"
                    op = operators.pop()
                    if op == LPAREN:
                        break
                    result.append(op)
            elif tok == LPAREN:
                operators.append(tok)
            else:
                assert tok in (PIPE, STAR, CCAT)

                while operators and self.pop_op(tok, operators[-1]):
                    tmp = operators.pop()
                    result.append(tmp)
                operators.append(tok)

        while operators:
            op = operators.pop()
            result.append(op)

        return result

    #######################################
    ##
    ## tokenizer
    ##
    #######################################
    def tokenize_pattern(self, pat):
        result = []

        n_paren = 0
        special_chars = char2sym.keys()
        while len(pat) > 0:
            ch = pat[0]
            pat = pat[1:]

            if ch == '\\':
                ch  = pat[0]
                pat = pat[1:]
                result.append(ch)

            elif ch == '[':
                if len(result) > 0 and type( result[-1] ) is str:
                    result.append(CCAT)
                result.append(LPAREN)
                need_pipe = False
                end_found = False
                while len(pat) > 0:
                    ch = pat[0]
                    pat = pat[1:]

                    if ch == ']':
                        end_found = True
                        result.append(RPAREN)
                        break
                    else:
                        if need_pipe:
                            result.append(PIPE)
                        result.append(ch)
                        need_pipe = True
                    pass
                if not end_found:
                    raise RuntimeError, "'[' without matching ']'"

            elif ch in ('(', ')', '|', '*', '+'):
                if ch == '(':
                    n_paren += 1
                elif ch == ')':
                    n_paren -= 1

                if len(result) > 0 and ch == '(' and type( result[-1] ) is str:
                    result.append(CCAT)

                result.append(char2sym[ch])

            else:
                if len(result) > 0 and (type( result[-1] ) is str
                                        or result[-1] == RPAREN):
                    result.append(CCAT)
                result.append(ch)
            pass

        if n_paren != 0:
            raise RuntimeError, "Unbalanced parens found"
        return result

    pass

def struct_equal(s1, s2):
    if len(s1) != len(s2):
        return False
    n_items = len(s1)
    idx = 0
    while idx < n_items:
        s1_obj = s1[idx]
        s2_obj = s2[idx]
        idx += 1
                    
        if type(s1_obj) is not type(s2_obj):
            return False
        obj_type = type(s1_obj)

        if obj_type is str or obj_type is int:
            if s1_obj != s2_obj:
                return False
        else:
            assert obj_type is list or obj_type is tuple
            if not struct_equal(s1_obj, s2_obj):
                return False
        pass
    return True

def make_string_from_token_list(tlist):
    tmp = []
    for tok in tlist:
        if type(tok) is str:
            tmp.append(tok)
        else:
            tmp.append( sym2name[tok] )
    result = "[%s]" % ",".join(tmp)
    return result

###################################################################
###################################################################
##
## overall architecture
##
## regexps --> nfa --> dfa --> ir code --> x86 code
##
## ir code :    intermediate representation of machine code to
##              implement the state machine for the dfa
##              the code object has only pure executable code
##
## buffer:      text to be scanned + scanner state
##              buffer objects can be switched at will by user
##              code
##
###################################################################
###################################################################
##
## addressing modes: (var) -- var_indirect - use var as an address
## const - any integer - no worry about too large ints for now
## addr - any integer
##
## var     : string: var_<num>
## label   : string: lab_<num>  -- code label
## dlab    : string: dlab_<num> -- data label
##
IR_LABEL   =  0 # label
IR_DATA    =  1 # dlabel, string | dlabel, int 
IR_LDW     =  2 # var, addr  | var, (var) | var, dlab
IR_LDB     =  3 # var, addr  | var, (var) | var, dlab
IR_STW     =  4 # addr, var  | (var), var | dlab, var
IR_STB     =  5 # addr, var  | (var), var | dlab, var
IR_SET     =  6 # var, const | var, var
IR_CMP     =  7 # var, var   | var, const
IR_BEQ     =  8 # label
IR_BNE     =  9 # label
IR_BR      = 10 # label
IR_NOP     = 11 #
IR_ADD     = 12 # var, const | var, var
IR_RET     = 13 # var
IR_COM     = 14 # comment
IR_CALL    = 15 # var, addr, <arg>...<arg> | var, var, <arg>...<arg>
IR_GPARM   = 16 # var, <parm_num>

instr2txt = {
    IR_LABEL    : "label",
    IR_DATA     : "data",
    IR_LDW      : "ldw",
    IR_LDB      : "ldb",
    IR_STW      : "stw",
    IR_STB      : "stb",
    IR_SET      : "set",
    IR_CMP      : "cmp",
    IR_BEQ      : "beq",
    IR_BNE      : "bne",
    IR_BR       : "br",
    IR_NOP      : "nop",
    IR_ADD      : "add",
    IR_RET      : "ret",
    IR_COM      : "com",
    IR_CALL     : "call",
    IR_GPARM    : "gparm"
    }

ir_names = ['ir_label', 'ir_data',
               'ir_ldw', 'ir_ldb',
               'ir_stw', 'ir_stb',
               'ir_set',
               'ir_cmp', 'ir_beq', 'ir_bne', 'ir_br',
               'ir_nop',
               'ir_add',
               'ir_ret',
               'ir_com',
               'ir_call', 'ir_gparm']

####################################################

def ir_label(lab):
    assert_is_code_label(lab)
    return (IR_LABEL, lab)

def ir_data(dlab, val):
    assert_is_dlabel(dlab)
    return (IR_DATA, dlab, val)

def ir_ldw(dst, src):
    assert_is_var(dst)
    assert_is_addr_or_indirect_var_or_dlab(src)
    return (IR_LDW, dst, src)

def ir_ldb(dst, src):
    assert_is_var(dst)
    assert_is_addr_or_indirect_var_or_dlab(src)
    return (IR_LDB, dst, src)

def ir_stw(dst, src):
    assert_is_addr_or_indirect_var_or_dlab(dst)
    assert_is_var(src)
    return (IR_STW, dst, src)

def ir_stb(dst, src):
    assert_is_addr_or_indirect_var_or_dlab(dst)
    assert_is_var(src)
    return (IR_STB, dst, src)

def ir_set(var, val):
    assert_is_var(var)
    assert_is_var_or_const(val)
    return (IR_SET, var, val)

def ir_cmp(v1, v2):
    assert_is_var(v1)
    assert_is_var_or_const(v2)
    return (IR_CMP, v1, v2)

def ir_beq(lab):
    assert_is_code_label(lab)
    return (IR_BEQ, lab)

def ir_bne(lab):
    assert_is_code_label(lab)
    return (IR_BNE, lab)

def ir_br(lab):
    assert_is_code_label(lab)
    return (IR_BR, lab)

def ir_nop():
    return (IR_NOP,)

def ir_add(var, v):
    assert_is_var(var)
    assert_is_var_or_const(v)
    return (IR_ADD, var, v)

def ir_ret(var):
    assert_is_var_or_const(var)
    return (IR_RET, var)

def ir_com(txt):
    return (IR_COM, txt)

def ir_call(var, func, *args):
    assert_is_var(var)
    assert_is_addr_or_var(func)
    tmp = [IR_CALL, var, func]
    tmp.extend(args)
    return tuple(tmp)

def ir_gparm(var, pnum):
    assert_is_var(var)
    assert_is_const(pnum)
    return (IR_GPARM, var, pnum)

####################################################

def str_ir_label(tup):
    assert len(tup)==2 and tup[0]==IR_LABEL
    assert_is_code_label(tup[1])
    return "%s:" % tup[1]

def str_ir_data(tup):
    assert len(tup)==3 and tup[0]==IR_DATA
    assert_is_dlabel(tup[1])
    return "%s:  data: %s" % (tup[1], str(tup[2]))

def str_ir_ldw(tup):
    assert len(tup)==3
    assert tup[0]==IR_LDW
    assert_is_var(tup[1])
    assert_is_addr_or_indirect_var_or_dlab(tup[2])
    if type(tup[2]) is str:
        return "    ldw %s <-- %s" % (tup[1], tup[2])
    else:
        return "    ldw %s <-- %d" % (tup[1], tup[2])

def str_ir_ldb(tup):
    assert len(tup)==3 and tup[0]==IR_LDB
    assert_is_var(tup[1])
    assert_is_addr_or_indirect_var_or_dlab(tup[2])
    if type(tup[2]) is str:
        return "    ldb %s <-- %s" % (tup[1], tup[2])
    else:
        return "    ldb %s <-- %d" % (tup[1], tup[2])

def str_ir_stw(tup):
    assert len(tup)==3 and tup[0]==IR_STW
    assert_is_addr_or_indirect_var_or_dlab(tup[1])
    assert_is_var(tup[2])
    if type(tup[1]) is str:
        return "    stw %s <-- %s" % (tup[1], tup[2])
    else:
        return "    stw %s <-- %d" % (tup[1], tup[2])

def str_ir_stb(tup):
    assert len(tup)==3
    assert tup[0]==IR_STB
    assert_is_addr_or_indirect_var_or_dlab(tup[1])
    assert_is_var(tup[2])
    if type(tup[1]) is str:
        return "    stb %s <-- %s" % (tup[1], tup[2])
    else:
        return "    stb %s <-- %d" % (tup[1], tup[2])

def str_ir_set(tup):
    assert len(tup) == 3 and tup[0] == IR_SET
    assert_is_var(tup[1])
    assert_is_var_or_const(tup[2])
    if is_var(tup[2]):
        return "    set %s <-- %s" % (tup[1], tup[2])
    else:
        return "    set %s <-- %d" % (tup[1], tup[2])

def str_ir_cmp(tup):
    assert len(tup)==3 and tup[0]==IR_CMP
    assert_is_var(tup[1])
    assert_is_var_or_const(tup[2])
    if type(tup[2]) is str:
        return "    cmp %s, %s" % (tup[1], tup[2])
    else:
        return "    cmp %s, %d" % (tup[1], tup[2])

def str_ir_beq(tup):
    assert len(tup)==2 and tup[0]==IR_BEQ
    assert_is_code_label(tup[1])
    return "    beq %s" % (tup[1])

def str_ir_bne(tup):
    assert len(tup)==2 and tup[0]==IR_BNE
    assert_is_code_label(tup[1])
    return "    bne %s" % (tup[1])

def str_ir_br(tup):
    assert len(tup)==2 and tup[0]==IR_BR
    assert_is_code_label(tup[1])
    return "    br %s" % (tup[1])

def str_ir_nop(tup):
    assert len(tup)==1 and tup[0]==IR_NOP
    return "    nop"

def str_ir_add(tup):
    assert len(tup)==3 and tup[0]==IR_ADD
    assert_is_var(tup[1])
    assert_is_var_or_const(tup[2])
    if type(tup[2]) is str:
        return "    add %s <-- %s,%s" % (tup[1], tup[1], tup[2])
    else:
        return "    add %s <-- %s,%d" % (tup[1], tup[1], tup[2])

def str_ir_ret(tup):
    assert len(tup)==2 and tup[0]==IR_RET
    assert_is_var_or_const(tup[1])
    if type(tup[1]) is int:
        return "    ret %d" % tup[1]
    else:
        return "    ret %s" % tup[1]

def str_ir_com(tup):
    assert len(tup)==2 and tup[0]==IR_COM
    return "#%s" % tup[1]

def str_ir_call(tup):
    assert tup[0]==IR_CALL
    assert_is_var(tup[1])
    dst  = tup[1]
    func = tup[2]
    tmp = [str(item) for item in tup[3:]]
    args = ", ".join(tmp)
    if is_var(func):
        return "    call %s <-- %s(%s)" % (dst, func, args)
    return "    call %s <-- %x(%s)" % (dst, func, args)

def str_ir_gparm(tup):
    assert len(tup)==3 and tup[0]==IR_GPARM
    assert_is_var(tup[1])
    assert_is_const(tup[2])
    return "    gparm %s <-- parm<%d>" % (tup[1], tup[2])

instr2pfunc = {
    IR_LABEL    : str_ir_label,
    IR_DATA     : str_ir_data,
    IR_LDW      : str_ir_ldw,
    IR_LDB      : str_ir_ldb,
    IR_STW      : str_ir_stw,
    IR_STB      : str_ir_stb,
    IR_SET      : str_ir_set,
    IR_CMP      : str_ir_cmp,
    IR_BEQ      : str_ir_beq,
    IR_BNE      : str_ir_bne,
    IR_BR       : str_ir_br,
    IR_NOP      : str_ir_nop,
    IR_ADD      : str_ir_add,
    IR_RET      : str_ir_ret,
    IR_COM      : str_ir_com,
    IR_CALL     : str_ir_call,
    IR_GPARM    : str_ir_gparm
    }

####################################################
def is_var(r):
    if type(r) is str and r.startswith("var_"):
        return True
    return False

def is_indirect_var(r):
    if type(r) is str and r.startswith("(var_") and r.endswith(")"):
        return True
    return False

def is_num(val):
    if type(val) in (int,long):
        return True
    return False

def is_data_label(lab):
    if type(lab) is str and lab.startswith("dlab_"):
        return True
    return False

def is_code_label(lab):
    if type(lab) is str and lab.startswith("lab_"):
        return True
    return False

def is_byte(v):
    if type(v) is not int:
        return False
    if (v >= -128 and v <= 255):
        return True
    return False
    
#################

def assert_is_var(r):
    assert is_var(r)
    return

def assert_is_addr_or_indirect_var_or_dlab(arg):
    assert is_num(arg) \
           or is_indirect_var(arg) \
           or is_data_label(arg)
    return

def assert_is_code_label(l):
    assert is_code_label(l)
    return

def assert_is_data_label(l):
    assert is_data_label(l)
    return

def assert_is_var_or_const(r):
    assert (type(r) is str and r.startswith("var_")) or is_num(r)
    return

def assert_is_const(r):
    assert is_num(r)
    return

def assert_is_addr_or_var(v):
    assert is_num(v) or is_var(v)
    return
    
####################################################

def assert_is_byte(v):
    assert is_byte(v)
    return

####################################################

def dereference_indirect_var(r):
    assert is_indirect_var(r)
    return r[1:-1]

####################################################
def print_instructions(arg):
    if type(arg) is list:
        tmp_list = arg
    elif isinstance(arg, ir_code):
        tmp_list = arg.instructions
    elif isinstance(arg, escape.code):
        n = len(arg)
        tmp_list = [arg[i] for i in xrange(n)]
    else:
        assert type(arg) is tuple
        tmp_list = [arg]

    idx = 0
    for idx, obj in enumerate(tmp_list):
        if type(obj) is tuple or type(obj) is list:
            op = obj[0]
            if op in instr2pfunc:
                func   = instr2pfunc[op]
                s = func(obj)
                print idx, s
            else:
                print idx, obj
        else:
            print idx, obj
    return

####################################################
class ir_code(object):
    def __init__(self, lexer_obj):
        self.lexer              = lexer_obj
        self.all_vars           = []
        self.str_ptr_var        = None
        self.lstate_ptr         = None
        self.data_var           = None

        self.saved_valid        = None
        self.saved_ptr          = None
        self.saved_result       = None

        self.next_avail_var_num = 1
        self.instructions       = []
        self.call_method_addr   = escape.get_func_addr("PyObject_CallMethod")
        self.char_ptr_offset    = escape.get_char_ptr_offset()
        self.token_start_offset = escape.get_token_start_offset()
        self.fill_caller_addr   = escape.get_fill_caller_addr()
        self.lbuf               = None

        symtab = globals()
        for f in ir_names:
            func_obj = symtab[f]
            setattr(self, "make_" + f, func_obj)

        pass

    def __len__(self):
        return len(self.instructions)

    def __getitem__(self, key):
        return self.instructions[key]

    ####################
    def make_new_var(self):
        r = "var_%d" % self.next_avail_var_num
        self.next_avail_var_num += 1
        self.all_vars.append(r)
        return r

    def make_indirect_var(self, v):
        assert_is_var(v)
        return '(' + v + ')'

    def make_std_vars(self):
        self.tmp_var           = self.make_new_var()
        self.tmp_var2          = self.make_new_var()
        self.str_ptr_var       = self.make_new_var()
        self.token_start_ptr   = self.make_new_var()
        self.data_var          = self.make_new_var()

        self.saved_valid       = self.make_new_var()
        self.saved_ptr         = self.make_new_var()
        self.saved_result      = self.make_new_var()

        self.lstate_ptr        = self.make_new_var()
        self.fill_status       = self.make_new_var()
        return

    def set_str_ptr_var(self, val):
        self.str_ptr_var = val
        return

    ####################
    ## ir creator funcs
    ####################
    def add_ir_label(self, *args):
        self.instructions.append(ir_label(*args))
        return
    def add_ir_data(self, *args):
        self.instructions.append(ir_data(*args))
        return
    def add_ir_ldw(self, *args):
        self.instructions.append(ir_ldw(*args))
        return
    def add_ir_ldb(self, *args):
        self.instructions.append(ir_ldb(*args))
        return
    def add_ir_stw(self, *args):
        self.instructions.append(ir_stw(*args))
        return
    def add_ir_stb(self, *args):
        self.instructions.append(ir_stb(*args))
        return
    def add_ir_set(self, *args):
        self.instructions.append(ir_set(*args))
        return
    def add_ir_cmp(self, *args):
        self.instructions.append(ir_cmp(*args))
        return
    def add_ir_beq(self, *args):
        self.instructions.append(ir_beq(*args))
        return
    def add_ir_bne(self, *args):
        self.instructions.append(ir_bne(*args))
        return
    def add_ir_br(self, *args):
        self.instructions.append(ir_br(*args))
        return
    def add_ir_nop(self, *args):
        self.instructions.append(ir_nop(*args))
        return
    def add_ir_add(self, *args):
        self.instructions.append(ir_add(*args))
        return
    def add_ir_ret(self, *args):
        self.instructions.append(ir_ret(*args))
        return
    def add_ir_com(self, *args):
        self.instructions.append(ir_com(*args))
        return
    def add_ir_call(self, *args):
        self.instructions.append(ir_call(*args))
        return
    def add_ir_gparm(self, *args):
        self.instructions.append(ir_gparm(*args))
        return

    ####################
    ## list ir creator funcs
    ####################
    def ladd_ir_label(self, l, *args):
        l.append(ir_label(*args))
        return
    def ladd_ir_data(self, l, *args):
        l.append(ir_data(*args))
        return
    def ladd_ir_ldw(self, l, *args):
        l.append(ir_ldw(*args))
        return
    def ladd_ir_ldb(self, l, *args):
        l.append(ir_ldb(*args))
        return
    def ladd_ir_stw(self, l, *args):
        l.append(ir_stw(*args))
        return
    def ladd_ir_stb(self, l, *args):
        l.append(ir_stb(*args))
        return
    def ladd_ir_set(self, l, *args):
        l.append(ir_set(*args))
        return
    def ladd_ir_cmp(self, l, *args):
        l.append(ir_cmp(*args))
        return
    def ladd_ir_beq(self, l, *args):
        l.append(ir_beq(*args))
        return
    def ladd_ir_bne(self, l, *args):
        l.append(ir_bne(*args))
        return
    def ladd_ir_br(self, l, *args):
        l.append(ir_br(*args))
        return
    def ladd_ir_nop(self, l, *args):
        l.append(ir_nop(*args))
        return
    def ladd_ir_add(self, l, *args):
        l.append(ir_add(*args))
        return
    def ladd_ir_ret(self, l, *args):
        l.append(ir_ret(*args))
        return
    def ladd_ir_com(self, l, *args):
        l.append(ir_com(*args))
        return
    def ladd_ir_call(self, l, *args):
        l.append(ir_call(*args))
        return
    def ladd_ir_gparm(self, l, *args):
        l.append(ir_gparm(*args))
        return
    pass

####################################################
####################################################
##
## compile to actual machine code
##
####################################################
####################################################
def compile_to_vcode(ir):
    r = escape.code()
    r.set_type("vcode")
    for tup in ir.instructions:
        r.append(tup)
    return r

def compile_to_x86_32(ir, debug=False):
    if 1:
        l = ir_to_asm_list_x86_32(ir, debug=debug)
        r = asm_list_x86_32_to_code(l, print_asm_txt=debug)
        escape.do_serialize()
    return r

def asm_list_x86_32_to_code(lines, print_asm_txt=False, asm_mode="py"):
    if asm_mode == "py":
        c = asm_list_x86_32_to_code_py(lines, print_asm_txt)
        return c
    elif asm_mode == "as":
        c = asm_list_x86_32_to_code_as(lines, print_asm_txt)
        return c
    elif asm_mode == "comp":
        c1 = asm_list_x86_32_to_code_as(lines)
        c2 = asm_list_x86_32_to_code_py(lines, print_asm_txt=True)
        c1_code = c1.get_code()
        c2_code = c2.get_code()
        if c1_code != c2_code:
            l = min(len(c1_code), len(c2_code))
            for i in range(l):
                if c1_code[i] != c2_code[i]:
                    print "First byte diff at", i
                    break
            print "code is different"
            pdb.set_trace()
            raise RuntimeError, "Code compare error"
        else:
            print "code is same"
        return c1
    else:
        raise RuntimeError, "Unknown asm mode=" + str(asm_mode)

def asm_list_x86_32_to_code_as(lines, print_asm_txt=False):
    fp = open("/tmp/foobar.s", "w")
    for tup in lines:
        assert len(tup)==3
        if tup[0] is None:
            txt = "\t"
        elif tup[0][0] == "#":
            txt = "#"
        else:
            txt = tup[0] + ":\t"

        if tup[1] is None:
            assert tup[2] is None
        else:
            txt += tup[1]
            if tup[2] is not None:
                txt += " " + tup[2]

        print >>fp, txt
    fp.close()

    if print_asm_txt:
        print "-----------------"
        print "asm text:"
        fp = open("/tmp/foobar.s", "r")
        for l in fp:
            print l,
        fp.close()
        print "-----------------"

    code = os.system("as -o /tmp/foobar.o /tmp/foobar.s > /tmp/foobar.as_stdout 2> /tmp/foobar.as_stderr")
    assert code==0, "error while running assembler"
    assert os.path.getsize("/tmp/foobar.as_stdout")==0
    assert os.path.getsize("/tmp/foobar.as_stderr")==0

    code = os.system("ld -o /tmp/foobar.so -shared /tmp/foobar.o")
    assert code==0, "error while creating shared library"

    dl_handle = dl.open("/tmp/foobar.so")
    addr1 = dl_handle.sym("func1")
    addr2 = dl_handle.sym("func2")
    assert type(addr1) in (int,long)
    assert type(addr2) in (int,long)
    n_bytes = addr2 - addr1
    assert n_bytes >= 0

    code_obj = escape.code()
    b = escape.get_bytes(addr1, n_bytes)
    code_obj.set_bytes(b)
    return code_obj

def ir_to_asm_list_x86_32(ir, debug=False):
    asm_list = []

    var2offset = {}
    frame_offset = -4
    for r in ir.all_vars:
        var2offset[r] = frame_offset
        if debug:
            print "   offset=%d ---> <%s>" % (frame_offset, r)
        frame_offset += -4
    n_locals = len(ir.all_vars)
    locals_size = n_locals * 4

    asm_list.append((None, ".text", None))
    asm_list.append((None, ".globl", "func1"))
    asm_list.append((None, ".globl", "func2"))

    asm_list.append(("func1", None, None))
    asm_list.append((None, "pushl", "%ebp"))
    asm_list.append((None, "movl", "%esp, %ebp"))
    asm_list.append(("#", "n_locals=%d" % n_locals, None))
    asm_list.append((None, "add", "$%d, %%esp" % -locals_size))

    data_lab_num = 0
    code_lab_num = 0

    for tup in ir.instructions:
        op = tup[0]
        if op==IR_LABEL:
            asm_list.append((tup[1], None, None))
        elif op==IR_LDW:
            asm_list.append(("#", "ldw", None))
            dst_var = tup[1]
            assert_is_var(dst_var)
            src = tup[2]
            if is_indirect_var(src):
                src2 = dereference_indirect_var(src)
                so = var2offset[src2]
                do = var2offset[dst_var]
                asm_list.append((None, "movl", "%d(%%ebp), %%eax" % so))
                asm_list.append((None, "movl", "(%eax), %eax"))
                asm_list.append((None, "movl", "%%eax, %d(%%ebp)" % do))
            elif is_num(src):
                asm_list.append((None, "movl", "%d(,1), %%eax" % src))
                offset = var2offset[dst_var]
                asm_list.append((None, "movl", "%%eax, %d(%%ebp)" % offset))
            elif is_data_label(src):
                raise RuntimeError, "ldw data src label not yet handled"
            else:
                raise RuntimeError, "Unknown ldw src operand type"
        elif op==IR_LDB:
            asm_list.append(("#", "ldb", None))
            dst_var = tup[1]
            assert_is_var(dst_var)
            src = tup[2]
            if is_indirect_var(src):
                src2 = dereference_indirect_var(src)
                offset = var2offset[src2]
                asm_list.append((None, "movl", "%d(%%ebp), %%eax" % offset))
                asm_list.append((None, "movl", "$0, %ecx"))
                asm_list.append((None, "movb", "(%eax), %cl"))
                offset = var2offset[dst_var]
                asm_list.append((None, "movl", "%%ecx, %d(%%ebp)" % offset))
            elif is_num(src):
                asm_list.append((None, "movl", "$0, %eax"))
                asm_list.append((None, "movb", "%d(,1), %%eal" % src))
                offset = var2offset[dst_var]
                asm_list.append((None, "movb", "%%eax, %d(%%ebp)" % offset))
            elif is_data_label(src):
                assert None, "ldb data src label not yet handled"
            else:
                assert None, "Unknown ldb src operand type"
        elif op==IR_STW:
            asm_list.append(("#", "stw", None))
            dst = tup[1]
            src = tup[2]
            assert_is_var(src)
            src_o = var2offset[src]
            if is_num(dst):
                asm_list.append((None, "movl", "%d(%%ebp), %eax" % src_o))
                asm_list.append((None, "movl", "%%eax, %d(,1)" % dst))
            elif is_indirect_var(dst):
                dst_var = dereference_indirect_var(dst)
                dst_o = var2offset[dst_var]
                asm_list.append((None, "movl", "%d(%%ebp), %%ecx" % dst_o))
                asm_list.append((None, "movl", "%d(%%ebp), %%eax" % src_o))
                asm_list.append((None, "movl", "%eax, (%ecx)"))
            elif is_data_label(dst):
                assert None, "STW to data label not yet supported"
            else:
                assert None, "Invalid dst for STW"
        elif op==IR_STB:
            assert None, "op not yet supported"
        elif op==IR_SET:
            asm_list.append(("#", "set", None))
            dst = tup[1]
            src = tup[2]
            assert_is_var(dst)
            assert_is_var_or_const(src)
            off1 = var2offset[dst]
            if is_var(src):
                off2 = var2offset[src]
                asm_list.append((None, "movl", "%d(%%ebp), %%eax" % off2))
                asm_list.append((None, "movl", "%%eax, %d(%%ebp)" % off1))
            else:
                asm_list.append((None, "movl", "$%d, %d(%%ebp)" % (src, off1)))
        elif op==IR_CMP:
            r = tup[1]
            v = tup[2]
            assert_is_var(r)
            r_off = var2offset[r]

            if is_var(v):
                v_off = var2offset[v]
                asm_list.append((None, "movl", "%d(%%ebp), %%eax" % r_off))
                asm_list.append((None, "cmpl", "%d(%%ebp), %%eax" % v_off))
            else:
                assert is_num(v)
                asm_list.append((None, "movl", "%d(%%ebp), %%eax" % r_off))
                asm_list.append((None, "cmpl", "$%d, %%eax" % v))
        elif op==IR_BEQ:
            dst_lab = tup[1]
            asm_list.append((None, "je", dst_lab))
        elif op==IR_BNE:
            dst_lab = tup[1]
            asm_list.append((None, "jne", dst_lab))
        elif op==IR_BR:
            dst_lab = tup[1]
            asm_list.append((None, "jmp", dst_lab))
        elif op==IR_NOP:
            assert None, "op not yet supported:" + instr2txt[op]
        elif op==IR_ADD:
            r = tup[1]
            assert_is_var(r)
            val = tup[2]
            if is_var(val):
                r_off = var2offset[r]
                v_off = var2offset[val]
                asm_list.append((None, "movl", "%d(%%ebp), %%eax" % r_off))
                asm_list.append((None, "addl", "%d(%%ebp), %%eax" % v_off))
                asm_list.append((None, "movl", "%%eax, %d(%%ebp)" % r_off))
            else:
                assert is_num(val)
                r_off = var2offset[r]
                asm_list.append((None, "movl", "%d(%%ebp), %%eax" % r_off))
                asm_list.append((None, "addl", "$%d, %%eax" % val))
                asm_list.append((None, "movl", "%%eax, %d(%%ebp)" % r_off))
        elif op==IR_RET:
            var = tup[1]
            assert_is_var_or_const(var)
            if is_var(var):
                offset = var2offset[var]
                asm_list.append(("#", "ret", None))
                asm_list.append((None, "movl", "%d(%%ebp), %%eax" % offset))
                asm_list.append((None, "movl", "%ebp, %esp"))
                asm_list.append((None, "popl", "%ebp"))
                asm_list.append((None, "ret", None))
            else:
                assert type(var) is int
                val = var
                asm_list.append(("#", "ret", None))
                asm_list.append((None, "movl", "$%d, %%eax" % val))
                asm_list.append((None, "movl", "%ebp, %esp"))
                asm_list.append((None, "popl", "%ebp"))
                asm_list.append((None, "ret", None))
        elif op==IR_COM:
            asm_list.append(("#", tup[1], None))
        elif op==IR_CALL:
            asm_list.append(("#", "call", None))
            dst_var = tup[1]
            fptr    = tup[2]
            if len(tup) == 3:
                # no args
                asm_list.append((None, "movl", "$0x%x, %%eax" % fptr))
                asm_list.append((None, "call", "*%eax"))
                n_pops = 0
            else:
                # have args
                args = tup[3:]
                for idx in range(len(args) - 1, -1, -1):
                    a = args[idx]
                    if is_var(a):
                        o = var2offset[a]
                        asm_list.append((None, "movl", "%d(%%ebp), %%eax" % o))
                        asm_list.append((None, "pushl", "%eax"))
                    elif type(a) is str:
                        clab = "code_lab_%d" % code_lab_num
                        code_lab_num += 1
                        asm_list.append((None, "call", clab))
                        asm_list.append((None, ".asciz", a))
                        asm_list.append((clab, None, None))
                        asm_list.append((None, "nop", None))
                    else:
                        assert a is None
                        asm_list.append((None, "pushl", "$0"))
                if is_var(fptr):
                    o = var2offset[fptr]
                    asm_list.append((None, "movl", "%d(%%ebp), %%eax" % o))
                else:
                    asm_list.append((None, "movl", "$0x%x, %%eax" % fptr))
                asm_list.append((None, "call", "*%eax"))
                n_pops = len(args)
            if is_var(dst_var):
                dst_off = var2offset[dst_var]
                asm_list.append((None, "movl", "%%eax, %d(%%ebp)" % dst_off))
            asm_list.append((None, "add", "$%d, %%esp" % (n_pops * 4)))
        elif op==IR_GPARM:
            asm_list.append(("#", "gparm", None))
            dst_var = tup[1]
            assert_is_var(dst_var)
            arg_num = tup[2]
            assert_is_const(arg_num)
            dst_offset = var2offset[dst_var]
            arg_offset = (arg_num + 2) * 4
            asm_list.append((None, "movl", "%d(%%ebp), %%eax" % arg_offset))
            asm_list.append((None, "movl", "%%eax, %d(%%ebp)" % dst_offset))
        else:
            assert None, "Unknown op code"

    asm_list.append(("func2", None, None))
    asm_list.append((None, "nop", None))
    return asm_list

##################################################################
##
## x86 32bit assembler
##
## <instr prefix><opcode><ModR/M><SIB><displacement><immediate>
##
## opcode         is 1, 2 or 3 bytes
## ModR/M         1 byte if required --> <2-Mod><3-Reg/Opcode><3-R/M>
## SIB            1 byte if required --> <2-scale><3-index><3-base>
## displacement   0, 1,2 or 4 bytes
## immediate      0, 1,2,or 4 bytes
##
##################################################################
class instr_x86_32(object):
    def __init__(self, label, opcode, args):
        self.asm_label        = label

        self.bytes            = []

        self.is_var_len       = False
        self.bytes_rel8       = []
        self.bytes_rel16      = []
        self.bytes_rel32      = []
        self.which_variant    = None
        self.jump_target      = None

        self.asm_op           = opcode
        self.asm_args         = args
        self.first_byte_idx   = None

        self.instr_list_idx   = None
        self.distance_to_targ = None

        return

    def __str__(self):
        if self.first_byte_idx is None:
            idx = -1
        else:
            idx = self.first_byte_idx

        if self.asm_label:
            return "%4d: %s: %s %s b=%s" % (idx, self.asm_label, self.asm_op,
                                            self.asm_args, str(self.bytes))
        else:
            return "%4d -----: %s %s b=%s" % (idx, self.asm_op,
                                              self.asm_args, str(self.bytes))
    pass

def asm_list_x86_32_to_code_py(asm_list, print_asm_txt=False):
    all_labels = {}
    for label, opcode, args in asm_list:
        if label and type(label) is str and label[0] != '#':
            all_labels[label] = True

    saved_label = None
    instr_list = []
    for label, opcode, args in asm_list:
        if type(label) is str and label[0] != '#':
            saved_label = label
        if opcode in (".text", ".globl", None):
            continue
        if type(label) is str and label[0]=='#':
            continue


        if label:
            saved_label = None
        elif saved_label:
            label = saved_label
            saved_label = None

        instr = instr_x86_32(label, opcode, args)
        instr_list.append(instr)
        if opcode=="ret":
            instr.bytes.append(0xC3)
        elif opcode=="movl":
            args2 = parse_x86_32_args(args)
            src, dst = args2
            if x86_32_arg_is_const(src):
                if x86_32_arg_is_plain_reg(dst):
                    src_val = x86_32_arg_parse_const(src)
                    assert src_val >= 0
                    if dst == "%eax":
                        op_byte = 0xB8
                    elif dst == "%ebx":
                        op_byte = 0xBB
                    elif dst == "%ecx":
                        op_byte = 0xB9
                    else:
                        raise RuntimeError, "movl to known dest=" + str(dst)
                    immed = asm_x86_32_make_pos_immed32(src_val)
                    instr.bytes.append(op_byte)
                    instr.bytes.extend(immed)
                else:
                    assert x86_32_arg_is_reg_indirect(dst)
                    instr.bytes.append(0xC7)
                    tmp = asm_x86_32_encode_modrm_const_indirreg(src, dst)
                    instr.bytes.extend(tmp)
            elif x86_32_arg_is_plain_reg(src):
                if x86_32_arg_is_reg_indirect(dst):
                    tmp = asm_86_32_encode_modrm_reg_indirreg(src, dst)
                    instr.bytes.append(0x89)
                    instr.bytes.extend(tmp)
                elif x86_32_arg_is_plain_reg(dst):
                    instr.bytes.append(0x89)
                    r   = modrm_tbl1[src]
                    rm  = modrm_tbl2[dst]
                    mod = 3
                    tmp = asm86_32_make_modrm(mod, r, rm)
                    instr.bytes.append(tmp)
                else:
                    assert None, "movl with unrecog dst=" + str(dst)
            elif x86_32_arg_is_reg_indirect(src):
                if x86_32_arg_is_plain_reg(dst):
                    tmp = asm_86_32_encode_modrm_reg_indirreg(dst, src)
                    instr.bytes.append(0x8B)
                    instr.bytes.extend(tmp)                    
                else:
                    assert None, "movl"
            else:
                pdb.set_trace()
                assert None, "movl with unsupported src operand " + str(src)
        elif opcode=="movb":
            args2 = parse_x86_32_args(args)
            src, dst = args2
            if x86_32_arg_is_reg_indirect(src):
                if x86_32_arg_is_plain_reg(dst):
                    tmp = asm_86_32_encode_modrm_reg_indirreg(dst, src)
                    instr.bytes.append(0x8A)
                    instr.bytes.extend(tmp)                    
                else:
                    assert None, "movl"
            else:
                assert None, "movl with non-const src operand " + str(src)
        elif opcode=="addl":
            src, dst = parse_x86_32_args(args)
            if x86_32_arg_is_reg_indirect(src):
                tmp = asm_86_32_encode_modrm_reg_indirreg(dst, src)
                instr.bytes.append(0x03)
                instr.bytes.extend(tmp)
            elif x86_32_arg_is_const(src):
                assert x86_32_arg_is_plain_reg(dst)
                src_val = x86_32_arg_parse_const(src)
                if x86_32_const_is_imm8(src_val):
                    instr.bytes.append(0x83)
                    mod = 3
                    r   = 0
                    rm  = modrm_tbl1[dst]
                    tmp = asm86_32_make_modrm(mod, r, rm)
                    instr.bytes.append(tmp)
                    imm = asm_x86_32_make_s_immed8(src_val)
                    instr.bytes.append(imm)
                else:
                    instr.bytes.append(0x81)
                    mod = 3
                    r   = 0
                    rm  = modrm_tbl1[dst]
                    tmp = asm86_32_make_modrm(mod, r, rm)
                    instr.bytes.append(tmp)
                    imm = asm_x86_32_make_immed32(src_val)
                    instr.bytes.extend(imm)
            else:
                raise RuntimeError, "Unsupported src for addl=" + str(src)
        elif opcode=="add":
            src, dst = parse_x86_32_args(args)
            if x86_32_arg_is_const(src) and x86_32_arg_is_plain_reg(dst):
                src_val = x86_32_arg_parse_const(src)
                if x86_32_const_is_imm8(src_val):
                    instr.bytes.append(0x83)
                    mod = 3
                    r   = 0
                    rm  = modrm_tbl1[dst]
                    tmp = asm86_32_make_modrm(mod, r, rm)
                    instr.bytes.append(tmp)
                    imm = asm_x86_32_make_s_immed8(src_val)
                    instr.bytes.append(imm)
                else:
                    instr.bytes.append(0x81)
                    mod = 3
                    r   = 0
                    rm  = modrm_tbl1[dst]
                    tmp = asm86_32_make_modrm(mod, r, rm)
                    instr.bytes.append(tmp)
                    imm = asm_x86_32_make_immed32(src_val)
                    instr.bytes.extend(imm)
            else:
                raise RuntimeError, \
                      "Unsupported arg types for add opcode=" + str(args)
        elif opcode=="cmpl":
            a1, a2 = parse_x86_32_args(args)
            assert x86_32_arg_is_plain_reg(a2)
            if x86_32_arg_is_const(a1):
                a1 = x86_32_arg_parse_const(a1)
                assert x86_32_const_is_imm8(a1)
                instr.bytes.append(0x83)
                reg_sel = modrm_tbl1[a2]
                modrm = asm86_32_make_modrm(3, 7, reg_sel)
                imm = asm_x86_32_make_s_immed8(a1)
                instr.bytes.append(modrm)
                instr.bytes.append(imm)
            else:
                assert x86_32_arg_is_reg_indirect(a1)
                instr.bytes.append(0x3B)
                tmp = asm_86_32_encode_modrm_reg_indirreg(a2, a1)
                instr.bytes.extend(tmp)
        elif opcode in ("jne", "je"):
            assert type(args) is str
            instr.jump_target = args
            instr.is_var_len = True

            rel8_op = jumpcc_rel8_tbl[opcode]
            instr.bytes_rel8.append(rel8_op)
            instr.bytes_rel8.append(None)

            rel16or32_op = jumpcc_rel16or32_tbl[opcode]
            instr.bytes_rel32.append(0x0F)
            instr.bytes_rel32.append(rel16or32_op)
            instr.bytes_rel32.append(None)
            instr.bytes_rel32.append(None)
            instr.bytes_rel32.append(None)
            instr.bytes_rel32.append(None)
        elif opcode=="jmp":
            assert type(args) is str
            instr.jump_target = args
            instr.is_var_len = True

            instr.bytes_rel8.append(0xEB)
            instr.bytes_rel8.append(None)

            instr.bytes_rel32.append(0xE9)
            instr.bytes_rel32.append(None)
            instr.bytes_rel32.append(None)
            instr.bytes_rel32.append(None)
            instr.bytes_rel32.append(None)
        elif opcode=="nop":
            instr.bytes.append(0x90)
        elif opcode=="call":
            assert type(args) is str
            if args == "*%eax":
                instr.bytes.append(0xFF)
                
                mod = 3
                r   = 2
                rm  = modrm_tbl1["%eax"]
                tmp = asm86_32_make_modrm(mod, r, rm)
                instr.bytes.append(tmp)
            else:
                assert args in all_labels
                instr.is_var_len = True

                instr.jump_target = args
                instr.bytes_rel32.append(0xE8)
                instr.bytes_rel32.append(None)
                instr.bytes_rel32.append(None)
                instr.bytes_rel32.append(None)
                instr.bytes_rel32.append(None)
        elif opcode=="pushl":
            if x86_32_arg_is_plain_reg(args):
                if args == "%eax":
                    op_byte = 0x50
                elif args == "%ebx":
                    op_byte = 0x53
                elif args == "%ecx":
                    op_byte = 0x51
                elif args == "%ebp":
                    op_byte = 0x55
                else:
                    raise RuntimeError, "Unsupported reg to pushl" + str(args)
                instr.bytes.append(op_byte)
            else:
                assert x86_32_arg_is_const(args)
                const_val = x86_32_arg_parse_const(args)
                instr.bytes.append(0x68)
                tmp = asm_x86_32_make_immed32(const_val)
                instr.bytes.extend(tmp)
        elif opcode=="popl":
            assert x86_32_arg_is_plain_reg(args)
            if args == "%eax":
                op_byte = 0x58
            elif args == "%ebx":
                op_byte = 0x5B
            elif args == "%ecx":
                op_byte = 0x59
            elif args == "%ebp":
                op_byte = 0x5D
            else:
                raise RuntimeError, "Unknown pop reg " + str(args)
            instr.bytes.append(op_byte)
        elif opcode==".asciz":
            for ch in args:
                as_int = ord(ch)
                instr.bytes.append(as_int)
            instr.bytes.append(0)
        else:
            raise RuntimeError, "Unsupported x86 opcode " + str(opcode)
        pass

    for idx, instr in enumerate(instr_list):
        instr.instr_list_idx = idx

    lab2instridx = {}
    for idx, instr in enumerate(instr_list):
        if instr.asm_label:
            lab2instridx[instr.asm_label] = idx

    var_len_instrs = [i for i in instr_list if i.is_var_len]
    for i in var_len_instrs:
        assert i.jump_target is not None
        targ_idx = lab2instridx[i.jump_target]
        i.distance_to_targ = abs(i.instr_list_idx - targ_idx)

    def instr_sorter(i1, i2):
        return cmp(i1.distance_to_targ, i2.distance_to_targ)
    var_len_instrs.sort(instr_sorter)

    for i in var_len_instrs:
        assert len(i.bytes) == 0
        if i.distance_to_targ < 15 and i.asm_op != "call":
            assert len(i.bytes_rel8) > 0
            i.bytes = i.bytes_rel8
            i.which_variant = "rel8"
        else:
            assert len(i.bytes_rel32) > 0
            i.bytes = i.bytes_rel32
            i.which_variant = "rel32"

    byte_idx = 0
    for instr in instr_list:
        instr.first_byte_idx = byte_idx
        byte_idx += len(instr.bytes)
        pass

    for instr in instr_list:
        if not instr.jump_target:
            continue
        target_idx = lab2instridx[ instr.jump_target ]
        target_byte_idx = instr_list[ target_idx ].first_byte_idx
        cur_byte_idx = instr.first_byte_idx + len(instr.bytes)
        disp = target_byte_idx - cur_byte_idx 

        assert instr.which_variant == "rel8" or instr.which_variant == "rel32"
        if instr.which_variant == "rel8":
            tmp = asm_x86_32_make_s_immed8(disp)
            assert instr.bytes[-1] == None
            instr.bytes[-1] = tmp
        else:
            tmp = asm_x86_32_make_immed32(disp)
            assert instr.bytes[-1]==None and instr.bytes[-2]==None
            assert instr.bytes[-3]==None and instr.bytes[-4]==None
            assert instr.bytes.count(None) == len(tmp)
            instr.bytes[-4] = tmp[0]
            instr.bytes[-3] = tmp[1]
            instr.bytes[-2] = tmp[2]
            instr.bytes[-1] = tmp[3]
        pass

    if print_asm_txt or 0:
        print "Assembly result"
        addr = 0
        for instr in instr_list:
            print instr.first_byte_idx, instr.asm_label, instr.asm_op, \
                  instr.asm_args, ":",
            for b in instr.bytes:
                print " %0X" % b ,
            print ""

    byte_list = []
    for instr in instr_list:
        byte_list.extend(instr.bytes)
    byte_list2 = [chr(b) for b in byte_list]
    mcode = "".join(byte_list2)

    code = escape.code()
    code.set_bytes(mcode)
    if 0:
        addr = code.get_start_addr()
        print "Code start addr is 0x%x" % addr
        for instr in instr_list:
            addr2 = addr + instr.first_byte_idx
            print "0x%x %s" % (addr2, str(instr))

    return code

# jump type tables
jumpcc_rel8_tbl = {
    "jne"   : 0x75,
    "je"    : 0x74
    }

jumpcc_rel16or32_tbl = {
    "jne"    : 0x85,
    "je"     : 0x84
    }

# indexed by indirect register -- effective address
modrm_tbl1 = {
    "%eax"   : 0,
    "%ecx"   : 1,
    "%edx"   : 2,
    "%ebx"   : 3,
    "%esp"   : 4,
    "%ebp"   : 5
    }

# indexed by associated register
modrm_tbl2 = {
    "%al"      : 0,
    "%ax"      : 0,
    "%eax"     : 0,

    "%cl"      : 1,
    "%cx"      : 1,
    "%ecx"     : 1,

    "%dl"      : 2,
    "%dx"      : 2,
    "%edx"     : 2,

    "%bl"      : 3,
    "%bx"      : 3,
    "%ebx"     : 3,

    "%ah"      : 4,
    "%sp"      : 4,
    "%esp"     : 4,

    "%ch"      : 5,
    "%bp"      : 5,
    "%ebp"     : 5,

    "%dh"      : 6,
    "%bh"      : 7}

def asm_x86_32_encode_modrm_const_indirreg(const, indir):
    indir_offset, indir_reg = x86_32_arg_parse_indirect(indir)
    if indir_offset == 0:
        mod = 0
        disp = None
    elif indir_offset >= -127 and indir_offset <= 128:
        mod = 1
        if indir_offset < 0:
            disp = [ 256 - abs(indir_offset) ]
        else:
            disp = [indir_offset]
    else:
        mod = 2
        disp = asm_x86_32_make_pos_immed32(indir_offset)

    rm = modrm_tbl1[indir_reg]
    r  = 0
    modrm = asm86_32_make_modrm(mod, r, rm)
    result = [modrm]

    if disp:
       result.extend(disp)

    const_val = x86_32_arg_parse_const(const)
    tmp = asm_x86_32_make_immed32(const_val)
    result.extend(tmp)

    return result
    

def asm_86_32_encode_modrm_reg_indirreg(reg, indir):
    indir_offset, indir_reg = x86_32_arg_parse_indirect(indir)
    if indir_offset == 0:
        mod = 0
        disp = None
    elif indir_offset >= -127 and indir_offset <= 128:
        mod = 1
        if indir_offset < 0:
            disp = [ 256 - abs(indir_offset) ]
        else:
            disp = [indir_offset]
    else:
        mod = 2
        disp = asm_x86_32_make_pos_immed32(indir_offset)

    rm = modrm_tbl1[indir_reg]
    r  = modrm_tbl2[reg]
    modrm = asm86_32_make_modrm(mod, r, rm)
    result = [modrm]

    if disp:
       result.extend(disp)
    return result

def parse_x86_32_args(txt):
    txt2 = txt.replace(" ", "")
    f = txt2.split(",")
    if len(f) == 2:
        src, dst = f
        return (src, dst)
    return None

############
## addr modes
############
def x86_32_arg_is_reg_indirect(txt):
    pat = re.compile("([-x0-9]*)\\((.*)\\)")
    m = pat.match(txt)
    if m:
        return True
    return False

def x86_32_arg_parse_indirect(txt):
    pat = re.compile("([-x0-9]*)\\((.*)\\)")
    m = pat.match(txt)
    assert m
    assert x86_32_arg_is_plain_reg(m.group(2))
    offset_txt = m.group(1)
    if offset_txt.startswith("0x"):
        off = int(offset_txt, 16)
    elif len(offset_txt) > 0:
        off = int(offset_txt)
    else:
        off = 0
    return (off, m.group(2))

############
## arg types
############
def x86_32_arg_is_const(txt):
    if txt[0]=="$":
        return True
    return False

def x86_32_arg_is_plain_reg(txt):
    if txt in ("%eax", "%ebx", "%ecx", "%ebp", "%esp",
               "%al", "%ah", "%bl", "%bh", "%cl", "%ch"):
        return True
    return False

def x86_32_const_is_imm8(val):
    if val >= -127 and val < 128:
        return True
    return False

############
## consts
############
def x86_32_arg_parse_const(txt):
    assert x86_32_arg_is_const(txt)
    txt2 = txt[1:]
    if txt2.startswith("0x"):
        val = int(txt2, 16)
    else:
        assert txt2.isdigit() or (txt2[0]=="-" and txt2[1:].isdigit())
        val = int(txt2)
    return val

############
## make various things
############
def asm86_32_make_modrm(mod, reg, rm):
    assert mod >= 0 and mod <= 3
    assert reg >= 0 and reg <= 7
    assert rm  >= 0 and rm  <= 7
    modrm = (mod << 6) | (reg << 3) | rm
    return modrm

def asm_x86_32_make_immed32(val):
    if val >= 0:
        return asm_x86_32_make_pos_immed32(val)
    return asm_x86_32_make_neg_immed32(val)

def asm_x86_32_make_neg_immed32(val):
    assert val < 0
    tmp = 0xFFFFFFFF - abs(val) + 1
    return asm_x86_32_make_pos_immed32(tmp)

def asm_x86_32_make_pos_immed32(val):
    assert val >= 0
    b1 = val & 0xFF
    b2 = (val >>  8) & 0xFF
    b3 = (val >> 16) & 0xFF
    b4 = (val >> 24) & 0xFF
    return [int(b1), int(b2), int(b3), int(b4)]

def asm_x86_32_make_s_immed16(val):
    assert val >= -65535 and val <= 65536
    if val > 0:
        v1 = val & 0xFF
        v2 = (val >> 8) & 0xFF
        return [v1, v2]
    tmp = 65536 - abs(val)
    v1 = val & 0xFF
    v2 = (val >> 8) & 0xFF
    return [v1, v2]

def asm_x86_32_make_s_immed8(val):
    assert val >= -127 and val <= 128
    if val >= 0:
        return val
    return 256 - abs(val)

##################################################################
##
## simulator
##
##################################################################
def set_var(var_tbl, var, val):
    var_tbl[var] = val
    return

def resolve_var(var_tbl, var):
    assert_is_var(var)
    if var not in var_tbl:
        var_tbl[var] = 77
    return var_tbl[var]

def resolve_addr_or_indirect_var(var_tbl, arg):
    if type(arg) is str:
        assert arg[0] == "(" and arg[-1]==")"
        var = arg[1:-1]
        assert_is_var(var)
        return resolve_var(var_tbl, var)
    assert_is_const(arg)
    return arg

def resolve_var_or_const(var_tbl, arg):
    if type(arg) is str:
        assert_is_var(arg)
        return resolve_var(var_tbl, arg)
    assert_is_const(arg)
    return arg

def resolve_const(arg):
    assert_is_const(arg)
    return arg


def run_vcode_simulation(code_obj, lstate, debug_flag=False, max_instrs=None):
    assert lstate.has_data() == True

    n_instr = len(code_obj)
    if n_instr == 0:
        return None

    if debug_flag:
        print "---------start of simulation-------"
        off = lstate.get_cur_offset()
        addr = lstate.get_cur_addr()
        print "offset=%d addr=%d=0x%x" % (off, addr, addr)

    var_tbl    = {}
    label2idx  = {}
    is_eql     = False

    for idx in xrange(n_instr):
        tup = code_obj[idx]
        if tup[0] == IR_LABEL:
            label2idx[tup[1]] = idx
        pass

    instr_num = 0
    iptr = 0
    while True:
        assert iptr >= 0 and iptr < n_instr
        tup = code_obj[iptr]
        if debug_flag:
            print "sim iptr=", iptr, "tup=", instr2txt[tup[0]], tup[1:]

        instr_num += 1
        if type(max_instrs) is int and instr_num >= max_instrs:
            return None

        iptr += 1
        op = tup[0]
        if op == IR_LABEL:
            if debug_flag:
                print "  at label", tup[1]
        elif op == IR_LDW:
            # var, addr | var, (var)
            dst = tup[1]
            assert_is_var(dst)
            src = resolve_addr_or_indirect_var(var_tbl, tup[2])
            val = lstate.ldw(src)
            set_var(var_tbl, dst, val)
            if val == 0:
                is_eql = True
            else:
                is_eql = False
            if debug_flag:
                print "  ldw %s <-- %d eql_flag=%s" % (dst, val, str(is_eql))
        elif op == IR_LDB:
            # var, addr | var, (var)
            dst = tup[1]
            assert_is_var(dst)
            src = resolve_addr_or_indirect_var(var_tbl, tup[2])
            val = lstate.ldb(src)
            assert_is_byte(val)
            set_var(var_tbl, dst, val)
            if val == 0:
                is_eql = True
            else:
                is_eql = False
            if debug_flag:
                print "  ldb %s <-- %d eql_flag=%s" % (dst, val, str(is_eql))
        elif op == IR_STW:
            # addr, var | (var), var
            dst = resolve_addr_or_indirect_var(var_tbl, tup[1])
            src = resolve_var(var_tbl, tup[2])
            lstate.stw(dst, src)
            if debug_flag:
                print "  stw addr=%d <-- val=%d" % (dst, src)
        elif op == IR_STB:
            # addr, var | (var), var
            dst = resolve_addr_or_indirect_var(var_tbl, tup[1])
            src = resolve_var(var_tbl, tup[2])
            val = src & 0xFF
            lstate.stb(dst, val)
            if debug_flag:
                print "  stb addr=%d <-- val=%d" % (dst, val)
        elif op == IR_SET:
            var = tup[1]
            val = tup[2]
            assert_is_var(var)
            assert_is_var_or_const(val)
            if is_var(val):
                val = resolve_var(var_tbl, val)
            set_var(var_tbl, var, val)
            if val == 0:
                is_eql = True
            else:
                is_eql = False
            if debug_flag:
                print "  set var=%s <-- val=%d eql_flag=%s" % (var, val, str(is_eql))
        elif op == IR_CMP:
            arg1 = resolve_var(var_tbl, tup[1])
            arg2 = resolve_var_or_const(var_tbl, tup[2])
            if arg1 == arg2:
                is_eql = True
            else:
                is_eql = False
            if debug_flag:
                print "  cmp", arg1, "vs", arg2, "flag=", is_eql
        elif op == IR_BEQ:
            dst_lab = tup[1]
            assert_is_code_label(dst_lab)
            is_taken = False
            if is_eql == True:
                iptr = label2idx[dst_lab]
                is_taken = True
            if debug_flag:
                print "  beq taken=", is_taken, "iptr=", iptr
        elif op == IR_BNE:
            dst_lab = tup[1]
            assert_is_code_label(dst_lab)
            is_taken = False
            if is_eql == False:
                iptr = label2idx[dst_lab]
                is_taken = True
            if debug_flag:
                print "  beq taken=", is_taken, "iptr=", iptr
        elif op == IR_BR:
            dst_lab = tup[1]
            assert_is_code_label(dst_lab)
            iptr = label2idx[dst_lab]
            if debug_flag:
                print "  br iptr=", iptr
        elif op == IR_NOP:
            if debug_flag:
                print "  nop"
        elif op == IR_ADD:
            arg1 = resolve_var(var_tbl, tup[1])
            arg2 = resolve_var_or_const(var_tbl, tup[2])
            arg1 += arg2
            set_var(var_tbl, tup[1], arg1)
            if debug_flag:
                print "  add", tup[1], arg1
        elif op == IR_RET:
            val = resolve_var(var_tbl, tup[1])
            if debug_flag:
                print "  ret", val
            return val
        elif op == IR_COM:
            if debug_flag:
                print "  com", tup[1]
        elif op == IR_CALL:
            dst_var = tup[1]
            assert_is_var(dst_var)
            obj_id = resolve_var_or_const(var_tbl, tup[2])
            obj_obj = escape.get_obj_from_id(obj_id)
            method = tup[3]
            assert type(method) is str
            func = getattr(obj_obj, method)
            if len(tup)==4:
                v = func()
            else:
                func_args = []
                for item in tup[4:]:
                    if item.startswith("var_"):
                        val = resolve_var(var_tbl, item)
                        func_args.append(val)
                    elif type(item) is int:
                        func_args.append(val)
                    else:
                        assert None, "Unknown arg type"
                func_args = tuple(func_args)
                v = func(*func_args)
            set_var(var_tbl, dst_var, v)
            if debug_flag:
                print "  call", dst_var, "<--", v
        elif op == IR_DATA:
            if debug_flag:
                print "  data", tup[1]
        elif op == IR_GPARM:
            dst_var = tup[1]
            assert_is_var(dst_var)
            op_num = tup[2]
            assert op_num==0 or op_num==1
            if op_num==0:
                val = id(code_obj)
            else:
                val = id(lstate)
            set_var(var_tbl, dst_var, val)
            if debug_flag:
                print "  gparm", dst_var, val
        else:
            assert None, "Unknown op code=%d" % op
        pass
    return 1
