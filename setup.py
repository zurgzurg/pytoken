import os

from distutils.command.clean import clean as _clean
from distutils.core import setup, Extension

module1 = Extension('escape',
                    sources = ['escapemodule.c'])

##
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
      ext_modules = [module1],

      cmdclass = {"clean" : clean} )
