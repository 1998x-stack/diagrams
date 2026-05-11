"""
High-Level Mathematics Calculator — Version 2 (updated)
New components: MatrixCalculator, ComplexNumber, taylor_series.
Modified: integrate (multi-method), derivative (central difference).
"""
import math


class Trigonometry:
    """Basic trigonometric functions."""

    def sin(self, x: float) -> float:
        return math.sin(x)

    def cos(self, x: float) -> float:
        return math.cos(x)

    def tan(self, x: float) -> float:
        if math.cos(x) == 0:
            raise ValueError(f"tan is undefined at x={x}")
        return math.tan(x)


def derivative(f, x: float, h: float = 1e-5, order: int = 1) -> float:
    """
    Numerical derivative.
    order=1: central difference  f'(x) ≈ (f(x+h) - f(x-h)) / (2h)
    order=2: second derivative   f''(x) ≈ (f(x+h) - 2f(x) + f(x-h)) / h²
    """
    if order == 1:
        return (f(x + h) - f(x - h)) / (2 * h)
    elif order == 2:
        return (f(x + h) - 2 * f(x) + f(x - h)) / (h ** 2)
    else:
        raise ValueError(f"Unsupported derivative order: {order}. Use 1 or 2.")


def integrate(f, a: float, b: float, n: int = 1000, method: str = "midpoint") -> float:
    """
    Numerical integration.
    method: "midpoint" | "simpson" | "trapezoidal"
    """
    if n <= 0:
        raise ValueError("n must be a positive integer")
    dx = (b - a) / n
    if method == "midpoint":
        total = 0.0
        for i in range(n):
            mid = a + (i + 0.5) * dx
            total += f(mid)
        return total * dx
    elif method == "simpson":
        if n % 2 != 0:
            raise ValueError("Simpson's rule requires an even number of intervals")
        total = f(a) + f(b)
        for i in range(1, n):
            coeff = 4 if i % 2 != 0 else 2
            total += coeff * f(a + i * dx)
        return total * dx / 3
    elif method == "trapezoidal":
        total = (f(a) + f(b)) / 2
        for i in range(1, n):
            total += f(a + i * dx)
        return total * dx
    else:
        raise ValueError(f"Unknown integration method: {method!r}")


def taylor_series(f, x0: float, n: int, x: float) -> float:
    """
    Approximate f(x) using Taylor series centered at x0 up to order n.
    Uses numerical derivatives for each term.
    """
    result = 0.0
    factorial = 1
    for k in range(n + 1):
        if k == 0:
            term = f(x0)
        else:
            factorial *= k
            dk = derivative(f, x0, h=1e-4, order=min(k, 2))
            term = dk * ((x - x0) ** k) / factorial
        result += term
    return result


class MatrixCalculator:
    """Linear algebra operations for square matrices (represented as list of lists)."""

    def _validate(self, matrix: list[list[float]]) -> int:
        n = len(matrix)
        for row in matrix:
            if len(row) != n:
                raise ValueError("Matrix must be square")
        return n

    def determinant(self, matrix: list[list[float]]) -> float:
        """Compute determinant via cofactor expansion (recursive)."""
        n = self._validate(matrix)
        if n == 1:
            return matrix[0][0]
        if n == 2:
            return matrix[0][0] * matrix[1][1] - matrix[0][1] * matrix[1][0]
        det = 0.0
        for col in range(n):
            minor = [
                [matrix[row][c] for c in range(n) if c != col]
                for row in range(1, n)
            ]
            sign = (-1) ** col
            det += sign * matrix[0][col] * self.determinant(minor)
        return det

    def inverse(self, matrix: list[list[float]]) -> list[list[float]]:
        """Compute inverse using Gauss-Jordan elimination."""
        n = self._validate(matrix)
        det = self.determinant(matrix)
        if abs(det) < 1e-10:
            raise ValueError("Matrix is singular and cannot be inverted")
        # Augment matrix with identity
        augmented = [row[:] + [1.0 if i == j else 0.0 for j in range(n)]
                     for i, row in enumerate(matrix)]
        for col in range(n):
            # Find pivot
            pivot_row = max(range(col, n), key=lambda r: abs(augmented[r][col]))
            augmented[col], augmented[pivot_row] = augmented[pivot_row], augmented[col]
            pivot = augmented[col][col]
            if abs(pivot) < 1e-10:
                raise ValueError("Matrix is singular (encountered zero pivot)")
            augmented[col] = [x / pivot for x in augmented[col]]
            for row in range(n):
                if row != col:
                    factor = augmented[row][col]
                    augmented[row] = [
                        augmented[row][k] - factor * augmented[col][k]
                        for k in range(2 * n)
                    ]
        return [row[n:] for row in augmented]

    def multiply(self, a: list[list[float]], b: list[list[float]]) -> list[list[float]]:
        """Matrix multiplication A × B."""
        n = self._validate(a)
        m = self._validate(b)
        if n != m:
            raise ValueError("Matrix dimensions must match for multiplication")
        result = [[0.0] * n for _ in range(n)]
        for i in range(n):
            for j in range(n):
                for k in range(n):
                    result[i][j] += a[i][k] * b[k][j]
        return result


class ComplexNumber:
    """Complex number arithmetic."""

    def __init__(self, real: float, imag: float = 0.0):
        self.real = real
        self.imag = imag

    def __add__(self, other: "ComplexNumber") -> "ComplexNumber":
        return ComplexNumber(self.real + other.real, self.imag + other.imag)

    def __sub__(self, other: "ComplexNumber") -> "ComplexNumber":
        return ComplexNumber(self.real - other.real, self.imag - other.imag)

    def __mul__(self, other: "ComplexNumber") -> "ComplexNumber":
        return ComplexNumber(
            self.real * other.real - self.imag * other.imag,
            self.real * other.imag + self.imag * other.real,
        )

    def __truediv__(self, other: "ComplexNumber") -> "ComplexNumber":
        denom = other.real ** 2 + other.imag ** 2
        if abs(denom) < 1e-15:
            raise ZeroDivisionError("Cannot divide by zero complex number")
        return ComplexNumber(
            (self.real * other.real + self.imag * other.imag) / denom,
            (self.imag * other.real - self.real * other.imag) / denom,
        )

    def modulus(self) -> float:
        return math.sqrt(self.real ** 2 + self.imag ** 2)

    def argument(self) -> float:
        """Return argument (angle) in radians, in range (-π, π]."""
        return math.atan2(self.imag, self.real)

    def __repr__(self) -> str:
        sign = "+" if self.imag >= 0 else "-"
        return f"({self.real} {sign} {abs(self.imag)}i)"
