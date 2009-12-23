import sys
import pytoken
import ply.yacc as yacc

tokens = ('LINE',)

t_LINE = r'[a-zA-Z0-9 ]*\n'

#############################
def p_file_line_list(p):
    'file : line_list'
    p[0] = p[1]
    

def p_line_list_empty(p):
    'line_list : '
    p[0] = []

def p_line_list_line(p):
    'line_list : line_list LINE'
    p[0] = p[1]
    p[0].append(p[2])

def p_error(p):
    return None

#############################

lexer = pytoken.ply_lex()
parser = yacc.yacc()

llist = parser.parse("foo\nbar\n", lexer)
if len(llist) == 2:
    sys.exit(0)
else:
    sys.exit(1)
