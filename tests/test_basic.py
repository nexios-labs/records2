import pytest

from records2 import record


def test_record_creation():
    rec = record.Record(keys=["id", "name"], values=[1, "Test"])
    assert rec["id"] == 1
    assert rec["name"] == "Test"
