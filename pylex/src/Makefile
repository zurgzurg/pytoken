python_inc_dir=/custom/python-2.5.1-memdebug/include/python2.5
#python_inc_dir=/custom/python-2.5.1/include/python2.5

build/lib.linux-i686-2.5/escape.so: build/temp.linux-i686-2.5/escapemodule.o asm_helper.o
	gcc -pthread -shared -g build/temp.linux-i686-2.5/escapemodule.o asm_helper.o -o build/lib.linux-i686-2.5/escape.so

build/temp.linux-i686-2.5/escapemodule.o: escapemodule.c
	gcc -pthread -fno-strict-aliasing -g -Wall -Wstrict-prototypes -fPIC -g -I$(python_inc_dir) -c escapemodule.c -o build/temp.linux-i686-2.5/escapemodule.o

asm_helper.o: asm_helper.s
	as -o $@ $<

tar:
	tar zcf pylex.tar.gz escapemodule.c utest.py pylex.py Makefile

clean:
	rm -fr *~ *.[ao] *.so *.pyc build/lib.linux-i686-2.5/escape.so build/temp.linux-i686-2.5/escapemodule.o
