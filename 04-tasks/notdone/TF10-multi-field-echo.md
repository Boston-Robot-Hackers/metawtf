# TF10 Multi-field echo columns for Feature F10
**Date Created:** 2026-07-29

## TF10.0 — `field=` as a comma list in EchoColumn
**Status**: done
**Description**: `field=` accepts a comma list (no separate `fields`/`names`
keyword). One path is the plain single column; several fan out into
`EchoColumn.fields`/`field_names`/`field_widths`. Reject a multi-path `field`
combined with `json`/`subfields`. Test: parsing produces fields/names/widths;
single path stays a single column; conflict cases raise.

## TF10.1 — per-column widths and names
**Status**: done
**Description**: `width=` and `name=` are comma lists matched to the column
count on a multi-field/`subfields` echo (`parse_width_list`, `resolve_multi_
names`); auto headers are `<topic>_<path>`. Test: width/name count mismatch
raises; custom names apply to fields and subfields.

## TF10.2 — fan out one subscription into N EchoColumnState
**Status**: done
**Description**: `ColumnManager.add_echo_column` builds one `EchoColumnState`
per field path from a single subscription. Test in `test_column_manager.py`:
one subscription, N named states, values track their paths.

## TF10.3 — docs
**Status**: done
**Description**: Update `metawtf.conf` grammar header, README, and literate
`01-config.md`.
