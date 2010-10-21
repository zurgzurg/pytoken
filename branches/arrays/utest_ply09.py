import ply.lex as ply_lex
import pytoken_ply_lex as ptok_lex

tokens = ('tok1',)

t_tok1 = 'a'

err_count = 0
def t_error(t):
    global err_count
    err_count += 1
    t.lexer.skip(1)

ply_lexer = ply_lex.lex()
ptok_lexer = ptok_lex.lex()
