import sys
import pytoken
import ply.lex as lex

tokens = ('LINE',)

t_LINE = r'[a-zA-Z0-9 ]*\n'

def t_error(t):
    t.lexer.skip(1)
    return

#############################

lex1 = pytoken.ply_lex()
lex2 = lex.lex()

txt = "foo\nbar\n"

lex1.input(txt)
lex2.input(txt)

toklist1 = []
while True:
    tok = lex1.token()
    if not tok:
        break
    toklist1.append(tok)

toklist2 = []
while True:
    tok = lex2.token()
    if not tok:
        break
    toklist2.append(tok)

print toklist1
print toklist2

