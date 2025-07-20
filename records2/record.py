# -*- coding: utf-8 -*-

from collections import OrderedDict

import tablib


def _reduce_datetimes(row):
    # Placeholder, will be replaced by import from utils.py
    return row


class Record(object):
    """A row, from a query, from a database."""

    __slots__ = ("_keys", "_values")

    def __init__(self, keys, values):
        self._keys = keys
        self._values = values
        assert len(self._keys) == len(self._values)

    def keys(self):
        return self._keys

    def values(self):
        return self._values

    def __repr__(self):
        return "<Record {}>".format(self.export("json")[1:-1])

    def __getitem__(self, key):
        if isinstance(key, int):
            return self.values()[key]
        usekeys = self.keys()
        if hasattr(usekeys, "_keys"):
            usekeys = usekeys._keys
        if key in usekeys:
            i = usekeys.index(key)
            if usekeys.count(key) > 1:
                raise KeyError("Record contains multiple '{}' fields.".format(key))
            return self.values()[i]
        raise KeyError("Record contains no '{}' field.".format(key))

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError as e:
            raise AttributeError(e)

    def __dir__(self):
        standard = dir(super(Record, self))
        return sorted(standard + [str(k) for k in self.keys()])

    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default

    def as_dict(self, ordered=False):
        items = zip(self.keys(), self.values())
        return OrderedDict(items) if ordered else dict(items)

    @property
    def dataset(self):
        data = tablib.Dataset()
        data.headers = self.keys()
        row = _reduce_datetimes(self.values())
        data.append(row)
        return data

    def export(self, format, **kwargs):
        return self.dataset.export(format, **kwargs)


class RecordCollection(object):
    """A set of excellent Records from a query."""

    def __init__(self, rows):
        self._rows = rows
        self._all_rows = []
        self.pending = True

    def __repr__(self):
        return "<RecordCollection size={} pending={}>".format(len(self), self.pending)

    def __iter__(self):
        i = 0
        while True:
            if i < len(self):
                yield self[i]
            else:
                try:
                    yield next(self)
                except StopIteration:
                    return
            i += 1

    def next(self):
        return self.__next__()

    def __next__(self):
        try:
            nextrow = next(self._rows)
            self._all_rows.append(nextrow)
            return nextrow
        except StopIteration:
            self.pending = False
            raise StopIteration("RecordCollection contains no more rows.")

    def __getitem__(self, key):
        is_int = isinstance(key, int)
        if is_int:
            key = slice(key, key + 1)
        while key.stop is None or len(self) < key.stop:
            try:
                next(self)
            except StopIteration:
                break
        rows = self._all_rows[key]
        if is_int:
            return rows[0]
        else:
            return RecordCollection(iter(rows))

    def __len__(self):
        return len(self._all_rows)

    def export(self, format, **kwargs):
        return self.dataset.export(format, **kwargs)

    @property
    def dataset(self):
        data = tablib.Dataset()
        if len(list(self)) == 0:
            return data
        first = self[0]
        data.headers = first.keys()
        for row in self.all():
            row = _reduce_datetimes(row.values())
            data.append(row)
        return data

    def all(self, as_dict=False, as_ordereddict=False):
        rows = list(self)
        if as_dict:
            return [r.as_dict(ordered=as_ordereddict) for r in rows]
        return rows

    def as_dict(self, ordered=False):
        return self.all(as_dict=True, as_ordereddict=ordered)

    def first(self, default=None, as_dict=False, as_ordereddict=False):
        try:
            row = self[0]
        except IndexError:
            return default
        if as_dict:
            return row.as_dict(ordered=as_ordereddict)
        return row

    def one(self, default=None, as_dict=False, as_ordereddict=False):
        rows = self.all()
        if len(rows) == 0:
            return default
        if len(rows) > 1:
            raise Exception("Multiple rows found when exactly one was required.")
        row = rows[0]
        if as_dict:
            return row.as_dict(ordered=as_ordereddict)
        return row

    def scalar(self, default=None):
        try:
            return self[0][0]
        except IndexError:
            return default
