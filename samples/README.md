# Synthetic, redistributable GTFS fixtures

`baseline.zip` and `candidate.zip` contain **invented place names and data** for
unit tests and demonstrations. They are *not real transit service* and must not be
used for trip planning. They intentionally include losses through parent-station
inheritance, a `2 → 1` metadata change, an `unknown → 1` gain, and an added/removed
ID. Their only file is `stops.txt`, because the v0.1 analyzer only reads it.
