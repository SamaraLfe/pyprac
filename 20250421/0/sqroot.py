import math

def sqroots(coeffs: str) -> str:
    a, b, c = map(float, coeffs.strip().split())
    if a == 0:
        raise ValueError("Coefficient 'a' cannot be zero")
    d = b * b - 4 * a * c
    if d < 0:
        return ""
    elif d == 0:
        x = -b / (2 * a)
        return f"{x:.6f}"
    else:
        sqrt_d = math.sqrt(d)
        x1 = (-b + sqrt_d) / (2 * a)
        x2 = (-b - sqrt_d) / (2 * a)
        return f"{x1:.6f} {x2:.6f}"