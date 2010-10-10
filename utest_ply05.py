import ply.lex as ply_lex
import pytoken_ply_lex as ptok_lex

tokens = ('tok1', 'tok2')

def t_tok2(t):
    'b+'
    return t

def t_tok1(t):
    'b'
    t.value = 7
    return t

def t_error(t):
    print "Illegal character '%s'" % t.value[0]
    t.lexer.skip(1)

ply_lexer = ply_lex.lex()
ptok_lexer = ptok_lex.lex()
