import unittest

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

if __name__ == "__main__":
    unittest.main()

