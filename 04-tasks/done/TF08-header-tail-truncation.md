# TF08 — Truncate long column headers to their tail (Feature F08)

## T01 — Add tail truncation for headers in the sampler
**Status**: done
**Description**: In `metawtf/sampler.py`, drop the header-widening in
`effective_width` so columns keep their configured width, and truncate an
over-wide header cell from the front (`…` + trailing chars) in `join_human`.
Data cells keep the existing front-keep truncation. csv path unchanged.

## T02 — Update and add tests
**Status**: done
**Description**: Flip `test_column_widens_to_fit_long_header` to assert the new
tail-truncated header, and add a test that a header shorter than the width is
untouched and a header longer than the width shows `…` + tail exactly filling
the width. Confirm csv header tests are unaffected. Run full suite.

## T03 — Docs + literate regen
**Status**: done
**Description**: Update the sampler docstring/comments and regenerate the
sampler literate doc; note the behaviour in spec/README if headers are
described there.
