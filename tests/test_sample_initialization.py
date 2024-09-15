import pytest


def add(a, b):
    """Return the sum of a and b."""
    return a + b


def subtract(a, b):
    """Return the difference between a and b."""
    return a - b


def test_add():
    """Test function for add."""
    assert add(1, 2) == 3
    assert add(-1, 1) == 0
    assert add(0, 0) == 0


def test_subtract():
    """Test function for subtract."""
    assert subtract(2, 1) == 1
    assert subtract(1, 1) == 0
    assert subtract(0, 1) == -1


@pytest.mark.parametrize("a, b, expected", [
    (1, 2, 3),
    (-1, 1, 0),
    (0, 0, 0),
])
def test_add_parametrized(a, b, expected):
    """Parameterized test function for add."""
    assert add(a, b) == expected