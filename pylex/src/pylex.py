import sys
import pdb

sys.path.append("/home/ramb/src/pylex/src/build/lib.linux-i686-2.5")
import escape

code = escape.code

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
        self.next_avail_state = 1

        self.nfa_obj          = None
        self.dfa_obj          = None
        self.iform            = None

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
        self.pats.append((pat, action))
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
        
        iform = compile_to_intermediate_form(self, the_dfa)
        return iform

    def build_dfa(self):
        self.dfa_obj = self.nfa_obj.convert_to_dfa()
        return self.dfa_obj

    def compile_to_iform(self):
        self.iform = compile_to_intermediate_form(self, self.dfa_obj)
        return self.iform

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
## addressing modes: (reg) -- reg_indirect - use reg as an address
## const - any integer - no worry about too large ints for now
## addr - any integer
##
## register: string: reg_<num>
## label   : string: lab_<num>  -- code label
## dlab    : string: dlab_<num> -- data label
##
IFORM_LABEL   =  0 # label
IFORM_DATA    =  1 # dlabel, string | dlabel, int 
IFORM_LDW     =  2 # reg, addr  | reg, (reg) | reg, dlab
IFORM_LDB     =  3 # reg, addr  | reg, (reg) | reg, dlab
IFORM_STW     =  4 # addr, reg  | (reg), reg | dlab, reg
IFORM_STB     =  5 # addr, reg  | (reg), reg | dlab, reg
IFORM_SET     =  6 # reg, const
IFORM_CMP     =  7 # reg, reg   | reg, const
IFORM_BEQ     =  8 # label
IFORM_BNE     =  9 # label
IFORM_BR      = 10 # label
IFORM_NOP     = 11 #
IFORM_ADD     = 12 # reg, const | reg, reg
IFORM_RET     = 13 # reg
IFORM_COM     = 14 # comment
IFORM_CALL    = 15 # addr, <arg>...<arg> | reg, <arg>...<arg>


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
    IFORM_CALL     : "call"
    }

iform_names = ['iform_label', 'iform_data',
               'iform_ldw', 'iform_ldb',
               'iform_stw', 'iform_stb',
               'iform_set',
               'iform_cmp', 'iform_beq', 'iform_bne', 'iform_br',
               'iform_nop',
               'iform_add',
               'iform_ret',
               'iform_com', 'iform_call']

####################################################

def iform_label(lab):
    assert_is_label(lab)
    return (IFORM_LABEL, lab)

def iform_data(dlab, val):
    assert_is_dlabel(dlab)
    return (IFORM_DATA, dlab, val)

def iform_ldw(dst, src):
    assert_is_reg(dst)
    assert_is_addr_or_indirect_reg_or_dlab(src)
    return (IFORM_LDW, dst, src)

def iform_ldb(dst, src):
    assert_is_reg(dst)
    assert_is_addr_or_indirect_reg_or_dlab(src)
    return (IFORM_LDB, dst, src)

def iform_stw(dst, src):
    assert_is_addr_or_indirect_reg_or_dlab(dst)
    assert_is_reg(src)
    return (IFORM_STW, dst, src)

def iform_stb(dst, src):
    assert_is_addr_or_indirect_reg_or_dlab(dst)
    assert_is_reg(src)
    return (IFORM_STB, dst, src)

def iform_set(reg, val):
    assert_is_reg(reg)
    assert_is_const(val)
    return (IFORM_SET, reg, val)

def iform_cmp(v1, v2):
    assert_is_reg(v1)
    assert_is_reg_or_const(v2)
    return (IFORM_CMP, v1, v2)

def iform_beq(lab):
    assert_is_label(lab)
    return (IFORM_BEQ, lab)

def iform_bne(lab):
    assert_is_label(lab)
    return (IFORM_BNE, lab)

def iform_br(lab):
    assert_is_label(lab)
    return (IFORM_BR, lab)

def iform_nop():
    return (IFORM_NOP,)

def iform_add(reg, v):
    assert_is_reg(reg)
    assert_is_reg_or_const(v)
    return (IFORM_ADD, reg, v)

def iform_ret(reg):
    assert_is_reg(reg)
    return (IFORM_RET, reg)

def iform_com(txt):
    return (IFORM_COM, txt)

def iform_call(func, *args):
    assert_is_addr_or_reg(func)
    tmp = [IFORM_CALL, func]
    tmp.extend(args)
    return tuple(tmp)

####################################################

def str_iform_label(tup):
    assert len(tup)==2 and tup[0]==IFORM_LABEL
    assert_is_label(tup[1])
    return "%s:" % tup[1]

def str_iform_data(tup):
    assert len(tup)==3 and tup[0]==IFORM_DATA
    assert_is_dlabel(tup[1])
    return "%s:  data: %s" % (tup[1], str(tup[2]))

