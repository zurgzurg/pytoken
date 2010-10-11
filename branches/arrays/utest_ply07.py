import ply.lex as ply_lex
import pytoken_ply_lex as ptok_lex

tokens = ('tok1', 'tok2', 'tok3')

t_ignore_tok2 = 'a'
t_tok1 = 'b'

def t_tok3(t):
    'c'
    return

def t_error(t):
    print "Illegal character '%s'" % t.value[0]
    t.lexer.skip(1)

ply_lexer = ply_lex.lex()
ptok_lexer = ptok_lex.lex()
