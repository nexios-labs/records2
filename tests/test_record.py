import pytest

from records2 import record

# Test Record basic attribute and key access


def test_record_keys_and_values():
    rec = record.Record(keys=["id", "name"], values=[1, "Test"])
    assert rec.keys() == ["id", "name"]
    assert rec.values() == [1, "Test"]
    assert rec[0] == 1
    assert rec[1] == "Test"
    assert rec["id"] == 1
    assert rec["name"] == "Test"
    assert rec.get("id") == 1
    assert rec.get("missing", default=42) == 42


def test_record_as_dict():
    rec = record.Record(keys=["id", "name"], values=[1, "Test"])
    d = rec.as_dict()
    assert d == {"id": 1, "name": "Test"}
    od = rec.as_dict(ordered=True)
    assert list(od.keys()) == ["id", "name"]


def test_record_keyerror():
    rec = record.Record(keys=["id", "name"], values=[1, "Test"])
    with pytest.raises(KeyError):
        _ = rec["missing"]
    with pytest.raises(AttributeError):
        _ = rec.missing


def test_record_repr():
    rec = record.Record(keys=["id", "name"], values=[1, "Test"])
    assert "Record" in repr(rec)
