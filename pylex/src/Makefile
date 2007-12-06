build/lib.linux-i686-2.5/escape.so: build/temp.linux-i686-2.5/escapemodule.o
	gcc -pthread -shared -g build/temp.linux-i686-2.5/escapemodule.o -o build/lib.linux-i686-2.5/escape.so

build/temp.linux-i686-2.5/escapemodule.o: escapemodule.c
	gcc -pthread -fno-strict-aliasing -g -Wall -Wstrict-prototypes -fPIC -g -I/custom/python-2.5.1/include/python2.5 -c escapemodule.c -o build/temp.linux-i686-2.5/escapemodule.o

junk23.o: junk23.s
	as -a -o $@ $<

doit: caller.o junk23.o
	gcc -o $@ $^
