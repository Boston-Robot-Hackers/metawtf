# TF04 — JSON-string subfield columns, tasks for Feature F04

Builds on F01 (echo columns, field extractor, sampler) and reuses the `?`
invalid-cell behavior. All parsing/selection logic is pure and unit-testable
without a ROS graph; live delivery is covered by the demo.

## T01 — Schema: json + subfields on echo columns
**Status**: done
**Description**: Extend `parse_echo_column`: optional `json` (bool, default
false) and optional `subfields` (non-empty list of non-empty dotted-key
strings). `subfields` requires `json: true` (else clear error). With more than
one subfield, `name` is forbidden (clear error), mirroring hz `match`. Add
`json`/`subfields` to `ECHO_KEYS`. `json` on a non-echo metric is already
rejected because those metrics have their own key sets.
**Test**: Unit tests over YAML — valid json+subfields parse; `subfields` without
`json`, `name` with multiple subfields, empty/blank subfield, non-bool `json`
each raise a clear error; a plain echo column still parses unchanged.

## T02 — JSON value selector
**Status**: done
**Description**: Pure function: given a parsed JSON object and a dotted key,
return the scalar value, or raise a distinct error when the path is missing or
lands on a non-scalar (object/array/null). Separate from `field_extract` since
it walks dict keys, not object attributes.
**Test**: Unit test — flat key, nested dotted key, missing key raises, key
resolving to an object/array raises, scalar types (str/int/float/bool) returned.

## T03 — JSON echo column state
**Status**: done
**Description**: A column state (per selected subfield) that, on each message,
extracts the string via the existing field extractor, parses it with
`json.loads`, and selects its key. Any failure (bad attribute path, JSON parse
error, missing key, non-scalar) stores the `INVALID` sentinel so `sample`
returns `?`; success stores the scalar. Formatting reuses `format_value`.
Parsing the same string once per message per column is acceptable at trace
rates; note it as a possible future optimization (parse once, share).
**Test**: Unit test with fake messages — good JSON yields the value; malformed
JSON, missing key, and non-scalar each yield `?`; recovery after a good message;
empty before first message.

## T04 — Column expansion in the manager/config
**Status**: done
**Description**: One json echo entry expands to one column per subfield. Decide
and implement the expansion point (config produces a list of leaf column specs,
or the manager fans out one subscription feeding several column states). Exactly
one subscription per topic entry; each subfield column shares it. Column names
`<sanitized topic>_<key with dots→underscores>`; a single-subfield column may
use an explicit `name`.
**Test**: Unit test — a json entry with two subfields yields two named column
states from one subscription spec; single-subfield naming (default and explicit).

## T05 — Omitted subfields = all top-level keys
**Status**: done
**Description**: When `subfields` is omitted (but `json: true`), expand to all
top-level keys of the first parsed message, in insertion order. Columns are
fixed once first seen; keys appearing in later messages are ignored (documented
caveat), missing keys render `?`. If no message has arrived yet there are no
columns for that entry until one does (header reprint via F02's mechanism).
**Test**: Unit test with a fake first message — columns match its keys in order;
a later message with an extra/missing key does not add/remove columns and yields
`?` for the missing one.

## T06 — Feature test suite + demo verification
**Status**: done — full pytest green (112); live demo run by the user on
2026-07-22 showed scalar columns for the JSON keys and `?` on a malformed
message.
**Description**: T01–T05 pass together; run the demo against a JSON-string
publisher on a **non-real** topic (`/mw_demo_status`), including a deliberately
malformed message to show `?`.
**Test**: Full `pytest` green; demo shows numeric columns for the JSON keys and
`?` on the malformed message.
