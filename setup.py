import sys
import os
import pdb
import shutil

from distutils.command.clean import clean as _clean
from distutils.core import setup, Extension
from distutils import sysconfig

##################################################################
def customize_compiler2(compiler):
    (cc, cxx, opt, cflags, ccshared, ldshared, so_ext) = \
         sysconfig.get_config_vars('CC', 'CXX', 'OPT', 'CFLAGS',
                                   'CCSHARED', 'LDSHARED', 'SO')

    if 0:
        print "cc=", cc
        print "cxx=", cxx
        print "opt=", opt
        print "cflags=", cflags
        print "ccshared=", ccshared

        
    cflags = cflags.replace("-DNDEBUG", "")
    cflags = cflags.replace("-O2", "")

    cpp = cc + " -E"
    cc_cmd = cc + ' ' + cflags

    compiler.set_executables(
        preprocessor=cpp,
        compiler=cc_cmd,
        compiler_so=cc_cmd + ' ' + ccshared,
        compiler_cxx=cxx,
        linker_so=ldshared,
        linker_exe=cc)

    compiler.shared_lib_extension = so_ext
    return

idx = None
for i, arg in enumerate(sys.argv):
    if arg == "-debug":
        idx = i
if idx:
    sys.argv.pop(idx)
    
    d = sysconfig.__dict__
    d['customize_compiler'] = customize_compiler2


##################################################################
##
## the main module - escape
##
##################################################################
escape_module = Extension('pytoken.escape',
                          sources = ['pytoken/escapemodule.c'])

mlist = [escape_module]

##################################################################
##
## benchark support - most folks won't need this
##
##################################################################
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
## custom clean func
##
##################################################################
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
        for f in ["parser.out", "parsetab.py"]: 
            try:
                os.unlink(f)
            except OSError:
                pass
        shutil.rmtree("build")
        return
    pass

##################################################################
##
## toplevel
##
##################################################################
## how can I force setup to turn off -O ??
##
setup(name = 'pytoken',
      version = '1.01',
      description = 'Generates scanners for python.',
      author = 'Ram Bhamidipaty',
      author_email = 'rambham@gmail.com',
      url = 'http://code.google.com/p/pytoken/',
      ext_modules = mlist,
      packages = ["pytoken"],
      #py_modules = ['pytoken', 'pytoken_ply_lex'],
      cmdclass = {"clean" : clean} )
