##
## count lines in a file using ply
##
if 0:
    import ply.lex as lex
else:
    import pytoken.pytoken_ply_lex as lex
import ply.yacc as yacc

###########################
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


#############################

lexer = lex.lex()
parser = yacc.yacc()

llist = parser.parse("foo\nbar\n")
print llist
