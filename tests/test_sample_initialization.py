```python
import pytest

def add(a: float, b: float) -> float:
    """Return the sum of a and b."""
    return a + b

def subtract(a: float, b: float) -> float:
    """Return the difference of a and b."""
    return a - b

def test_add():
    """Test the add function with various inputs."""
    assert add(1, 2) == 3
    assert add(-1, 1) == 0
    assert add(0, 0) == 0

def test_subtract():
    """Test the subtract function with various inputs."""
    assert subtract(2, 1) == 1
    assert subtract(1, 1) == 0
    assert subtract(0, 1) == -1

@pytest.mark.parametrize("a, b, expected", [
    (1, 2, 3),
    (-1, 1, 0),
    (0, 0, 0),
])
def test_add_parametrized(a: float, b: float, expected: float):
    """Test the add function using parameterized inputs."""
    assert add(a, b) == expected
```