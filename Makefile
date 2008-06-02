#python_inc_dir=/custom/python-2.5.1-memdebug/include/python2.5
#python_inc_dir=/custom/python-2.5.1/include/python2.5
#python_inc_dir=/home/ramb/src/pylex/python-2.5.1-stock/include/python2.5
#python_inc_dir=/home/ramb/src/pylex/python-2.5.1-memdebug/include/python2.5

##
## expect PYINC to be set in build environment
##

tar:
	tar zcf pytoken.tar.gz escapemodule.c utest.py pytoken.py setup.py Makefile

hack:
	-mkdir build
	-mkdir build/temp.linux-i686-2.5
	-mkdir build/lib.linux-i686-2.5
	gcc -pthread -fno-strict-aliasing -g -pipe -Wall -Wp,-D_FORTIFY_SOURCE=2 -fexceptions -fstack-protector --param=ssp-buffer-size=4 -m32 -march=i386 -mtune=generic -fasynchronous-unwind-tables -D_GNU_SOURCE -fPIC -fPIC -I/usr/include/python2.5 -c escapemodule.c -o build/temp.linux-i686-2.5/escapemodule.o
	gcc -pthread -shared build/temp.linux-i686-2.5/escapemodule.o -L/usr/lib -lpython2.5 -o build/lib.linux-i686-2.5/escape.so



clean:
	rm -fr *~ *.[ao] *.so *.pyc build
