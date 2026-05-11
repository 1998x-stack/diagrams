"""
High-Level Mathematics Calculator — Version 1 (baseline)
Components: Trigonometry, numerical derivative, rectangular-rule integration.
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


def derivative(f, x: float, h: float = 1e-5) -> float:
    """
    Numerical derivative using forward difference:
        f'(x) ≈ (f(x+h) - f(x)) / h
    """
    return (f(x + h) - f(x)) / h


def integrate(f, a: float, b: float, n: int = 1000) -> float:
    """
    Numerical integration using the rectangular (midpoint) rule.
    """
    if n <= 0:
        raise ValueError("n must be a positive integer")
    dx = (b - a) / n
    total = 0.0
    for i in range(n):
        mid = a + (i + 0.5) * dx
        total += f(mid)
    return total * dx
