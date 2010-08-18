%{
#include <stdio.h>
int bmarkwrap();
%}

/* %option debug */

%%

"foo12345678901234567890" { return 2; }
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
