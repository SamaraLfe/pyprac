import unittest
from sqroot import sqroots


class TestSQRroots(unittest.TestCase):
    def test_no_roots(self):
        result = sqroots("1 2 3")
        self.assertEqual(result, "")

    def test_one_root(self):
        result = sqroots("1 2 1")
        self.assertEqual(result, "-1.000000")

    def test_two_roots(self):
        result = sqroots("1 -3 2")
        self.assertEqual(result, "2.000000 1.000000")

    def test_invalid_input(self):
        with self.assertRaises(ValueError):
            sqroots("1 2")
        with self.assertRaises(ValueError):
            sqroots("0 2 3")
        with self.assertRaises(ValueError):
            sqroots("a b c")


if __name__ == '__main__':
    unittest.main()