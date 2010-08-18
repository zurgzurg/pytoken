import sys
import pytoken

try:
    import ply.lex
    found_ply_lex = True
except ImportError:
    found_ply_lex = False
    lex = None

##
## layer to make pytoken usable for the
## ply lexer/parser generator
##

if found_ply_lex:
    class lex(object):
        def __init__(self):
            self.pytok_lexer = pytoken.lexer()
            self.pytok_state = pytoken.lexer_state()

            func_pats = []
            simple_pats = []

            d = ply.lex.get_caller_module_dict(2)
            for tok_name in d['tokens']:
                tok_sym_name = "t_" + tok_name
                tok_obj = d[tok_sym_name]
                if type(tok_obj) is str:
                    simple_pats.append((tok_sym_name, tok_obj))
                else:
                    regex = tok_obj.func_doc
                    func_pats.append((tok_sym_name, tok_obj.co_firstlineno, regex))


            def simple_sorter(tup1, tup2):
                if len(tup1[1]) < len(tup2[1]):
                    return -1
                elif len(tup1[1]) > len(tup2[1]):
                    return 1
                return 0


            simple_pats.sort(simple_sorter)

            for sym, pat in simple_pats:
                print pat, "-->", sym
                self.pytok_lexer.add_pattern(pat, sym)

            self.pytok_lexer.compile_to_machine_code()

            return

        def input(self, txt):
            self.pytok_state.set_input(txt)
            return

        def token(self):
            tok = self.pytok_lexer.get_token(self.pytok_state)
            return tok

        pass