def str_iform_ldw(tup):
    assert len(tup)==3
    assert tup[0]==IFORM_LDW
    assert_is_reg(tup[1])
    assert_is_addr_or_indirect_reg_or_dlab(tup[2])
    if type(tup[2]) is str:
        return "    ldw %s <-- %s" % (tup[1], tup[2])
    else:
        return "    ldw %s <-- %d" % (tup[1], tup[2])

def str_iform_ldb(tup):
    assert len(tup)==3 and tup[0]==IFORM_LDB
    assert_is_reg(tup[1])
    assert_is_addr_or_indirect_reg_or_dlab(tup[2])
    if type(tup[2]) is str:
        return "    ldb %s <-- %s" % (tup[1], tup[2])
    else:
        return "    ldb %s <-- %d" % (tup[1], tup[2])

def str_iform_stw(tup):
    assert len(tup)==3 and tup[0]==IFORM_STW
    assert_is_addr_or_indirect_reg_or_dlab(tup[1])
    assert_is_reg(tup[2])
    if type(tup[1]) is str:
        return "    stw %s <-- %s" % (tup[1], tup[2])
    else:
        return "    stw %s <-- %d" % (tup[1], tup[2])

def str_iform_stb(tup):
    assert len(tup)==3
    assert tup[0]==IFORM_STB
    assert_is_addr_or_indirect_reg_or_dlab(tup[1])
    assert_is_reg(tup[2])
    if type(tup[1]) is str:
        return "    stb %s <-- %s" % (tup[1], tup[2])
    else:
        return "    stb %s <-- %d" % (tup[1], tup[2])

def str_iform_set(tup):
    assert len(tup) == 3 and tup[0] == IFORM_SET
    assert_is_reg(tup[1])
    assert_is_const(tup[2])
    return "    set %s <-- %d" % (tup[1], tup[2])

def str_iform_cmp(tup):
    assert len(tup)==3 and tup[0]==IFORM_CMP
    assert_is_reg(tup[1])
    assert_is_reg_or_const(tup[2])
    if type(tup[2]) is str:
        return "    cmp %s, %s" % (tup[1], tup[2])
    else:
        return "    cmp %s, %d" % (tup[1], tup[2])

def str_iform_beq(tup):
    assert len(tup)==2 and tup[0]==IFORM_BEQ
    assert_is_label(tup[1])
    return "    beq %s" % (tup[1])

def str_iform_bne(tup):
    assert len(tup)==2 and tup[0]==IFORM_BNE
    assert_is_label(tup[1])
    return "    bne %s" % (tup[1])

def str_iform_br(tup):
    assert len(tup)==2 and tup[0]==IFORM_BR
    assert_is_label(tup[1])
    return "    br %s" % (tup[1])

def str_iform_nop(tup):
    assert len(tup)==1 and tup[0]==IFORM_NOP
    return "    nop"

def str_iform_add(tup):
    assert len(tup)==3 and tup[0]==IFORM_ADD
    assert_is_reg(tup[1])
    assert_is_reg_or_const(tup[2])
    if type(tup[2]) is str:
        return "    add %s <-- %s,%s" % (tup[1], tup[1], tup[2])
    else:
        return "    add %s <-- %s,%d" % (tup[1], tup[1], tup[2])

def str_iform_ret(tup):
    assert len(tup)==2 and tup[0]==IFORM_RET
    assert_is_reg(tup[1])
    return "    ret %s" % tup[1]

def str_iform_com(tup):
    assert len(tup)==2 and tup[0]==IFORM_COM
    assert_is_reg(tup[1])
    return "#%s" % tup[1]

def str_iform_call(tup):
    assert tup[0]==IFORM_CALL
    args = ", ".join(tup[1:])
    return "    call " + args

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
    IFORM_CALL     : str_iform_call
    }

####################################################

def assert_is_reg(r):
    assert r.startswith("reg_")
    return

def assert_is_addr_or_indirect_reg_or_dlab(arg):
    assert type(arg) in (int,long) \
           or (arg.startswith("(reg_") and arg.endswith(")")) \
           or arg.startswith("dlab_")
    return

def assert_is_label(l):
    assert l.startswith("lab_")
    return

def assert_is_dlabel(l):
    assert l.startswith("dlab_")
    return

def assert_is_reg_or_const(r):
    assert (type(r) is str and r.startswith("reg_")) or type(r) is int
    return

def assert_is_const(r):
    assert type(r) in (int, long)
    return

def assert_is_addr_or_reg(v):
    assert type(v) in (int,long) or v.startswith("reg_")
    return
    
####################################################

def assert_is_byte(v):
    assert type(v) is int
    assert v >= 0 and v <= 255
    return

####################################################

