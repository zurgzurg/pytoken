########################################################
##
## Copyright (c) 2008-2010, Ram Bhamidipaty
## All rights reserved.
## 
## Redistribution and use in source and binary forms, with or without
## modification, are permitted provided that the following conditions are
## met:
## 
##     * Redistributions of source code must retain the above
##       copyright notice, this list of conditions and the
##       following disclaimer.
## 
##     * Redistributions in binary form must reproduce the above
##       copyright notice, this list of conditions and the following
##       disclaimer in the documentation and/or other materials
##       provided with the distribution.
## 
##     * Neither the name of Ram Bhamidipaty nor the names of its
##       contributors may be used to endorse or promote products
##       derived from this software without specific prior written permission.
## 
## THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
## "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
## LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
## A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
## OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
## SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
## LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
## DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
## THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
## (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
## OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
## 
########################################################
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
        self.lstate = None
        return

    def get_tok_info(self):
        md = get_caller_module_dict(3)
        if 'tokens' not in md:
            raise RuntimeError, "Unable to find ply required list of tokens."
        tok_names = md['tokens']
        toks = [TokenInfo(tname) for tname in md['tokens']]
        
        simple_toks = []
        func_toks = []
        for tinfo in toks:
            basic_name = 't_' + tinfo.name
            if basic_name in md:
                tval = md[basic_name]
            else:
                ign_name = 't_ignore_' + tinfo.name
                if not ign_name in md:
                    raise RuntimeError, 'No token def for ' + tinfo.name
                tval = md[ign_name]
                tinfo.is_ignore = True
            if type(tval) is str:
                tinfo.regex = tval
                simple_toks.append(tinfo)
            else:
                assert callable(tval)
                tinfo.regex = tval.__doc__
                tinfo.func = tval
                tinfo.line_num = tval.func_code.co_firstlineno
                func_toks.append(tinfo)


        def tok_sorter1(a, b):
            return cmp(a.line_num, b.line_num)
        def tok_sorter2(a, b):
            return cmp(len(b.regex), len(a.regex))
        
        func_toks.sort(tok_sorter1)
        simple_toks.sort(tok_sorter2)
        toks2 = []
        toks2.extend(func_toks)
        toks2.extend(simple_toks)

        if 'literals' in md:
            for ch in md['literals']:
                tinfo = TokenInfo(ch)
                tinfo.regex = "\Q" + ch + "\E"
                toks2.append(tinfo)

        return toks2

    def make_lexer(self, toks):
        lobj = pytoken.lexer()
        for idx, tinfo in enumerate(toks):
            if 0:
                print "Adding regex", tinfo.regex
            if tinfo.is_ignore:
                lobj.add_pattern(tinfo.regex)
            else:    
                lobj.add_pattern(tinfo.regex, tok_func, tinfo)
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
        if isinstance(tok, pytoken.EndOfBuffer):
            return None
        return tok

    pass

def tok_func(tup, tok_info):
    if 0:
        print "tok match=", tup, tok_info, tok_info.name
    res = LexToken()
    res.type = tok_info.name
    res.lineno = 1
    res.lexpos = tup[0]
    res.value = tup[1]
    if tok_info.func:
        return tok_info.func(res)
    return res

class TokenInfo:
    def __init__(self, name):
        self.name = name
        self.regex = None
        self.func = None
        self.line_num = None
        self.is_ignore = False
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
## copied from plex
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
