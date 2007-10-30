import pdb

class node(object):
    next_avail_num = 0
    __slots__ = ["name", "next_tbl", "action", "is_accepting", "priority"]
    def __init__(self):
        self.name         = "Node_%d" % node.next_avail_num
        node.next_avail_num += 1
        self.next_tbl     = {}
        self.action       = None
        self.is_accepting = False
        self.priority     = None
        return

    def must_get_next_node(self, ch_str_or_tup):
        assert type(ch_str_or_tup) is str or type(ch_str_or_tup) is tuple
        ch0 = ch_str_or_tup[0]
        if not self.next_tbl.has_key(ch0):
            self.next_tbl[ch0] = node()
        the_node = self.next_tbl[ch0]
        for ch in ch_str_or_tup[1:]:
            self.next_tbl[ch] = the_node
        return the_node

    def maybe_get_next_node(self, ch):
        if not self.next_tbl.has_key(ch):
            return None
        result = self.next_tbl[ch]
        return result

    def num_out_edges(self):
        return len(self.next_tbl.items())

    def show_tbl(self):
        print "Node table"
        for ch, nxt in self.next_tbl.items():
            print "    ", ch, "--->", nxt
        print "Done."
        return

    def __str__(self):
        result = [self.name]
        result.append("is_accepting=" + str(self.is_accepting))
        result.append("priority=" + str(self.priority))
        for ch, node in self.next_tbl.items():
            result.append("ch %s --> node %s" % (ch, node.name))
        return "\n".join(result)

    pass

##########################################################################
class fsa(object):
    def __init__(self, lexer):
        self.next_avail_state = 1
        self.init_state       = 0
        self.trans_tbl        = {}
        self.states           = []
        self.lexer            = lexer
        return

    def get_new_state(self):
        s = self.next_avail_state
        self.next_avail_state += 1
        return s

    ##
    ## debug routines
    ##
    def __str__(self):
        result = ""
        for k,v in self.trans_tbl.iteritems():
            result = result + str(k) + "->" + str(v) + "\n"
        result = result + "accepting=" + str(self.accepting_states) + "\n"
        return result

    pass

##########################################################################
class nfa(fsa):
    def __init__(self, lexer, txt=None):
        super(nfa, self).__init__(lexer)
        self.accepting_states = []

        if txt is not None:
            assert len(txt) == 1
            s2 = self.get_new_state()
            self.add_edge(self.init_state, txt, s2)
            self.set_accepting_state(s2)

        pass

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
    ## merge related funcs
    ##
    def copy_edges(self, other_nfa, offset):
        for k,v in other_nfa.trans_tbl.iteritems():
            st, ch = k
            for dst in v:
                self.add_edge(st + offset, ch, dst + offset)
        return

    ##
    ## dfa construction support
    ##
    def e_closure(self, start_list):
        if type(start_list) is not list:
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
        if type(st_list) is not list:
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
    def convert_to_dfa(self):
        result = dfa(self.lexer)

        all_ch = [chr(i) for i in range(127)]
        seen = {}
        start = self.e_closure(self.init_state)
        new_states = [start]
        while new_states:
            s = new_states.pop()
            seen[s] = True
            for ch in all_ch:
                s2 = self.move(s, ch)
                if s2 not in seen:
                    new_states.append(s2)
                    
        return result
        

    pass

##########################################################################
class dfa(object):
    def __init__(self, lexer):
        super(dfa, self).__init__(lexer)
        return
    pass

##########################################################################
def do_nfa_ccat(lexer, nfa1, nfa2):
    result = nfa(lexer)
    offset = nfa1.next_avail_state
    result.copy_edges(nfa1, 0)
    result.copy_edges(nfa2, offset)

    for s1 in nfa1.accepting_states:
        result.add_edge(s1, None, nfa2.init_state + offset)

    for s2 in nfa2.accepting_states:
        result.set_accepting_state(s2 + offset)

    return result

def do_nfa_pipe(lexer, nfa1, nfa2):
    result = nfa(lexer)
    offset = nfa1.next_avail_state
    result.copy_edges(nfa1, 1)
    result.copy_edges(nfa2, offset + 1)

    for s1 in nfa1.accepting_states:
        result.set_accepting_state(s1 + 1)
    for s2 in nfa2.accepting_states:
        result.set_accepting_state(s2 + offset + 1)

    result.add_edge(result.init_state, None, nfa1.init_state + 1)
    result.add_edge(result.init_state, None, nfa2.init_state + offset + 1)
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

class lexer(object):
    def __init__(self):
        self.pats        = []
        self.start       = node()
        self.nfa_obj     = None
        self.cur_result  = None
        self.cur_pattern = None
        return

    def define_token(self, pat, action):
        self.pats.append((pat, action))
        return

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
