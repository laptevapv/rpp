import pytest
from triangle_class import Triangle, IncorrectTriangleSides

# Позитивные тесты

def test_equilateral_triangle():
    t = Triangle(3, 3, 3)
    assert t.triangle_type() == "equilateral"
    assert t.perimeter() == 9

def test_isosceles_triangle():
    t = Triangle(5, 5, 3)
    assert t.triangle_type() == "isosceles"
    assert t.perimeter() == 13

def test_nonequilateral_triangle():
    t = Triangle(3, 4, 5)
    assert t.triangle_type() == "nonequilateral"
    assert t.perimeter() == 12

def test_float_sides():
    t = Triangle(2.5, 2.5, 3.0)
    assert t.triangle_type() == "isosceles"
    assert t.perimeter() == 8.0

# Негативные тесты

@pytest.mark.parametrize("a, b, c", [
    (0, 4, 5),      # нулевая сторона
    (-1, 4, 5),     # отрицательная сторона
    (1, 2, 3),      # нарушение неравенства треугольника
    (10, 1, 1),     # одна сторона слишком длинная
])
def test_invalid_triangle_sides(a, b, c):
    with pytest.raises(IncorrectTriangleSides):
        Triangle(a, b, c)

@pytest.mark.parametrize("a, b, c", [
    ('a', 2, 3),
    (None, 2, 3),
    ([1], 2, 3),
])
def test_invalid_input_types(a, b, c):
    with pytest.raises(IncorrectTriangleSides):
        Triangle(a, b, c)
