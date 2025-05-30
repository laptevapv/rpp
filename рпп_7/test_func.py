import unittest
from triangle_func import get_triangle_type, IncorrectTriangleSides

class TestGetTriangleType(unittest.TestCase):

    # Позитивные тесты
    def test_equilateral_triangle(self):
        self.assertEqual(get_triangle_type(3, 3, 3), "equilateral")

    def test_isosceles_triangle(self):
        self.assertEqual(get_triangle_type(5, 5, 3), "isosceles")
        self.assertEqual(get_triangle_type(2.5, 2.5, 3), "isosceles")

    def test_nonequilateral_triangle(self):
        self.assertEqual(get_triangle_type(3, 4, 5), "nonequilateral")

    # Негативные тесты
    def test_zero_side(self):
        with self.assertRaises(IncorrectTriangleSides):
            get_triangle_type(0, 4, 5)

    def test_negative_side(self):
        with self.assertRaises(IncorrectTriangleSides):
            get_triangle_type(-1, 4, 5)

    def test_invalid_triangle_sum(self):
        with self.assertRaises(IncorrectTriangleSides):
            get_triangle_type(1, 2, 3)
        with self.assertRaises(IncorrectTriangleSides):
            get_triangle_type(10, 1, 1)

    def test_invalid_types(self):
        with self.assertRaises(Exception):
            get_triangle_type('a', 2, 3)
        with self.assertRaises(Exception):
            get_triangle_type(None, 2, 3)

if __name__ == '__main__':
    unittest.main()
