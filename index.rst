`.. pytoken documentation master file, created by
   sphinx-quickstart on Sat Mar 14 07:47:58 2009.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

:mod:`pytoken` --- A generator of fast scanners
===============================================

.. module:: pytoken
   :synopsis: A generator of fast scanners.
.. moduleauthor:: Ram Bhamidipaty <rambham@gmail.com>
.. sectionauthor:: Ram Bhamidipaty <rambham@gmail.com>

This module provides support for creating fast scanners.

Background - What is a scanner

In traditional compilers the first step to processing a language, like
C or Pascal, is to read the raw text input and turn it into
tokens. The tokens are then processed by the parser, sometimes to
create an abstract syntax tree.

The run time performance of a scanner can be important to the overall
performance of a compiler system since the scanner will need to process
every character in the input stream. A slow scanner will lead to a slow
compiler.

What makes pytoken special

Scanner generators are not new. Tools like lex and flex have been
around for a long time. pytoken is different because it creates
scanners at run time and it emits native x86 machine code. The aim
of pytoken is to generate scanners that are extremely fast.

pytoken defines two main classes:

.. class:: lexer

   Instances of class :class:`lexer` are the primary workers. Normally
   instances will go through four phases: Initial setup, compilation,
   tokenization, and finally cleanup.

.. class:: lexer_state

   Instances of class :class:`lexer_state` are used by lexer instances
   to keep track of the current position in a file, stream, buffer or
   other input source.
