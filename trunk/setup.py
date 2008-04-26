from distutils.core import setup, Extension

module1 = Extension('escape',
                    sources = ['escapemodule.c'])

setup(name = 'escape',
      version = '1.0',
      description = 'The escape package. Gives python low level access.',
      ext_modules = [module1])