class iform_code(object):
    def __init__(self, lexer_obj):
        self.lexer              = lexer_obj
        self.all_regs           = []
        self.str_ptr_reg        = None
        self.data_reg           = None
        self.next_avail_reg_num = 1
        self.instructions       = []
        self.call_method_addr   = escape.get_func_addr("PyObject_CallMethod")
        self.lbuf               = None

        symtab = globals()
        for f in iform_names:
            func_obj = symtab[f]
            setattr(self, "make_" + f, func_obj)

        pass

    ####################
    ##
    ## main user API
    ##
    ####################
    def get_token(self):
        return None

    def set_buffer(self, lbuf):
        self.lbuf = lbuf
        return

    ####################
    def make_new_register(self):
        r = "reg_%d" % self.next_avail_reg_num
        self.next_avail_reg_num += 1
        self.all_regs.append(r)
        return r

    def make_std_registers(self):
        self.str_ptr_reg  = self.make_new_register()
        self.data_reg     = self.make_new_register()
        return

    def set_str_ptr_reg(self, val):
        self.str_ptr_reg = val
        return

    def print_instructions(self, opt_list=None):
        if opt_list:
            tmp = opt_list
        else:
            tmp = self.instructions
        for tup in tmp:
            op     = tup[0]
            func   = instr2pfunc[op]
            s = func(tup)
            print s
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
    pass

####################################################
####################################################
##
## intermediate form generator
##
####################################################
####################################################
def compile_to_intermediate_form(lexer, dfa_obj):
    code = iform_code(lexer)
    code.make_std_registers()
    for i, s in enumerate(dfa_obj.states):
        s.label = "lab_%d" % i

    code.add_iform_label("lab_main1")
    code.add_iform_set(code.str_ptr_reg, 0)
    code.add_iform_label("lab_main2")

    for s in dfa_obj.states:
        tmp = compile_one_node(code, s, dfa_obj)
        code.instructions.extend(tmp)

    return code

def compile_one_node(code, state, dfa_obj):
    lst = []
    code.ladd_iform_com(lst, "begin " + str(state))
    code.ladd_iform_label(lst, state.label)
    if len(state.out_chars) > 0:
        ld_src = "(" + code.str_ptr_reg + ")"
        code.ladd_iform_ldb(lst, code.data_reg, ld_src)
        code.ladd_iform_add(lst, code.str_ptr_reg, 1)
    if state.user_action:
        code.ladd_iform_call(lst, code.call_method_addr, )
        code.ladd_iform_set(lst, code.data_reg, state.user_action)
        code.ladd_iform_ret(lst, code.data_reg)
        return lst
    for ch in state.out_chars:
        k = (state, ch)
        dst = dfa_obj.trans_tbl[k]
        assert len(dst) == 1
        dst = dst[0]
        code.ladd_iform_cmp(lst, code.data_reg, ord(ch))
        code.ladd_iform_beq(lst, dst.label)
    code.ladd_iform_set(lst, code.data_reg, 0)
    code.ladd_iform_ret(lst, code.data_reg)
    return lst

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
    r = escape.code()
    return r

