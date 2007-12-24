import sys
import os
import os.path
import dl
import pdb


sys.path.append("/home/ramb/src/pylex/src/build/lib.linux-i686-2.5")
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
            return "state_%d_act=%d" % (self.num, self.user_action)
        return "state_%d" % self.num
    pass

class lexer(object):
    def __init__(self):
        self.pats             = []
        self.actions          = [self.runtime_fill_buffer,
                                 self.runtime_unhandled_input]

        self.next_avail_state = 1

        self.nfa_obj          = None
        self.dfa_obj          = None
        self.iform            = None
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
        
        iform = self.compile_to_intermediate_form()
        return iform

    def build_dfa(self):
        self.dfa_obj = self.nfa_obj.convert_to_dfa()
        return self.dfa_obj

    def add_end_of_buf_edges(self, dfa_obj):
        assert dfa_obj.has_end_of_buf_edges == False, "Edges already present"
        dfa_obj.has_end_of_buf_edges = True

        end1 = dfa_obj.get_new_state()
        end2 = dfa_obj.get_new_state()
        end3 = dfa_obj.get_new_state()

        dfa_obj.add_edge(end1, '\x00', end2)
        dfa_obj.add_edge(end2, '\x00', end3)

        dfa_obj.set_accepting_state(end3)
        end3.user_action = 1
        return

    def compile_to_machine_code(self):
        self.code_obj = compile_to_x86_32(self.iform)
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
    ## intermediate form generator
    ##
    ## General approach: in each state get the next char
    ## and add 1 to the next char pointer. The char is compared
    ## to all outgoing edges from the current state. When a
    ## match is found, branch to that state.
    ##
    ## The end of buffer detection is stolen from Flex. Two
    ## null chars are placed sequentially. All states have
    ## out edges to detect this case. Hopefully the two-null
    ## char sequence is very rare in the users input.
    ##
    ## The code object should be called like this
    ## code_obj_addr(code_obj, lex_state)
    ##
    ## initial code sequence
    ##   load second arg
    ##   add offset to get address of lex_state->next_char_ptr
    ##   deref ptr to get actual next_char_ptr
    ##
    ## each state looks roughly like this
    ##   if this is an accepting state - save the
    ##   char pointer, return value, and set the
    ##   flag to indicate saved data is available
    ##
    ##   load cur char
    ##
    ##   branch to appopriate state based on char
    ##
    ##   if no appropriate char is found - then the
    ##   lexer is wedged - since this is an input that
    ##   is not matched by any user pattern - return a 1
    ##
    ## The return value from the lexer is always an integer, which
    ## is used as an index into the self.actions list to find out
    ## what actual action to perform. The first two entries in the
    ## actions list are fill buffer and unhandled input. Therefore
    ## if the lexer returns 0 a fill buffer operation is performed
    ## and a 1 indicates an unmatched input.
    ##
    ####################################################
    ####################################################
    def compile_to_intermediate_form(self):
        self.iform = iform_code(self)
        c = self.iform
        c.make_std_vars()
        for i, s in enumerate(self.dfa_obj.states):
            s.label = "lab_%d" % i

        c.add_iform_com("main")
        c.add_iform_gparm(c.tmp_var1, 1)
        c.add_iform_com("get saved data ptr")
        c.add_iform_add(c.tmp_var1, c.char_ptr_offset)
        c.add_iform_ldw(c.str_ptr_var, c.make_indirect_var(c.tmp_var1))
        c.add_iform_com("no valid data yet")
        c.add_iform_set(c.saved_valid, 0)

        for s in self.dfa_obj.states:
            tmp = self.compile_one_node(c, s)
            c.instructions.extend(tmp)

        return c

    def compile_one_node(self, c, state):
        lst = []
        c.ladd_iform_com(lst, "begin " + str(state))
        c.ladd_iform_label(lst, state.label)
        if len(state.out_chars) > 0:
            ld_src = c.make_indirect_var(c.str_ptr_var)
            c.ladd_iform_ldb(lst, c.data_var, ld_src)
            c.ladd_iform_add(lst, c.str_ptr_var, 1)

            for ch in state.out_chars:
                k = (state, ch)
                dst = self.dfa_obj.trans_tbl[k]
                assert len(dst) == 1
                dst = dst[0]
                c.ladd_iform_cmp(lst, c.data_var, ord(ch))
                c.ladd_iform_beq(lst, dst.label)

        if state.user_action:
            c.ladd_iform_stw(lst, c.make_indirect_var(c.tmp_var1),
                             c.str_ptr_var)
            c.ladd_iform_set(lst, c.data_var, state.user_action)
            c.ladd_iform_ret(lst, c.data_var)
            return lst
        c.ladd_iform_com(lst, "unmatched input")
        c.ladd_iform_set(lst, c.data_var, 1)
        c.ladd_iform_ret(lst, c.data_var)
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
## regexps --> nfa --> dfa --> iform code --> x86 code
##
## iform code : intermediate form of machine code to
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
IFORM_LABEL   =  0 # label
IFORM_DATA    =  1 # dlabel, string | dlabel, int 
IFORM_LDW     =  2 # var, addr  | var, (var) | var, dlab
IFORM_LDB     =  3 # var, addr  | var, (var) | var, dlab
IFORM_STW     =  4 # addr, var  | (var), var | dlab, var
IFORM_STB     =  5 # addr, var  | (var), var | dlab, var
IFORM_SET     =  6 # var, const | var, var
IFORM_CMP     =  7 # var, var   | var, const
IFORM_BEQ     =  8 # label
IFORM_BNE     =  9 # label
IFORM_BR      = 10 # label
IFORM_NOP     = 11 #
IFORM_ADD     = 12 # var, const | var, var
IFORM_RET     = 13 # var
IFORM_COM     = 14 # comment
IFORM_CALL    = 15 # var, addr, <arg>...<arg> | var, var, <arg>...<arg>
IFORM_GPARM   = 16 # var, <parm_num>

