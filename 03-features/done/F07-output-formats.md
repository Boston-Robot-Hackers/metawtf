# F07 — Human/CSV output formats with pinned header

**Priority**: Medium
**Done:** yes
**Tasks File Created:** yes
**Tests Written:** yes
**Test Passing:** yes

**Description**: The sampler today emits one hybrid stream: RFC-4180 quoting
*plus* padding so columns line up in a terminal. Live readers pay for the
padding (headers force wide columns, long values shove rows around), and CSV
consumers get padding and leading spaces they must tolerate. This feature
splits output into two formats:

- **csv** — pure RFC-4180: comma-joined, quoted only when needed, no padding,
  full untruncated values. Imports cleanly into spreadsheets/pandas.
- **human** — padded and aligned as today, but values wider than their column
  are truncated with `…` so rows never misalign, and the header is pinned to
  the top of the terminal via an ANSI scroll region (DECSTBM): rows scroll
  below the frozen header while the terminal's existing scrollback is
  untouched. (xterm-style terminals do not add rows scrolled off a scroll
  region to scrollback — redirect csv output to a file for a full record.)

Mode selection: a new `format human|csv` directive in `metawtf.conf`. When
the directive is absent, the mode is auto-detected from stdout — a tty gets
`human`, a pipe or redirect gets `csv`, so `metawtf > out.csv` just works.

Rules and semantics:

- `format` is a singleton directive with one positional value (`human` or
  `csv`); anything else — a bad value, a `key=value` option, a repeat — is a
  line-numbered config error.
- Auto-detection happens at startup in the node, not in the sampler: the
  sampler just renders the mode it is given.
- csv mode changes nothing but the join: header reprint on column growth
  (hz `match`, json expander) stays, as a documented CSV caveat.
- human mode truncates *values* to the effective column width with `…`;
  headers are never truncated (`name=` remains the fix for wide headers).
- The pinned header is active only in human mode on a tty. Forcing
  `format human` into a pipe yields padded, unpinned text.
- The header is redrawn in place when the column set grows mid-run; the
  scroll region is re-issued so terminal resizes stay sane.
- On quit (`q`, Ctrl-C, stdin EOF) the scroll region is reset and the cursor
  drops below the output, so the shell prompt lands cleanly and scrollback is
  intact.

## How to Demo
**Setup**: A publisher on a stand-in topic (never a real robot topic):
`ros2 topic pub -r 2 /mw_demo_status std_msgs/msg/String '{data: "{\"state\": \"exploring\", \"reached\": 3}"}'`
and a `metawtf.conf` with:
```
echo /mw_demo_status field=data json=true subfields=state,reached
```

**Steps**:
1. Run `metawtf` in a terminal — no `format` directive.
2. Pipe it: `metawtf | head -5`.
3. Add `format csv` and run in the terminal again.

**Expected output**:
1. Header frozen at the top, rows scrolling beneath; long values clipped with
   `…`; `q` quits and the prompt lands below the output with scrollback kept.
2. Plain comma-joined rows, no padding, no escape sequences.
3. Same plain csv on the terminal; no pinned header.

## Non-Goals (this feature)
- Truncating columns to the terminal width — truncation is per column to the
  configured width; a config wider than the terminal still wraps.
- Full-screen alternate-buffer UI (htop-style repaint) — the scroll region
  keeps normal scrollback instead.
- Making pause/help stderr messages scroll-region aware.

## Process Gate
After creating this feature file and the corresponding task file, **stop and
present the plan to the user**. Do not write any code until the user approves.
(Plan presented and approved 2026-07-25.)
