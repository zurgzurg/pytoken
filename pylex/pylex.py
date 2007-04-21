class node(object):
    next_avail_num = 0
    def __init__(self):
        self.name         = "Node_%d" % node.next_avail_num
        node.next_avail_num += 1
        self.nfa_tbl      = []
        self.next_tbl     = {}
        self.action       = None
        self.is_accepting = False
        self.priority     = None
        return

    def must_get_next_node(self, ch):
        if not self.next_tbl.has_key(ch):
            self.next_tbl[ch] = node()
        result = self.next_tbl[ch]
        return result

    def maybe_get_next_node(self, ch):
        if not self.next_tbl.has_key(ch):
            return None
        result = self.next_tbl[ch]
        return result

    def show_tbl(self):
        print "Node table"
        for ch, nxt in self.next_tbl.items():
            print "    ", ch, "--->", nxt
        print "Done."
        return

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

    def token(self, pat, action):
        self.pats.append((pat, action))
        return

    #######################################
    ##
    #######################################
    def compile(self):
        for pat, action in self.pats:
            self.compile_one_pat(self.start, pat, action)
        return

    def get_next_chars(self, pat):
        ch = pat[0]
        if ch != "[":
            pat_next = pat[1:]
            if len(pat_next) == 0:
                pat_next = None
            return (ch, pat_next)
        idx = pat.find("]")
        if idx == -1:
            raise RuntimeError, "Unable to find closing ']' char " \
                  + "in pattern: " + self.cur_pattern
        cclass = pat[1:idx]
        pat_next = pat[idx+1:]
        if len(pat_next) == 0:
            pat_next = None
        return (cclass, pat_next)

    def compile_one_pat(self, node, pat, action):
        cur_pat  = pat
        cur_node = node

        while cur_pat:
            ch, cur_pat = self.get_next_chars(cur_pat)
            cur_node = cur_node.must_get_next_node(ch)
            pass

        cur_node.action = action
        cur_node.is_accepting = True
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

