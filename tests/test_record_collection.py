import pytest

from records2 import record

# Test RecordCollection features


def make_records():
    return [
        record.Record(keys=["id", "name"], values=[i, f"Name{i}"]) for i in range(3)
    ]


def test_record_collection_iteration():
    from records2.record import RecordCollection

    rc = RecordCollection(iter(make_records()))
    items = list(rc)
    assert len(items) == 3
    assert items[0]["id"] == 0
    assert items[2]["name"] == "Name2"


def test_record_collection_slice():
    from records2.record import RecordCollection

    rc = RecordCollection(iter(make_records()))
    first_two = rc[:2]
    assert isinstance(first_two, RecordCollection)
    assert len(list(first_two)) == 2


def test_record_collection_first_and_one():
    from records2.record import RecordCollection

    rc = RecordCollection(iter(make_records()))
    first = rc.first()
    assert first["id"] == 0
    rc_one = RecordCollection(iter([make_records()[0]]))
    assert rc_one.one()["id"] == 0
    rc_empty = RecordCollection(iter([]))
    assert rc_empty.first(default=None) is None
    assert rc_empty.one(default=None) is None
    with pytest.raises(Exception):
        RecordCollection(iter(make_records())).one()


def test_record_collection_scalar():
    from records2.record import RecordCollection

    rc = RecordCollection(iter(make_records()))
    assert rc.scalar() == 0
    rc_empty = RecordCollection(iter([]))
    assert rc_empty.scalar(default=42) == 42
