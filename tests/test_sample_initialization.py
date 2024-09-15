```python
import pytest

def add(a: int, b: int) -> int:
    """Return the sum of two numbers."""
    return a + b

def subtract(a: int, b: int) -> int:
    """Return the difference of two numbers."""
    return a - b

def test_add() -> None:
    """Test the add function with various cases."""
    assert add(1, 2) == 3
    assert add(-1, 1) == 0
    assert add(0, 0) == 0

def test_subtract() -> None:
    """Test the subtract function with various cases."""
    assert subtract(2, 1) == 1
    assert subtract(1, 1) == 0
    assert subtract(0, 1) == -1

@pytest.mark.parametrize("a, b, expected", [
    (1, 2, 3),
    (-1, 1, 0),
    (0, 0, 0),
])
def test_add_parametrized(a: int, b: int, expected: int) -> None:
    """Test the add function using parameterized tests."""
    assert add(a, b) == expected
```