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

char2sym = {
    '('  : LPAREN,
    ')'  : RPAREN,
    '['  : LBRACKET,
    ']'  : RBRACKET,
    '|'  : PIPE,
    '+'  : PLUS,
    '*'  : STAR
    }

all_special_syms = (LPAREN, RPAREN, LBRACKET, RBRACKET, PIPE, PLUS)

class lexer(object):
    def __init__(self):
        self.pats        = []
        self.start       = node()
        self.cur_result  = None
        self.cur_pattern = None
        return

    def define_token(self, pat, action):
        self.pats.append((pat, action))
        return

    #######################################
    ##
    #######################################
    def compile(self):
        for pat, action in self.pats:
            self.compile_one_pat(self.start, pat, action)

        return

    def compile_one_pat(self, node, pat, action):
        cur_pat  = pat
        cur_node = node

        while cur_pat:
            ch_info, cur_pat = self.get_next_chars(cur_pat)
            cur_node = cur_node.must_get_next_node(ch_info)
            pass

        cur_node.action = action
        cur_node.is_accepting = True
        return
        
    def get_next_chars(self, pat):
        ch = pat[0]

        ch2 = None
        if len(pat) > 1:
            ch2 = pat[1]

        if ch != "[" and ch2 != '|' and ch != '(':
            pat_next = pat[1:]
            if len(pat_next) == 0:
                pat_next = None
            return (ch, pat_next)

        if ch == '[':
            idx = pat.find("]")
            if idx == -1:
                raise RuntimeError, "Unable to find closing ']' char " \
                      + "in pattern: " + self.cur_pattern
            cclass = pat[1:idx]
            pat_next = pat[idx+1:]
            if len(pat_next) == 0:
                pat_next = None
            return (cclass, pat_next)

        if ch == '(':
            idx2 = pat.find(')')
            if idx2 == -1:
                raise RuntimeError, "No matching close ')' found"
            sub = pat[1:idx2]
            pat_next = pat[idx2+1:]
            return (sub, pat_next)

        assert ch2 == '|'
        if len(pat) > 2:
            ch3 = pat[2]
            pat_next = pat[3:]
        else:
            raise RuntimeError, "Illegal use of alternation character | at " \
                  + "end of string." + self.cur_pattern
            
        return ((ch, ch3), pat_next)

    #######################################
    ##
    ## pattern parsing
    ##
    ## a            --> (TEXT  "a")
    ## ab           --> (TEXT  "ab")
    ## a*           --> (STAR "a")
    ## a|b          --> (PIPE "a" "b")
    ## aa|ba        --> (TEXT "a" (PIPE "a" "b") "a")
    ## (aaa)|(bbb)  --> (PIPE "aaa" "bbb")
    ## (a|b)*       --> (STAR (PIPE "a" "b"))
    ## [abcd]       --> (PIPE "a" "b" "c" "d")
    ## (a)          --> (TEXT "a")
    ##
    #######################################
    def parse_pattern(self, pat):
        self.all_toks     = None
        self.next_token   = None
        self.parse_result = []

        self.all_toks = self.tokenize_pattern(pat)
        if len(self.all_toks) == 0:
            return tuple(self.parse_result)

        first_tok = True
        self.get_next_token()
        
        done = False
        while (not done and self.all_toks) or first_tok:
            item = self.parse_top()
            self.parse_result.append(item)
            first_tok = False
        return self.parse_result

    def parse_top(self):
        if type(self.next_token) is str:
            result = self.parse_text()
        elif self.next_token == LPAREN:
            result = self.parse_group()
        elif self.next_token == LBRACKET:
            result = self.parse_char_class()
        else:
            raise RuntimeError, "Unexpected char type" + self.next_token
        return result

    def parse_text(self):
        s1 = self.next_token
        self.consume(TEXT)
        if self.next_token == STAR:
            self.consume(STAR)
            return (STAR, s1)
        elif self.next_token == PIPE:
            self.consume(PIPE)
            p2 = self.parse_top()
            return (PIPE, s1, p2)
        elif self.next_token == None:
            return (TEXT, s1)
        return None

    def parse_group(self):
        self.consume(LPAREN)
        result = parse_top()
        self.consume(RPAREN)
        return result

    def parse_char_class(self):
        self.consume(LBRACKET)
        txt = self.next_token
        self.consume(TEXT)
        tmp = [PIPE]
        for c in txt:
            tmp.append(c)
        self.consume(RBRACKET)
        return tuple(tmp)

    ######

    def consume(self, expected):
        if expected == TEXT:
            if type(self.next_token) is str:
                self.get_next_token()
                return
            raise RuntimeError, "Expected normal text, but got" \
                  + self.next_token
        assert expected in all_special_syms
        if self.next_token not in char2sym \
           or char2sym[self.next_token] != expected:
            raise RuntimeError, "did not expect actual char" + self.next_token
        self.get_next_token()
        return

    def get_next_token(self):
        if not self.all_toks:
            self.next_token = None
            return
        self.next_token = self.all_toks.pop(0)
        return

    #######################################
    ##
    ## regexp tokens
    ##
    #######################################
    def tokenize_pattern(self, pat):
        result = []

        special_chars = char2sym.keys()
        while len(pat) > 0:
            ch = pat[0]
            pat = pat[1:]
            if ch in special_chars:
                result.append(char2sym[ch])
            elif ch == '\\':
                ch  = pat[0]
                pat = pat[1:]
                self.tokenize_helper(ch, result)
            else:
                self.tokenize_helper(ch, result)
            pass
        return result

    def tokenize_helper(self, ch, result):
        if len(result)==0 or type(result[-1]) is int:
            result.append(ch)
        else:
            last_str = result[-1]
            last_str = last_str + ch
            result[-1] = last_str
        return

    #######################################
    ##
    #######################################
    def parse(self, lexer_in):
        self.cur_result = []

        cur_node = self.start
        cur_in   = lexer_in
        backup   = None

        while cur_in:
            ch = cur_in[0]
            next_node = cur_node.maybe_get_next_node(ch)

            if next_node:
                cur_in = cur_in[1:]
                if next_node.is_accepting:
                    backup = (next_node, cur_in)
                cur_node = next_node
                continue

            if backup:
                next_node, cur_in = backup
                backup = None
                self.add_to_result(next_node)
                cur_node = self.start
                continue

            raise RuntimeError, "parse error"
        
        if next_node.is_accepting:
            self.add_to_result(next_node)
            
        if len(self.cur_result) == 1:
            return self.cur_result[0]
        return self.cur_result

    def add_to_result(self, node):
        assert node.is_accepting
        if node.action is None:
            return
        self.cur_result.append(node.action)
        return

    pass

