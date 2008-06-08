import sys
import os

from distutils.command.clean import clean as _clean
from distutils.core import setup, Extension

module1 = Extension('escape',
                    sources = ['escapemodule.c'])

mlist = [module1]

##################################################################
##
## benchark support - most folks wont need this
##
##################################################################
module2 = None
idx = None
for i, arg in enumerate(sys.argv):
    if arg == "-bmark":
        idx = i
if idx:
    sys.argv.pop(idx)
    slist = ["bmarkmodule.c", "bmark_scan.c"]
    obj = Extension("bmark", sources=slist)
    mlist.append(obj)

    # does distutils have a way to run flex?
    cmd = "flex -f -s -B -L -obmark_scan.c -Pbmark bmark_scan.lex"
    print "Running flex command"
    print cmd
    c = os.system(cmd)
    if c != 0:
        print "Flex return non-zero status. Stopping."
        sys.exit(-1)


##################################################################
##
##
##
##################################################################
## how can I force setup to turn off -O ??
##
class clean(_clean):
    """Custom clean routine to clean pyc files"""
    def run(self):
        _clean.run(self)
        for f in os.listdir("."):
            if f.endswith(".pyc") \
               or f.endswith("~") \
               or f.endswith(".s") \
               or f.endswith(".o") \
               or f in ("a.out", "pytoken.tar.gz"):
                os.unlink(f)
        return
    pass

setup(name = 'escape',
      version = '1.0',
      description = 'The escape package. Gives python low level access.',
      ext_modules = mlist,

      cmdclass = {"clean" : clean} )
