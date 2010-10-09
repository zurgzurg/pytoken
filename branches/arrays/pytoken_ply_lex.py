import sys
import pytoken

##
## layer to make pytoken usable for the
## ply lexer/parser generator
##

#####################################################
class lex(object):
    def __init__(self):
        self.toks = self.get_tok_info()
        self.lobj = self.make_lexer(self.toks)

        return

    def get_tok_info(self):
        md = get_caller_module_dict(3)
        if 'tokens' not in md:
            raise RuntimeError, "Unable to find ply required list of tokens."
        tok_names = md['tokens']
        toks = [TokenInfo(tname) for tname in md['tokens']]
        
        for tinfo in toks:
            tval = md['t_' + tinfo.name]
            if type(tval) is str:
                tinfo.regex = tval

        return toks

    def make_lexer(self, toks):
        lobj = pytoken.lexer()
        for idx, tinfo in enumerate(toks):
            lobj.add_pattern(tinfo.regex, tok_func, tinfo.name)
        lobj.compile_to_arrays()
        return lobj

    #####################
    ### ply.lex api below
    #####################
    def input(self, obj):
        self.lstate = pytoken.lexer_state();
        self.lstate.set_input(obj)
        return
        
    def token(self):
        tok = self.lobj.get_token( self.lstate )
        return tok

    pass

def tok_func(txt, tname):
    res = LexToken()
    res.type = tname
    res.value = txt
    res.lineno = 1
    res.lexpos = 0
    return res

class TokenInfo:
    def __init__(self, name):
        self.name = name
        self.regex = None
        return
    pass

#####################################################
class LexToken(object):
    """Clone of the ply token object."""
    def __init__(self):
        self.type = None
        self.value = None
        self.lineno = None
        self.lexpos = None
        return
    def __str__(self):
        return "LexToken(%s,%r,%d,%d)" % \
            (self.type,self.value,self.lineno,self.lexpos)
    def __repr__(self):
        return str(self)
    pass

#####################################################
#####################################################
def get_caller_module_dict(levels):
    try:
        raise RuntimeError
    except RuntimeError:
        e,b,t = sys.exc_info()
        f = t.tb_frame
        while levels > 0:
            f = f.f_back                   
            levels -= 1
        ldict = f.f_globals.copy()
        if f.f_globals != f.f_locals:
            ldict.update(f.f_locals)

        return ldict
