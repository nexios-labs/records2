import pytest
from pydantic import Field
from records2 import BaseRecord


class TestUser(BaseRecord):
    """Test user model."""
    id: int
    name: str


def test_pydantic_model_creation():
    """Test that Pydantic models work correctly."""
    user = TestUser(id=1, name="Test User")
    assert user.id == 1
    assert user.name == "Test User"
    
    # Test model_dump
    user_dict = user.model_dump()
    assert user_dict == {"id": 1, "name": "Test User"}
    
    # Test JSON serialization
    user_json = user.model_dump_json()
    assert '"id":1' in user_json
    assert '"name":"Test User"' in user_json


def test_pydantic_validation():
    """Test that Pydantic validation works."""
    # Valid user
    user = TestUser(id=1, name="Valid User")
    assert user.id == 1
    
    # Invalid user should raise validation error
    with pytest.raises(Exception):  # Pydantic ValidationError
        TestUser(id="not_an_int", name="Invalid User")
