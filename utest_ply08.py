import ply.lex as ply_lex
import pytoken_ply_lex as ptok_lex

tokens = ('tok1',)

literals = ['x']

t_tok1 = 'a'

def t_error(t):
    print "Illegal character '%s'" % t.value[0]
    t.lexer.skip(1)

ply_lexer = ply_lex.lex()
ptok_lexer = ptok_lex.lex()