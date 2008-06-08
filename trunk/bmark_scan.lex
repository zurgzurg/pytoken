%{
#include <stdio.h>
int bmarkwrap();
%}

/* %option debug */

%%

"foo" { return 2; }
"bar" { return 3; }
" "   { ; }
"\n"  { ; }
.     { return 1; }

%%

int
bmarkwrap()
{
  return 1;
}
