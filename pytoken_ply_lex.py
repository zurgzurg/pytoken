import sys
import ply.lex

##
## layer to make pytoken usable for the
## ply lexer/parser generator
##


class lex(object):
    def __init__(self):
        d = ply.lex.get_caller_module_dict(2)
        for tok_name in d['tokens']:
            tok_sym_name = "t_" + tok_name
            tok_obj = d[tok_sym_name]
            if type(tok_obj) is str:
                print "simple", tok_name, tok_sym_name, tok_obj
            else:
                doc_str = tok_obj.func_doc
                print "complex:", tok_name, doc_str

        return
    pass
