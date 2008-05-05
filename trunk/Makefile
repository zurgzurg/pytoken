#python_inc_dir=/custom/python-2.5.1-memdebug/include/python2.5
#python_inc_dir=/custom/python-2.5.1/include/python2.5
#python_inc_dir=/home/ramb/src/pylex/python-2.5.1-stock/include/python2.5
#python_inc_dir=/home/ramb/src/pylex/python-2.5.1-memdebug/include/python2.5

##
## expect PYINC to be set in build environment
##

tar:
	tar zcf pytoken.tar.gz escapemodule.c utest.py pytoken.py setup.py Makefile

clean:
	rm -fr *~ *.[ao] *.so *.pyc build