####################################################
####################################################
####################################################
class simulator(object):
    def __init__(self, mem_size=100):
        # each pos in memory _must_ store an int: 0 <= val <= 255
        # basically an 8 bit quantity
        self.memory           = list((None,)*mem_size)
        self.registers        = {}
        self.label2pos        = {}
        self.is_eql           = False
        self.is_little_endian = True
        self.mem_size         = mem_size
        pass

    def set_memory(self, m):
        for i, ch in enumerate(m):
            self.memory[i] = ord(ch)
        return

    def set_register(self, r, v):
        assert r in self.registers
        self.registers[r] = v
        return

    def do_sim(self, code, start_lab="lab_main1"):
        for r in code.all_regs:
            self.registers[r] = 77
        for idx, tup in enumerate(code.instructions):
            if tup[0] == IFORM_LABEL:
                self.label2pos[tup[1]] = idx

        start_pos = self.label2pos[start_lab]
        code.set_str_ptr_reg(start_pos)

        iptr = 0
        while True:
            tup = code.instructions[iptr]
            iptr += 1
            op = tup[0]
            if op == IFORM_LABEL:
                pass
            elif op == IFORM_LDW:
                # reg, addr | reg, (reg)
                dst = tup[1]
                assert_is_reg(dst)
                src = self.resolve_addr_or_indirect_reg(tup[2])
                if self.is_little_endian:
                    val = self.do_little_endian_load_w(src)
                else:
                    val = self.do_big_endian_load_w(src)
                self.set_register(dst, val)
                if val == 0:
                    self.is_eql = True
                else:
                    self.is_eql = False
            elif op == IFORM_LDB:
                # reg, addr | reg, (reg)
                dst = tup[1]
                assert_is_reg(dst)
                src = self.resolve_addr_or_indirect_reg(tup[2])
                val = self.do_load_b(src)
                assert_is_byte(val)
                self.set_register(dst, val)
                if val == 0:
                    self.is_eql = True
                else:
                    self.is_eql = False
            elif op == IFORM_STW:
                # addr, reg | (reg), reg
                dst = self.resolve_addr_or_indirect_reg(tup[1])
                src = self.resolve_reg(tup[2])
                if self.is_little_endian:
                    self.do_little_endian_store_w(dst, src)
                else:
                    self.do_big_endian_store_w(dst, src)
            elif op == IFORM_STB:
                # addr, reg | (reg), reg
                dst = self.resolve_addr_or_indirect_reg(tup[1])
                src = self.resolve_reg(tup[2])
                self.do_store_b(dst, src & 0xFF)
            elif op == IFORM_SET:
                reg = tup[1]
                val = tup[2]
                assert_is_reg(reg)
                assert_is_const(val)
                self.set_register(reg, val)
            elif op == IFORM_CMP:
                arg1 = self.resolve_reg(tup[1])
                arg2 = self.resolve_reg_or_const(tup[2])
                if arg1 == arg2:
                    self.is_eql = True
                else:
                    self.is_eql = False
            elif op == IFORM_BEQ:
                dst_lab = tup[1]
                assert_is_label(dst_lab)
                if self.is_eql == True:
                    iptr = self.label2pos[dst_lab]
            elif op == IFORM_BNE:
                dst_lab = tup[1]
                assert_is_label(dst_lab)
                if self.is_eql == False:
                    iptr = self.label2pos[dst_lab]
            elif op == IFORM_BR:
                dst_lab = tup[1]
                assert_is_label(dst_lab)
                iptr = self.label2pos[dst_lab]
            elif op == IFORM_NOP:
                pass
            elif op == IFORM_ADD:
                arg1 = self.resolve_reg(tup[1])
                arg2 = self.resolve_reg_or_const(tup[2])
                arg1 += arg2
                self.set_register(tup[1], arg1)
            elif op == IFORM_RET:
                val = self.resolve_reg(tup[1])
                return val
            elif op == IFORM_COM:
                pass
            elif op == IFORM_CALL:
                pass
            elif op == IFORM_DATA:
                pass
            else:
                assert None, "Unknown op code"
        return

    #######

    def resolve_reg(self, reg):
        assert_is_reg(reg)
        v = self.registers[reg]
        return v

    def resolve_addr_or_indirect_reg(self, arg):
        if type(arg) is str:
            assert arg[0] == "(" and arg[-1]==")"
            reg = arg[1:-1]
            assert_is_reg(reg)
            v = self.registers[reg]
            return v
        assert_is_const(arg)
        return arg

    def resolve_reg_or_const(self, arg):
        if type(arg) is str:
            assert_is_reg(arg)
            v = self.registers[arg]
            return v
        assert_is_const(arg)
        return arg

    def resolve_const(self, arg):
        assert_is_const(arg)
        return arg

    #######

    def do_little_endian_load_w(self, addr):
        b0 = 0xFF & self.memory[addr + 0]
        b1 = 0xFF & self.memory[addr + 1]
        b2 = 0xFF & self.memory[addr + 2]
        b3 = 0xFF & self.memory[addr + 3]
        v = (b3 << 24) | (b2 << 16) | (b1 << 8) | b0
        return v

    def do_big_endian_load_w(self, addr):
        b0 = 0xFF & self.memory[addr + 0]
        b1 = 0xFF & self.memory[addr + 1]
        b2 = 0xFF & self.memory[addr + 2]
        b3 = 0xFF & self.memory[addr + 3]
        v = (b0 << 24) | (b1 << 16) | (b2 << 8) | b3
        return v

    def do_little_endian_store_w(self, addr, val):
        b0 =  val & 0x000000FF
        b1 = (val & 0x0000FF00) >>  8
        b2 = (val & 0x00FF0000) >> 16
        b3 = (val & 0xFF000000) >> 24
        self.memory[addr + 0] = b0
        self.memory[addr + 1] = b1
        self.memory[addr + 2] = b2
        self.memory[addr + 3] = b3
        return

    def do_big_endian_store_w(self, addr, val):
        b0 =  val & 0x000000FF
        b1 = (val & 0x0000FF00) >>  8
        b2 = (val & 0x00FF0000) >> 16
        b3 = (val & 0xFF000000) >> 24
        self.memory[addr + 0] = b3
        self.memory[addr + 1] = b2
        self.memory[addr + 2] = b1
        self.memory[addr + 3] = b0
        return

    def do_store_b(self, addr, val):
        assert addr >= 0 and addr < self.mem_size
        assert_is_byte(val)
        self.memory[addr] = val
        return

    def do_load_b(self, addr):
        assert addr >= 0 and addr < self.mem_size
        v = self.memory[addr]
        assert_is_byte(v)
        return v

    pass
