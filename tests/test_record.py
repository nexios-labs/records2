import pytest
from typing import Optional
from pydantic import Field

from records2 import BaseRecord

# Test BaseRecord (Pydantic model) functionality


class TestRecord(BaseRecord):
    """Test record model."""
    id: int
    name: str


class TestOptionalRecord(BaseRecord):
    """Test record with optional fields."""
    id: int
    name: str
    description: Optional[str] = None


def test_record_keys_and_values():
    rec = TestRecord(id=1, name="Test")
    assert rec.model_dump()["id"] == 1
    assert rec.model_dump()["name"] == "Test"
    assert rec.id == 1
    assert rec.name == "Test"


def test_record_as_dict():
    rec = TestRecord(id=1, name="Test")
    d = rec.model_dump()
    assert d == {"id": 1, "name": "Test"}
    od = rec.model_dump()
    assert list(od.keys()) == ["id", "name"]


def test_record_keyerror():
    rec = TestRecord(id=1, name="Test")
    with pytest.raises(KeyError):
        _ = rec.model_dump()["missing"]
    with pytest.raises(AttributeError):
        _ = rec.missing


def test_record_repr():
    rec = TestRecord(id=1, name="Test")
    assert "TestRecord" in repr(rec)
