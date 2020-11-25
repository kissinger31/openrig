"""General number functions"""


def isclose(a, b, rel_tol=1e-09, abs_tol=0.0):
    return abs(a-b) <= max(rel_tol * max(abs(a), abs(b)), abs_tol)


def isfloat(value):
    """Identity test for floats or string floats (1.0 or "1.0")."""
    if isinstance(value, float):
        return True
    if isinstance(value, str or basestring):
        if not value.isdigit():
            try:
                float(value)
                return True
            except ValueError:
                return False
    return False


def isint(value):
    """Identity test for ints or string ints (1 or "1")."""
    if not isinstance(value, bool):
        if isinstance(value, int):
            return True
        if isinstance(value, str or basestring):
            if not isinstance(value, bool):
                if value.isdigit():
                    return True
    return False