instr2txt = {
    IFORM_LABEL    : "label",
    IFORM_DATA     : "data",
    IFORM_LDW      : "ldw",
    IFORM_LDB      : "ldb",
    IFORM_STW      : "stw",
    IFORM_STB      : "stb",
    IFORM_SET      : "set",
    IFORM_CMP      : "cmp",
    IFORM_BEQ      : "beq",
    IFORM_BNE      : "bne",
    IFORM_BR       : "br",
    IFORM_NOP      : "nop",
    IFORM_ADD      : "add",
    IFORM_RET      : "ret",
    IFORM_COM      : "com",
    IFORM_CALL     : "call",
    IFORM_GPARM    : "gparm"
    }

iform_names = ['iform_label', 'iform_data',
               'iform_ldw', 'iform_ldb',
               'iform_stw', 'iform_stb',
               'iform_set',
               'iform_cmp', 'iform_beq', 'iform_bne', 'iform_br',
               'iform_nop',
               'iform_add',
               'iform_ret',
               'iform_com',
               'iform_call', 'iform_gparm']

####################################################

def iform_label(lab):
    assert_is_code_label(lab)
    return (IFORM_LABEL, lab)

def iform_data(dlab, val):
    assert_is_dlabel(dlab)
    return (IFORM_DATA, dlab, val)

def iform_ldw(dst, src):
    assert_is_var(dst)
    assert_is_addr_or_indirect_var_or_dlab(src)
    return (IFORM_LDW, dst, src)

def iform_ldb(dst, src):
    assert_is_var(dst)
    assert_is_addr_or_indirect_var_or_dlab(src)
    return (IFORM_LDB, dst, src)

def iform_stw(dst, src):
    assert_is_addr_or_indirect_var_or_dlab(dst)
    assert_is_var(src)
    return (IFORM_STW, dst, src)

def iform_stb(dst, src):
    assert_is_addr_or_indirect_var_or_dlab(dst)
    assert_is_var(src)
    return (IFORM_STB, dst, src)

def iform_set(var, val):
    assert_is_var(var)
    assert_is_var_or_const(val)
    return (IFORM_SET, var, val)

def iform_cmp(v1, v2):
    assert_is_var(v1)
    assert_is_var_or_const(v2)
    return (IFORM_CMP, v1, v2)

def iform_beq(lab):
    assert_is_code_label(lab)
    return (IFORM_BEQ, lab)

def iform_bne(lab):
    assert_is_code_label(lab)
    return (IFORM_BNE, lab)

def iform_br(lab):
    assert_is_code_label(lab)
    return (IFORM_BR, lab)

def iform_nop():
    return (IFORM_NOP,)

