import unittest
import pytoken

class ply_test(unittest.TestCase):
    def assert_toks_equal(self, tok1, tok2):
        self.assertEqual(tok1.type, tok2.type)
        self.assertEqual(tok1.value, tok2.value)
        self.assertEqual(tok1.lineno, tok2.lineno)
        self.assertEqual(tok1.lexpos, tok2.lexpos)
    pass

class ply_simple_01(ply_test):
    def runTest(self):
        return
    pass

class check_ply03(ply_test):
    def runTest(self):
        import utest_ply03

        l1 = utest_ply03.ply_lexer
        l2 = utest_ply03.ptok_lexer
        l1.input('a')
        l2.input('a')
        tok1 = l1.token()
        tok2 = l2.token()
        self.assert_toks_equal(tok1, tok2)
        return
    pass

class check_ply04(ply_test):
    def runTest(self):
        import utest_ply04

        l1 = utest_ply04.ply_lexer
        l2 = utest_ply04.ptok_lexer
        l1.input('ab')
        l2.input('ab')

        tok1 = l1.token()
        tok2 = l2.token()
        self.assert_toks_equal(tok1, tok2)

        tok1 = l1.token()
        tok2 = l2.token()
        self.assert_toks_equal(tok1, tok2)
        return
    pass

class check_ply05(ply_test):
    def runTest(self):
        import utest_ply05

        l1 = utest_ply05.ply_lexer
        l2 = utest_ply05.ptok_lexer

        if 1:
            l1.input('b')
            l2.input('b')

            tok1 = l1.token()
            tok2 = l2.token()
            self.assert_toks_equal(tok1, tok2)

        l1.input('bb')
        l2.input('bb')

        tok1 = l1.token()
        tok2 = l2.token()
        self.assert_toks_equal(tok1, tok2)
        return
    pass

class check_ply06(ply_test):
    def runTest(self):
        import utest_ply06

        l1 = utest_ply06.ply_lexer
        l2 = utest_ply06.ptok_lexer

        if 1:
            l1.input('b')
            l2.input('b')

            tok1 = l1.token()
            tok2 = l2.token()
            self.assert_toks_equal(tok1, tok2)

        l1.input('bb')
        l2.input('bb')

        tok1 = l1.token()
        tok2 = l2.token()
        self.assert_toks_equal(tok1, tok2)
        return
    pass

class check_ply07(ply_test):
    def runTest(self):
        import utest_ply07

        l1 = utest_ply07.ply_lexer
        l2 = utest_ply07.ptok_lexer

        l1.input('abc')
        l2.input('abc')

        ply_list = []
        while True:
            tok = l1.token()
            #print "ply got a tok", len(ply_list), tok
            if not tok or len(ply_list) > 5:
                break
            ply_list.append(tok)
        #print "ply_list=", ply_list

        ptok_list = []
        while True:
            tok = l2.token()
            #print "pytoken got a tok", len(ptok_list), tok
            if not tok or len(ply_list) > 5:
                break
            ptok_list.append(tok)
        #print "ptok_list=", ptok_list
        
        self.assertEqual(len(ply_list), len(ptok_list))

        return
    pass

class check_ply08(ply_test):
    def runTest(self):
        import utest_ply08

        l1 = utest_ply08.ply_lexer
        l2 = utest_ply08.ptok_lexer

        l1.input('ax')
        l2.input('ax')

        tok1 = l1.token()
        tok2 = l2.token()
        self.assert_toks_equal(tok1, tok2)

        tok1 = l1.token()
        tok2 = l2.token()
        self.assert_toks_equal(tok1, tok2)

        return
    pass

class check_ply09(ply_test):
    def runTest(self):
        import utest_ply09

        l1 = utest_ply09.ply_lexer
        l2 = utest_ply09.ptok_lexer

        l1.input('xa')
        l2.input('xa')

        tok1 = l1.token()
        self.assert_(utest_ply09.err_count == 1)
        tok2 = l2.token()
        self.assert_(utest_ply09.err_count == 2)
        self.assert_toks_equal(tok1, tok2)

        return
    pass

if __name__ == "__main__":
    unittest.main()

