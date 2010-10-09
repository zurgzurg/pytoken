import unittest

class ply_test(unittest.TestCase):
    def assert_toks_equal(self, tok1, tok2):
        self.assert_(tok1.type == tok2.type)
        self.assert_(tok1.value == tok2.value)
        self.assert_(tok1.lineno == tok2.lineno)
        self.assert_(tok1.lexpos == tok2.lexpos)
    pass

class ply_simple_01(ply_test):
    def runTest(self):
        return
    pass

import utest_ply03
class check_ply03(ply_test):
    def runTest(self):
        l1 = utest_ply03.ply_lexer
        l2 = utest_ply03.ptok_lexer
        l1.input('a')
        l2.input('a')
        tok1 = l1.token()
        tok2 = l2.token()
        self.assert_toks_equal(tok1, tok2)
        return
    pass

if __name__ == "__main__":
    unittest.main()