def iform_add(var, v):
    assert_is_var(var)
    assert_is_var_or_const(v)
    return (IFORM_ADD, var, v)

def iform_ret(var):
    assert_is_var(var)
    return (IFORM_RET, var)

def iform_com(txt):
    return (IFORM_COM, txt)

def iform_call(var, func, *args):
    assert_is_var(var)
    assert_is_addr_or_var(func)
    tmp = [IFORM_CALL, var, func]
    tmp.extend(args)
    return tuple(tmp)

def iform_gparm(var, pnum):
    assert_is_var(var)
    assert_is_const(pnum)
    return (IFORM_GPARM, var, pnum)

####################################################

def str_iform_label(tup):
    assert len(tup)==2 and tup[0]==IFORM_LABEL
    assert_is_code_label(tup[1])
    return "%s:" % tup[1]

def str_iform_data(tup):
    assert len(tup)==3 and tup[0]==IFORM_DATA
    assert_is_dlabel(tup[1])
    return "%s:  data: %s" % (tup[1], str(tup[2]))

def str_iform_ldw(tup):
    assert len(tup)==3
    assert tup[0]==IFORM_LDW
    assert_is_var(tup[1])
    assert_is_addr_or_indirect_var_or_dlab(tup[2])
    if type(tup[2]) is str:
        return "    ldw %s <-- %s" % (tup[1], tup[2])
    else:
        return "    ldw %s <-- %d" % (tup[1], tup[2])

def str_iform_ldb(tup):
    assert len(tup)==3 and tup[0]==IFORM_LDB
    assert_is_var(tup[1])
    assert_is_addr_or_indirect_var_or_dlab(tup[2])
    if type(tup[2]) is str:
        return "    ldb %s <-- %s" % (tup[1], tup[2])
    else:
        return "    ldb %s <-- %d" % (tup[1], tup[2])

def str_iform_stw(tup):
    assert len(tup)==3 and tup[0]==IFORM_STW
    assert_is_addr_or_indirect_var_or_dlab(tup[1])
    assert_is_var(tup[2])
    if type(tup[1]) is str:
        return "    stw %s <-- %s" % (tup[1], tup[2])
    else:
        return "    stw %s <-- %d" % (tup[1], tup[2])

def str_iform_stb(tup):
    assert len(tup)==3
    assert tup[0]==IFORM_STB
    assert_is_addr_or_indirect_var_or_dlab(tup[1])
    assert_is_var(tup[2])
    if type(tup[1]) is str:
        return "    stb %s <-- %s" % (tup[1], tup[2])
    else:
        return "    stb %s <-- %d" % (tup[1], tup[2])

def str_iform_set(tup):
    assert len(tup) == 3 and tup[0] == IFORM_SET
    assert_is_var(tup[1])
    assert_is_var_or_const(tup[2])
    if is_var(tup[2]):
        return "    set %s <-- %s" % (tup[1], tup[2])
    else:
        return "    set %s <-- %d" % (tup[1], tup[2])

def str_iform_cmp(tup):
    assert len(tup)==3 and tup[0]==IFORM_CMP
    assert_is_var(tup[1])
    assert_is_var_or_const(tup[2])
    if type(tup[2]) is str:
        return "    cmp %s, %s" % (tup[1], tup[2])
    else:
        return "    cmp %s, %d" % (tup[1], tup[2])

def str_iform_beq(tup):
    assert len(tup)==2 and tup[0]==IFORM_BEQ
    assert_is_code_label(tup[1])
    return "    beq %s" % (tup[1])

def str_iform_bne(tup):
    assert len(tup)==2 and tup[0]==IFORM_BNE
    assert_is_code_label(tup[1])
    return "    bne %s" % (tup[1])

def str_iform_br(tup):
    assert len(tup)==2 and tup[0]==IFORM_BR
    assert_is_code_label(tup[1])
    return "    br %s" % (tup[1])

def str_iform_nop(tup):
    assert len(tup)==1 and tup[0]==IFORM_NOP
    return "    nop"

def str_iform_add(tup):
    assert len(tup)==3 and tup[0]==IFORM_ADD
    assert_is_var(tup[1])
    assert_is_var_or_const(tup[2])
    if type(tup[2]) is str:
        return "    add %s <-- %s,%s" % (tup[1], tup[1], tup[2])
    else:
        return "    add %s <-- %s,%d" % (tup[1], tup[1], tup[2])

