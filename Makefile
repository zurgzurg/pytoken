tar:
	tar zcf pytoken.tar.gz escapemodule.c utest.py pytoken.py setup.py Makefile

clean:
	rm -fr *~ *.[ao] *.so *.pyc build
