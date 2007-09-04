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

class nfa(object):
    def __init__(self):
        self.trans_tbl        = {}
        self.states           = []
        self.next_avail_state = 1
        self.init_state       = 0
        self.accepting_states = []
        return

    def get_new_state(self):
        s = self.next_avail_state
        self.next_avail_state += 1
        return s

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

    def add_sequence(self, state0, txt):
        cur_state = state0
        for ch in txt:
            n_state = self.get_new_state()
            self.add_edge(cur_state, ch, n_state)
            cur_state = n_state
        return cur_state

    def add_choice(self, start, end, txt_list):
        for txt in txt_list:
            last_state = self.add_sequence(start, txt[:-1])
            self.add_edge(last_state, txt[-1], end)
        return
    
    pass



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

all_special_syms = (LPAREN, RPAREN, LBRACKET, RBRACKET, PIPE, PLUS, STAR, CCAT)

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
    def compile_to_nfa(self):
        assert self.nfa_obj is None

        self.nfa_obj = nfa()
        obj = self.nfa_obj

        for pat, action in self.pats:
            cur_state = obj.init_state
            parse_info = self.parse_pattern(pat)
            for item in parse_info:
                if item[0] == TEXT:
                    cur_state = obj.add_sequence(cur_state, item[1])
                    obj.set_accepting_state(cur_state)
                elif item[0] == STAR:
                    pass
                elif item[0] == PIPE:
                    pdb.set_trace()
                    start = cur_state
                    end = obj.get_new_state()
                    obj.add_choice(start, end, item[1:])
                else:
                    raise RuntimeError, "Unexpected parse node type"
                
        return

    #######################################
    ## 
    ## regexp parser
    ## 
    #######################################
    def parse_pattern(self, pat):
        self.parse_result  = []

        operators = []
        tok_list = self.tokenize_pattern(pat)
        while tok_list:
            tok = tok_list.pop()
            if type(tok) is str:
                self.parse_result.append(tok)
            else:
                operators.append(tok)
        while operators:
            op = operators.pop()
            self.parse_result.append(op)

        return self.parse_result

    ######

    def consume(self, expected):
        if expected == TEXT:
            if type(self.cur_token) is str:
                self.get_next_token()
                return
            txt_rep = self.get_cur_token_as_string()
            raise RuntimeError, "Expected normal text, but got" + txt_rep
        assert expected in all_special_syms
        if self.cur_token != expected:
            txt_rep = self.get_cur_token_as_string()
            raise RuntimeError, "did not expect actual char" + txt_rep
        self.get_next_token()
        return

    def get_next_token(self):
        if not self.all_toks:
            self.cur_token = None
            return
        self.cur_token = self.all_toks.pop(0)
        return

    def get_cur_token_as_string(self):
        if type(self.cur_token) is str:
            return "text=" + self.cur_token
        assert type(self.cur_token) is int
        return "symbol=\'%s\'" % sym2char[self.cur_token]

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
