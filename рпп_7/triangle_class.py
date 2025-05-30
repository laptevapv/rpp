class IncorrectTriangleSides(Exception):
    """Исключение для некорректных сторон треугольника."""
    pass

class Triangle:
    def __init__(self, a, b, c):
        if not all(isinstance(x, (int, float)) for x in (a, b, c)):
            raise IncorrectTriangleSides("Стороны должны быть числами.")

        if a <= 0 or b <= 0 or c <= 0:
            raise IncorrectTriangleSides("Стороны должны быть положительными.")

        if a + b <= c or a + c <= b or b + c <= a:
            raise IncorrectTriangleSides("Нарушено неравенство треугольника.")

        self.a = a
        self.b = b
        self.c = c

    def triangle_type(self):
        if self.a == self.b == self.c:
            return "equilateral"
        elif self.a == self.b or self.b == self.c or self.a == self.c:
            return "isosceles"
        else:
            return "nonequilateral"

    def perimeter(self):
        return self.a + self.b + self.c