def str_iform_ret(tup):
    assert len(tup)==2 and tup[0]==IFORM_RET
    assert_is_var(tup[1])
    return "    ret %s" % tup[1]

def str_iform_com(tup):
    assert len(tup)==2 and tup[0]==IFORM_COM
    return "#%s" % tup[1]

def str_iform_call(tup):
    assert tup[0]==IFORM_CALL
    assert_is_var(tup[1])
    dst  = tup[1]
    func = tup[2]
    tmp = [str(item) for item in tup[3:]]
    args = ", ".join(tmp)
    if is_var(func):
        return "    call %s <-- %s(%s)" % (dst, func, args)
    return "    call %s <-- %x(%s)" % (dst, func, args)

def str_iform_gparm(tup):
    assert len(tup)==3 and tup[0]==IFORM_GPARM
    assert_is_var(tup[1])
    assert_is_const(tup[2])
    return "    gparm %s <-- parm<%d>" % (tup[1], tup[2])

instr2pfunc = {
    IFORM_LABEL    : str_iform_label,
    IFORM_DATA     : str_iform_data,
    IFORM_LDW      : str_iform_ldw,
    IFORM_LDB      : str_iform_ldb,
    IFORM_STW      : str_iform_stw,
    IFORM_STB      : str_iform_stb,
    IFORM_SET      : str_iform_set,
    IFORM_CMP      : str_iform_cmp,
    IFORM_BEQ      : str_iform_beq,
    IFORM_BNE      : str_iform_bne,
    IFORM_BR       : str_iform_br,
    IFORM_NOP      : str_iform_nop,
    IFORM_ADD      : str_iform_add,
    IFORM_RET      : str_iform_ret,
    IFORM_COM      : str_iform_com,
    IFORM_CALL     : str_iform_call,
    IFORM_GPARM    : str_iform_gparm
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
    elif isinstance(arg, iform_code):
        tmp_list = arg.instructions
    elif isinstance(arg, escape.code):
        n = len(arg)
        tmp_list = [arg[i] for i in xrange(n)]
    else:
        assert type(arg) is tuple
        tmp_list = [arg]

    for tup in tmp_list:
        op = tup[0]
        if op in instr2pfunc:
            func   = instr2pfunc[op]
            s = func(tup)
            print s
        else:
            print tup
    return

####################################################
class iform_code(object):
    def __init__(self, lexer_obj):
        self.lexer              = lexer_obj
        self.all_vars           = []
        self.str_ptr_var        = None
        self.tmp_var1           = None
        self.data_var           = None
        self.next_avail_var_num = 1
        self.instructions       = []
        self.call_method_addr   = escape.get_func_addr("PyObject_CallMethod")
        self.char_ptr_offset    = escape.get_char_ptr_offset()
        self.lbuf               = None

        symtab = globals()
        for f in iform_names:
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
        self.str_ptr_var  = self.make_new_var()
        self.data_var     = self.make_new_var()
        self.saved_valid  = self.make_new_var()
        self.saved_ptr    = self.make_new_var()
        self.saved_result = self.make_new_var()
        self.tmp_var1     = self.make_new_var()
        return

    def set_str_ptr_var(self, val):
        self.str_ptr_var = val
        return

    ####################
    ## iform creator funcs
    ####################
    def add_iform_label(self, *args):
        self.instructions.append(iform_label(*args))
        return
    def add_iform_data(self, *args):
        self.instructions.append(iform_data(*args))
        return
    def add_iform_ldw(self, *args):
        self.instructions.append(iform_ldw(*args))
        return
    def add_iform_ldb(self, *args):
        self.instructions.append(iform_ldb(*args))
        return
    def add_iform_stw(self, *args):
        self.instructions.append(iform_stw(*args))
        return
    def add_iform_stb(self, *args):
        self.instructions.append(iform_stb(*args))
        return
    def add_iform_set(self, *args):
        self.instructions.append(iform_set(*args))
        return
    def add_iform_cmp(self, *args):
        self.instructions.append(iform_cmp(*args))
        return
    def add_iform_beq(self, *args):
        self.instructions.append(iform_beq(*args))
        return
    def add_iform_bne(self, *args):
        self.instructions.append(iform_bne(*args))
        return
    def add_iform_br(self, *args):
        self.instructions.append(iform_br(*args))
        return
    def add_iform_nop(self, *args):
        self.instructions.append(iform_nop(*args))
        return
    def add_iform_add(self, *args):
        self.instructions.append(iform_add(*args))
        return
    def add_iform_ret(self, *args):
        self.instructions.append(iform_ret(*args))
        return
    def add_iform_com(self, *args):
        self.instructions.append(iform_com(*args))
        return
    def add_iform_call(self, *args):
        self.instructions.append(iform_call(*args))
        return
    def add_iform_gparm(self, *args):
        self.instructions.append(iform_gparm(*args))
        return

    ####################
    ## list iform creator funcs
    ####################
    def ladd_iform_label(self, l, *args):
        l.append(iform_label(*args))
        return
    def ladd_iform_data(self, l, *args):
        l.append(iform_data(*args))
        return
    def ladd_iform_ldw(self, l, *args):
        l.append(iform_ldw(*args))
        return
    def ladd_iform_ldb(self, l, *args):
        l.append(iform_ldb(*args))
        return
    def ladd_iform_stw(self, l, *args):
        l.append(iform_stw(*args))
        return
    def ladd_iform_stb(self, l, *args):
        l.append(iform_stb(*args))
        return
    def ladd_iform_set(self, l, *args):
        l.append(iform_set(*args))
        return
    def ladd_iform_cmp(self, l, *args):
        l.append(iform_cmp(*args))
        return
    def ladd_iform_beq(self, l, *args):
        l.append(iform_beq(*args))
        return
    def ladd_iform_bne(self, l, *args):
        l.append(iform_bne(*args))
        return
    def ladd_iform_br(self, l, *args):
        l.append(iform_br(*args))
        return
    def ladd_iform_nop(self, l, *args):
        l.append(iform_nop(*args))
        return
    def ladd_iform_add(self, l, *args):
        l.append(iform_add(*args))
        return
    def ladd_iform_ret(self, l, *args):
        l.append(iform_ret(*args))
        return
    def ladd_iform_com(self, l, *args):
        l.append(iform_com(*args))
        return
    def ladd_iform_call(self, l, *args):
        l.append(iform_call(*args))
        return
    def ladd_iform_gparm(self, l, *args):
        l.append(iform_gparm(*args))
        return
    pass

####################################################
####################################################
##
## compile to actual machine code
##
####################################################
####################################################
def compile_to_vcode(iform):
    r = escape.code()
    r.set_type("vcode")
    for tup in iform.instructions:
        r.append(tup)
    return r

def compile_to_x86_32(iform):
    if 1:
        l = iform_to_asm_list_x86_32(iform)
        r = asm_list_x86_32_to_code_obj(l)
    return r

def asm_list_x86_32_to_code_obj(lines, print_asm_txt=False):
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
    for ch in b:
        code_obj.append(ord(ch))
    return code_obj

def iform_to_asm_list_x86_32(iform):
    asm_list = []

    var2offset = {}
    frame_offset = -4
    for r in iform.all_vars:
        var2offset[r] = frame_offset
        frame_offset += -4
    n_locals = len(iform.all_vars)
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

    for tup in iform.instructions:
        op = tup[0]
        if op==IFORM_LABEL:
            asm_list.append((tup[1], None, None))
        elif op==IFORM_LDW:
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
                assert None, "ldw data src label not yet handled"
            else:
                assert None, "Unknown ldw src operand type"
        elif op==IFORM_LDB:
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
        elif op==IFORM_STW:
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
        elif op==IFORM_STB:
            assert None, "op not yet supported"
        elif op==IFORM_SET:
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
        elif op==IFORM_CMP:
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
        elif op==IFORM_BEQ:
            dst_lab = tup[1]
            asm_list.append((None, "je", dst_lab))
        elif op==IFORM_BNE:
            dst_lab = tup[1]
            asm_list.append((None, "jne", dst_lab))
        elif op==IFORM_BR:
            assert None, "op not yet supported:" + instr2txt[op]
        elif op==IFORM_NOP:
            assert None, "op not yet supported:" + instr2txt[op]
        elif op==IFORM_ADD:
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
        elif op==IFORM_RET:
            var = tup[1]
            assert_is_var(var)
            offset = var2offset[var]
            asm_list.append(("#", "ret", None))
            asm_list.append((None, "movl", "%d(%%ebp), %%eax" % offset))
            asm_list.append((None, "movl", "%ebp, %esp"))
            asm_list.append((None, "popl", "%ebp"))
            asm_list.append((None, "ret", None))
        elif op==IFORM_COM:
            asm_list.append(("#", tup[1], None))
        elif op==IFORM_CALL:
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
                        asm_list.append((None, ".asciz", "\"%s\"" % a))
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
        elif op==IFORM_GPARM:
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


def run_vcode_simulation(code_obj, lstate, debug_flag=False):
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
        if tup[0] == IFORM_LABEL:
            label2idx[tup[1]] = idx
        pass

    iptr = 0
    while True:
        assert iptr >= 0 and iptr < n_instr
        tup = code_obj[iptr]
        if debug_flag:
            print "sim iptr=", iptr, "tup=", instr2txt[tup[0]], tup[1:]

        iptr += 1
        op = tup[0]
        if op == IFORM_LABEL:
            if debug_flag:
                print "  at label", tup[1]
        elif op == IFORM_LDW:
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
        elif op == IFORM_LDB:
            # var, addr | var, (var)
            dst = tup[1]
            assert_is_var(dst)
            src = resolve_addr_or_indirect_var(var_tbl, tup[2])
            val = lstate.ldb(src)
            #if not is_byte(val):
            #    pdb.set_trace()
            assert_is_byte(val)
            set_var(var_tbl, dst, val)
            if val == 0:
                is_eql = True
            else:
                is_eql = False
            if debug_flag:
                print "  ldb %s <-- %d eql_flag=%s" % (dst, val, str(is_eql))
        elif op == IFORM_STW:
            # addr, var | (var), var
            dst = resolve_addr_or_indirect_var(var_tbl, tup[1])
            src = resolve_var(var_tbl, tup[2])
            lstate.stw(dst, src)
            if debug_flag:
                print "  stw addr=%d <-- val=%d" % (dst, src)
        elif op == IFORM_STB:
            # addr, var | (var), var
            dst = resolve_addr_or_indirect_var(var_tbl, tup[1])
            src = resolve_var(var_tbl, tup[2])
            val = src & 0xFF
            lstate.stb(dst, val)
            if debug_flag:
                print "  stb addr=%d <-- val=%d" % (dst, val)
        elif op == IFORM_SET:
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
        elif op == IFORM_CMP:
            arg1 = resolve_var(var_tbl, tup[1])
            arg2 = resolve_var_or_const(var_tbl, tup[2])
            if arg1 == arg2:
                is_eql = True
            else:
                is_eql = False
            if debug_flag:
                print "  cmp", arg1, "vs", arg2, "flag=", is_eql
        elif op == IFORM_BEQ:
            dst_lab = tup[1]
            assert_is_code_label(dst_lab)
            is_taken = False
            if is_eql == True:
                iptr = label2idx[dst_lab]
                is_taken = True
            if debug_flag:
                print "  beq taken=", is_taken, "iptr=", iptr
        elif op == IFORM_BNE:
            dst_lab = tup[1]
            assert_is_code_label(dst_lab)
            is_taken = False
            if is_eql == False:
                iptr = label2idx[dst_lab]
                is_taken = True
            if debug_flag:
                print "  beq taken=", is_taken, "iptr=", iptr
        elif op == IFORM_BR:
            dst_lab = tup[1]
            assert_is_code_label(dst_lab)
            iptr = label2idx[dst_lab]
            if debug_flag:
                print "  br iptr=", iptr
        elif op == IFORM_NOP:
            if debug_flag:
                print "  nop"
        elif op == IFORM_ADD:
            arg1 = resolve_var(var_tbl, tup[1])
            arg2 = resolve_var_or_const(var_tbl, tup[2])
            arg1 += arg2
            set_var(var_tbl, tup[1], arg1)
            if debug_flag:
                print "  add", tup[1], arg1
        elif op == IFORM_RET:
            val = resolve_var(var_tbl, tup[1])
            if debug_flag:
                print "  ret", val
            return val
        elif op == IFORM_COM:
            if debug_flag:
                print "  com", tup[1]
        elif op == IFORM_CALL:
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
        elif op == IFORM_DATA:
            if debug_flag:
                print "  data", tup[1]
        elif op == IFORM_GPARM:
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
