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
        self.lstate = None
        self.err_action = None

        self.toks = self.get_tok_info()
        self.lobj = self.make_lexer(self.toks)
        return

    def get_tok_info(self):
        md = get_caller_module_dict(3)
        if 'tokens' not in md:
            raise RuntimeError, "Unable to find ply required list of tokens."
        if 't_error' not in md:
            raise RuntimeError, "Unable to find error token t_error"
        self.err_action = md['t_error']
        tok_names = md['tokens']
        toks = [UserTokenDef(tname, self) for tname in md['tokens']]
        
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
                tinfo = UserTokenDef(ch, self)
                tinfo.regex = "\Q" + ch + "\E"
                toks2.append(tinfo)

        return toks2

    def make_lexer(self, toks):
        lobj = pytoken.lexer()
        for idx, u_tok_def in enumerate(toks):
            if 0:
                print "Adding regex", u_tok_def.regex
            if u_tok_def.is_ignore:
                lobj.add_pattern(u_tok_def.regex)
            else:    
                lobj.add_pattern(u_tok_def.regex, tok_func, u_tok_def)
        lobj.compile_to_arrays()
        return lobj

    #####################
    ### ply.lex api below
    #####################
    def input(self, obj):
        self.lstate = pytoken.lexer_state();
        self.lstate.set_input(obj)
        return
        
    def skip(self, num_to_skip):
        pos = self.lstate.get_cur_offset()
        pos += num_to_skip
        self.lstate.set_cur_offset(pos)
        return

    def token(self):
        while True:
            try:
                tok = self.lobj.get_token( self.lstate )
                if isinstance(tok, pytoken.EndOfBuffer):
                    return None
                return tok
            except pytoken.UnmatchedInputError:
                tok = LexToken()
                tok.lexer = self
                self.err_action(tok)

    pass

def tok_func(tup, user_tok_def):
    if 0:
        print "tok match=", tup, user_tok_def, user_tok_def.name
    res = LexToken()
    res.type = user_tok_def.name
    res.lineno = 1
    res.lexpos = tup[0]
    res.value = tup[1]
    if user_tok_def.func:
        return user_tok_def.func(res)
    return res

class UserTokenDef:
    def __init__(self, name, lexer):
        self.name = name
        self.regex = None
        self.func = None
        self.line_num = None
        self.is_ignore = False
        self.lexer = lexer
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
        self.lexer = None
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
