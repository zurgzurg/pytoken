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

