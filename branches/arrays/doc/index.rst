:mod:`pytoken` - A generator of fast scanners
===============================================

.. module:: pytoken
   :platform: linux 32bit x86
   :synopsis: A generator of fast scanners.
.. moduleauthor:: Ram Bhamidipaty <rambham@gmail.com>

This module provides support for creating fast scanners.

Background - What is a scanner
------------------------------

In traditional compilers the first step to processing a language, like
C or Pascal, is to read the raw text input and turn it into
tokens. The tokens are then processed by the parser, sometimes to
create an abstract syntax tree.

The run time performance of a scanner can be important to the overall
performance of a compiler system since the scanner will need to process
every character in the input stream. A slow scanner will lead to a slow
compiler.

What makes pytoken special
--------------------------

Scanner generators are not new. Tools like lex and flex have been
around for a long time. Those tools were used at compile time. They
read a special input file and wrote out C code that could be compiled
into the final application.  pytoken is different because it creates
scanners at run time and it emits native x86 machine code. No explicit
compile or link step is needed. The aim of pytoken is to generate
scanners that are extremely fast.

A Simple Example::

  import pytoken

  lexer_obj = pytoken.lexer()
  lexer_obj.add_pattern("a", 1)
  lexer_obj.add_pattern("b", 2)
  lexer_obj.compile_to_machine_code()

  buf = pytoken.lexer_state()
  buf.set_input("ab")

  tok = lexer_obj.get_token(buf)
  assert tok == 1
  tok = lexer_obj.get_token(buf)
  assert tok == 2

Main Interface
--------------

The two main classes are :class:`pytoken.lexer` and
:class:`pytoken.lexer_state`. Instances of :class:`pytoken.lexer` are
used for the lexer itself and instances of :class:`pytoken.lexer_state`
are use to hold the information needed while scanning an input, things
like the current position in a buffer, the text of the buffer, etc.

The current :class:`pytoken.lexer` implementation supports only one
basic useage model:

    1. Create an instance of :class:`pytoken.lexer`.
    2. Call :meth:`lexer.add_pattern()` for all tokens.
    3. Call :meth:`lexer.compile_to_machine_code()`.
    4. Repeatedly call :meth:`lexer.get_token()`.


After :meth:`lexer.compile_to_machine_code()` has been called on
an instance of :class:`pytoken.lexer` no further calls to
:meth:`lexer.add_pattern()` are allowed.

Calling :meth:`lexer.get_token()` requires an instance of
:class:`pytoken.lexer_state`. The particular instance of
:class:`pytoken.lexer_state` that is passed to :meth:`lexer.get_token()`
can change on each call. This techique can be used to handle
switching the input stream on a per-token basis.

The scanners are designed to store all state

Protocol for :meth:`lexer.get_token()`
----------------------------------------

:meth:`lexer.get_token()` will return the string "EOB" when the
end of the current :class:`pytoken.lexer_state` buffer is reached.
If input text is encountered that does not match any pattern an
a RuntimeError will be raised. A RuntimeError will also be raised
if the scanner find itself in some kind of illegal state - mostly
likely due to a bug in pytoken itself.

Otherwise the normal return protocol will be followed.



:class:`pytoken.lexer`
----------------------

.. class:: lexer

   Instances of class :class:`lexer` are the primary workers. Normally
   instances will go through four phases: Initial setup, compilation,
   tokenization, and finally cleanup.

   .. method:: lexer.add_pattern(regex, *args)

      Specifies a regex and some kind of action. The regex should be
      a string following the syntax described in the Regular Expression
      Syntax section. There are several possible forms for calling
      add_pattern:

      1. add_pattern(regex)
      2. add_pattern(regex, obj1)
      3. add_pattern(regex, obj1, obj2)
      
      Form 1 is equivalent to form2 where obj1 is None.

      In form 2 if obj1 is callable then it must accept a single argument.
      When this regex matches the callable will be called with the text
      of the match. The return value from calling obj1 will be returned
      by get_token(). If obj1 is not callable then when the regex matches
      get_token will return obj1.

      In form 3 obj1 must be a callable that accepts two arguments. The first
      will be the buffer object passed to get_token() and the second will be
      obj2. The return value from calling obj1 will be returned by get_token().

   .. method:: lexer.compile_to_machine_code()

      This method can be called only once. The patterns will be merged into
      a single DFA and then compiled into machine code. There is no return
      value. Currently the function always works. More work is needed to
      do things like limiting the number of NFA states that can be created
      and bounding the total run time that can be spent.

   .. method:: lexer.get_token(lstate=None)

      This method should only be called after
      :meth:`lexer.compile_to_machine_code()`. The return value will be
      the action associated with the next token from the lexer_state object
      that is passed. If no lexer_state argument is given then the default
      one will be used -- if a default one has been assigned. The
      consequences of callign get_token() with no lexer_state argument
      and without specifying a default lexer_state object are unspecified.

   .. method:: lexer.set_default_lexer_state(lstate)

      This is a convenience routine to set a default lexer state object.
      For the case when all tokens will come from the same lexer state
      object this function can be used to avoid needing to pass the
      same object to all get_token() calls.


