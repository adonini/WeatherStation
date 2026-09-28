"""Bounded, per-process cache of full-resolution graph history.
Only chart callbacks use this cache; station alerts keep their direct DB reads.
"""
from collections import OrderedDict
from copy import deepcopy
from datetime import timedelta, timezone
from threading import Lock
from time import monotonic


class HistoryCache:
    def __init__(self, collection, time_field, fields, ttl_seconds=30,
                 max_entries=6, clock=monotonic, full_refresh_seconds=600):
        self.collection = collection
        self.time_field = time_field
        fields = set(fields) | {time_field}
        # MongoDB rejects projecting both a parent and one of its children.
        self.projection = {field: 1 for field in fields
                           if not any(field.startswith(parent + '.') for parent in fields)}
        self.projection['_id'] = 0
        self.ttl_seconds = ttl_seconds
        self.max_entries = max_entries
        self.clock = clock
        self.full_refresh_seconds = full_refresh_seconds
        self._entries = OrderedDict()
        self._lock = Lock()

    def read(self, hours, now, force=False):
        """Return every sample, newest first.
        Graphs requesting the same duration share one snapshot for up to 30s.
        Expired snapshots refresh a two-minute overlap; a full read every ten
        minutes also picks up older corrections. A manual refresh bypasses it. 
        """
        hours = float(hours)
        if not 0 < hours <= 48:
            raise ValueError('Graph history must be between 0 and 48 hours')
        # Serialise refreshes so simultaneous callbacks do not duplicate queries.
        with self._lock:
            current = self.clock()
            entry = self._entries.get(hours)
            if not force and entry and current - entry[0] < self.ttl_seconds:
                self._entries.move_to_end(hours)
                return deepcopy(entry[1])

            sort = [(self.time_field, -1)]
            duration = timedelta(hours=hours)
            cutoff = self._utc(now) - duration
            incremental = (not force and entry and entry[1]
                           and current - entry[2] < self.full_refresh_seconds
                           and self._utc(entry[1][0][self.time_field]) >= cutoff)
            if incremental:
                # Replace a recent overlap, keep duplicate timestamps and corrected observations rather than deduplicating by time.
                boundary = max(cutoff, self._utc(entry[1][0][self.time_field])
                               - timedelta(minutes=2))
                recent = list(self.collection.find(
                    {self.time_field: {'$gte': boundary}}, self.projection, sort=sort))
                records = recent + [row for row in entry[1]
                                    if cutoff <= self._utc(row[self.time_field]) < boundary]
                full_read = entry[2]
            else:
                records = list(self.collection.find(
                    {self.time_field: {'$gte': cutoff}}, self.projection, sort=sort))
                full_read = current
            if not records:
                latest = self.collection.find_one({}, self.projection, sort=sort)
                if latest:
                    records = list(self.collection.find(
                        {self.time_field: {'$gte': latest[self.time_field] - duration}},
                        self.projection, sort=sort))

            self._entries[hours] = (self.clock(), records, full_read)
            self._entries.move_to_end(hours)
            while len(self._entries) > self.max_entries:
                self._entries.popitem(last=False)
            return deepcopy(records)

    @staticmethod
    def _utc(stamp):
        return stamp.replace(tzinfo=timezone.utc) if stamp.tzinfo is None else stamp