:class:`pytoken.lexer_state`
----------------------------
.. class:: lexer_state

   Instances of class :class:`lexer_state` are used by lexer instances
   to keep track of the current position in a file, stream, buffer or
   other input source.

   Instances have a buffer that holds the data that is waiting to be
   scanned, a pointer to the start of the current token and a next
   char pointer and some bookkeeping info.

   .. method:: lexer_state.has_data()

      Returns True if there is data in the buffer that has not yet been
      scanned. More precisely the return value is true if there is
      a buffer with data and the next char pointer is not null.

   .. method:: lexer_state.set_cur_offset(offset)

      Sets the next char pointer to point to offset chars into the buffer. It
      is an error if the offset position is outside the range of the buffer.
      There is no restriction on resetting the offset back to zero, if
      the scanner has advanced it, but there is also no supported protocol
      of when the scanner will cause the buffer to be shifted and filled
      again.


   .. method:: lexer_state.get_cur_offset()

      Raises an exception if there is no data in the buffer or the
      next char pointer is out of range. Otherwise an int is returned
      which is the offset of the next char pointer from the start of the
      buffer.

   .. method:: lexer_state.set_cur_addr(addr)

      Not intended for general use. This allows setting the next char pointer
      directly. It is the users resposibility to ensure that a valid address
      is passed.

   .. method:: lexer_state.get_cur_addr()

      Returns the next char pointer address as an integer. An exception is
      raised if there is no valid next char pointer.

   .. method:: lexer_state.get_match_text()

      Returns the text from the start of the current token to one before the
      next char pointer as a string. Raises an exception if the intstance
      does not have valid token start and next char pointers.

   .. method:: lexer_state.set_input(obj)

      Obj can either be a string or a file object. If obj is a string then the
      buffer will get a copy of the string. If the obj is a file then a
      buffer (of unspecified size) will be allocated and filled with bytes
      from the file. No other object type is supported (yet).

   .. method:: lexer_state.set_fill_method(obj)

      Obj must be a callable. If a fill method is given then it will be
      called when the buffer needs to be filled.

   .. method:: lexer_state.add_to_buffer(txt)

      Not yet documented.
      

   .. method:: lexer_state.get_all_state()

      Not yet documented.

Regular Expression Syntax
-------------------------

:mod:`pytoken` supports a limited set of regular expression meta characters.
The supported meta characters are:

  ``'|'``
    Alternation. ``'abc|def'`` matches the string ``'abc'`` or ``'def'``.
    The precedence of concatenation is higher than alternation.

  ``'[]'``
    Character class. The character class extends to the first ``']'``. A
    character class is just a simple way to specify an alternation. For example
    ``'[abc]'`` is the same as ``'(a|b|c)'``. If the first character of the
    character class is ``'^'`` then the sense of the class is inverted,
    that is it matches anything not in the class.

    As a convenience ranges of characters can be specified with the ``'-'``
    character. For example all the lower case letters can be specified
    with ``'[a-z]'``. To include a literal ``'-'`` in character class
    put it at the beginning or the end: ``'[0-9-]'`` or ``'[-0-9]'``.

  ``'()'``
    Grouping. Useful to control the binding of other meta characters. If you
    want ``'abc'`` or ``'def'`` you can use ``'(abc)|(def)'``.

  ``'*'``
    Traditional kleene star. Zero or more repetions of the previous regex.

  ``'+'``
    One or more repetitions of the previous regex.

  ``'?'``
    Zero or one repetion of the previous regex.

  ``'.'``
    Any character. Including newline.

  ``'\'``
    Backslash. Escapes the next character for all characters other than
    ``'n'``, ``'r'``, and ``'t'``. For those characters a newline, carriage
    return or tab is matched.

Operator Precedence and Compatability with Other Regular Expression Systems
---------------------------------------------------------------------------
pytoken strives to be compatible with Perl where possible. Some Perl
constructs have no meaning for DFA-type regex matchers - particularly
concepts like greedy and non-greedy. Kleene star has higher precedence
than concatenation, which has higher precedence than alternation.


Using :mod:`pytoken` with Ply
--------------------------------
Nothing here yet.

Benchmarks
----------
Nothing here yet.


:mod:`pytoken` Internals
------------------------
More stuff needed here.
