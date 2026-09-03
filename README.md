# metawtf

**A live, time-aligned dashboard for ROS2 topics** — a config-driven CLI that
samples the fields you name onto one shared clock and prints one row per
tick: aligned columns with a pinned header on a terminal, plain CSV when
piped or redirected.

```
time,    odom_x,   odom_z,   cmd_c,   tf,    cpu_nav2
12:00:01.200, 1.21,     0.04,     4.98,  9.90,  6.2%
12:00:01.400, 1.22,     0.05,     5.01,  9.93,  6.4%
12:00:01.600, 1.24,     0.05,     4.97,  9.88,  6.1%
```

## Why not `ros2 topic echo`, `rqt`, or `ros2 bag`?

A robotics developer juggling `ros2 topic echo` in one terminal, `ros2 topic
hz` in another, and `top` in a third cannot see a velocity command, a TF
rate, and a navigator's CPU% line up in time — each tool has its own pace and
its own window. metawtf merges them onto one shared clock in one place.

- **vs. `ros2 topic echo` / `ros2 topic hz` / `top`.** Same data, but combined:
  one process, one shared sample clock, one row per tick across every topic
  and process you name — instead of three terminals you have to eyeball at
  once.
- **vs. `rqt` / Foxglove.** Both are GUI tools: a display, a windowing
  toolkit or a browser, and (for Foxglove) usually a bridge or a bag file.
  metawtf is a single terminal process — it works over a plain SSH session
  with no display, and its output *is* already a CSV file, not a plot you
  have to export.
- **vs. `ros2 bag`.** A bag is a flight recorder: every raw message,
  serialized, for later replay — high fidelity, but unreadable while
  recording and requiring post-processing to become "just `pose.position.x`
  as a series." metawtf is the opposite trade: a live, deliberately lossy,
  pre-shaped view. Last-known-value sampling at a few Hz produces a CSV a
  spreadsheet opens directly, with derived columns (`hz` rates, JSON-field
  extraction, live array length) a bag can't give you without scripting.

**Rule of thumb:** if you don't yet know which fields you'll need, record a
bag — metawtf can't recover data it didn't sample. If you know exactly which
scalars you want to watch or graph *right now*, that's metawtf.

## Key features

- **Time-aligned columns.** Topics publishing at different rates are
  resampled onto one shared clock, so their values are directly comparable
  and plottable row-for-row.
- **Two output formats, auto-detected.** A terminal gets a pinned, aligned
  `human` view; a pipe or redirect gets plain RFC-4180 `csv` — no flag
  needed, though a `format` directive can force either.
- **Derived columns, not just raw values.** `hz` columns compute receive
  rates; `json=true` reaches inside a JSON string carried in a message field;
  array paths support indexing (`detections[0].id`) and length
  (`detections.#`, `0` on an empty array — a value, not a missing cell).
- **Host and process CPU columns**, alongside topic data, on the same clock.
- **Never crashes on bad data.** A missing field, a stale topic, or
  malformed JSON renders as an empty or `?` cell and recovers on the next
  good message — never a traceback mid-trace.
- **No rebuild to change what you're watching.** Edit `metawtf.conf`,
  re-run; nothing to recompile.
- **Runs interactively.** `space` pauses/resumes, `h` shows help, `q` (or
  `Ctrl-C`) quits cleanly, no Enter needed for any of them.

## Requirements

- ROS2 Jazzy (developed and tested there; no Jazzy-only API is used, so
  other recent distros likely work).
- Python 3, system install — no `uv`, no `pyproject.toml`.
- A `rclpy` workspace with `std_msgs` and `rosidl_runtime_py` (standard on
  any ROS2 install).

## Installation

```bash
cd ~/ros2_ws
colcon build --packages-select metawtf
source install/setup.bash
```

The build installs a `metawtf` command onto your `PATH`, so no `ros2 run` is
needed — it stays available in any shell where the workspace is sourced.

## Quick start

Get a live view of your node graph's log messages in under a minute:

```bash
cat > metawtf.conf <<'EOF'
sample 2
echo /rosout field=msg width=40
EOF
metawtf
```

You should see a pinned header and one row every half-second, with the most
recent `/rosout` message text in the `rosout` column. `q` quits.

## Usage

```bash
metawtf                  # aligned live view on a terminal, CSV when piped
metawtf > run.csv        # capture for a spreadsheet
metawtf -f other.conf    # use a config other than ./metawtf.conf
metawtf -h               # show help and exit
```

On start it reads `metawtf.conf` from the **current working directory** (or
the file given with `-f`). Edit it and re-run — no rebuild needed.
(`metawtf/metawtf.conf` in the repo is a sample to copy; `conf/metawtf.conf`
has a fuller one covering every column type.)

**Keys while running** (no Enter needed): `space` pauses/resumes row output,
`h` shows help, `q` quits (`Ctrl-C` also works). It shuts down cleanly with
no traceback. When stdin is not a terminal (e.g. piped), only `Ctrl-C`
applies.

## Configuration reference

One directive per line: `name [positional] key=value ...`. Blank lines and
lines starting with `#` are ignored (no trailing comments). Values are bare
tokens — no quoting, no spaces inside a value; lists are comma-separated.
Any key not listed below is rejected with a clear error at startup.

```
sample 5.0                  # rows per second (default 5.0)
time format=%H:%M:%S width=12   # optional leading timestamp column

echo /odom field=pose.pose.position.x name=odom_x stale_after=2.0 width=10
echo /explore/status field=data json=true subfields=reached,failed
echo /oak/detections field=detections.#,detections[0].id name=ntrk,first
hz /cmd_vel window=2.0      # receive rate of one topic
hz match=^/tf window=2.0    # one rate column per topic matching the regex
proc_cpu name=cpu_nav2 process=controller_server
sys_cpu name=cpu_idle mode=idle
```

#### Top-level directives

| Directive | Required | Meaning |
|---|---|---|
| `sample` | no | rows per second; positional value must be > 0 (default `5.0`) |
| `time` | no | configures the leading timestamp column; see below |
| `format` | no | `human` or `csv` (positional); default auto-detects from stdout — `human` on a tty, `csv` when piped |
| column directives | yes, at least one | `echo`, `hz`, `proc_cpu`, `sys_cpu`; one per line |

#### `time` directive (the leading timestamp column)

| Key | Required | Type | Default | Rules |
|---|---|---|---|---|
| `format` | no | string | `HH:MM:SS.mmm` | Python `strftime`; the default keeps millisecond precision (which strftime cannot express) |
| `width` | no | int | natural width | must be > 0; pads the column to a minimum width |

#### `echo` column keys

Reports the latest value of a message field, sampled at each tick.

| Key | Required | Type | Default | Rules |
|---|---|---|---|---|
| `topic` | yes | string | — | positional (or `topic=`); the topic to subscribe to |
| `field` | yes | string / list | — | path segments joined by `.`, each optionally indexed (`detections[0].id`) or, as a final segment, `#` for length (`detections.#`) — see below; a comma list makes one column per path from one subscription |
| `name` | no | string / list | sanitized topic | column header; with a multi-field or `subfields` echo it is a comma list, one header per column (count must match) |
| `type` | no | string | resolved from the graph | e.g. `nav_msgs/msg/Odometry`; needed only if the topic isn't up at start or is multi-type |
| `stale_after` | no | number | never stale | must be > 0; blank the cell if no message arrives within this many seconds |
| `width` | no | int / list | `8` | must be > 0; with a multi-field or `subfields` echo a comma list, one width per column (`4,10,6`) |
| `json` | no | bool | `false` | `json=true` parses the extracted field as a JSON string before selecting |
| `subfields` | no | list | all top-level keys | comma-separated; requires `json=true`; dotted keys reach nested objects (`payload.count`) |

A bad `field` path (e.g. a typo) does not crash the trace: that cell shows
`?` until a readable message arrives.

**Multiple fields (`field=` comma list).** One `echo` line can pull several
message fields at once — give `field=` a comma list. Handy for a `Twist` on
`/cmd_vel` where you want `linear.x` and `angular.z` side by side:

```
echo /cmd_vel field=linear.x,angular.z name=vx,wz width=6,6
```

This makes one subscription and one column per path, auto-named
`<sanitized topic>_<path with dots as underscores>` unless `name=` overrides
it with a matching comma list. A single-field echo keeps its plain
single-column behavior. A multi-field `field=` cannot combine with
`json`/`subfields`, which split one JSON string field rather than several
message fields.

**Array indexing and length (`[N]` and `#`).** A path segment can carry an
integer index in brackets to reach into an array-valued field, and the final
segment can instead be a bare `#` for the array's length:

```
echo /oak/detections field=detections.#,detections[0].id name=ntrk,first width=5,6
```

- `NAME[N]` — `N` is an integer; negative counts from the end, so `[-1]` is
  the last element.
- `NAME.#` — only legal as the final segment; resolves to `len(value)`.

A bad index behaves like any other bad `field` path: the cell shows `?`, not
a crash. That includes the case that reads like a bug and is not — on an
empty array, `detections[0].id` is `?` (there is no element 0), while
`detections.#` is `0` (a value). **Length, not indexing, is what answers "how
many."** Only indexing and length are supported: no slices, no wildcards, no
aggregate functions, no arithmetic. Auto-derived headers fold `[`, `]`, `#`,
and `-` the same way they already fold `.` — into `_` (or `n` for `#`/`-`).

**JSON subfields (`json=true`).** Some topics carry structured data as a JSON
string inside a single field (e.g. a `std_msgs/msg/String` whose `data` is
`{"state": "idle", "reached": 0}`). With `json=true`, one config line expands
into one plottable column per selected key:

- Column names are `<sanitized topic>_<key>`, or a `name=` comma list
  overrides them one-for-one.
- Omitting `subfields` expands to all top-level keys of the **first parsed
  message**, in order; the column set is then fixed.
- Malformed JSON, a missing key, or a non-scalar key shows `?` and recovers
  on the next well-formed message. Only scalars (string/number/bool) render.
- `json` is valid only on `echo` columns.

#### `hz` column keys

Reports the rolling message receive rate (`ros2 topic hz`-style span
estimate), formatted with 2 decimals. Give exactly one of `topic` or `match`.

| Key | Required | Type | Default | Rules |
|---|---|---|---|---|
| `topic` | one-of | string | — | positional (or `topic=`); a single topic; column name defaults to the sanitized topic |
| `match` | one-of | string | — | regex over graph topic names; one column per matched topic, added live as topics appear |
| `window` | no | number | `2.0` | rolling window in seconds; must be >= the sample period |
| `name` | no | string | sanitized topic | allowed with `topic`; **forbidden** with `match` |
| `width` | no | int | `6` | must be > 0; pads the cell to a minimum width |

A `match` column set can grow at runtime: when a new topic is discovered the
header is re-emitted before the next row (a fresh CSV header line in that
format; redrawn in place in the pinned human view).

#### `proc_cpu` and `sys_cpu` column keys

CPU usage columns, sampled on the same clock as everything else.

| Key | Required | Type | Default | Rules |
|---|---|---|---|---|
| `name` | yes | string | — | column header |
| `process` | yes (`proc_cpu` only) | regex | — | matched against process cmdlines; usage is summed across matches |
| `mode` | yes (`sys_cpu` only) | `busy` \| `idle` | — | system-wide CPU percent |
| `width` | no | int | `6` | must be > 0 |

Both print as `%.1f%%`.

### Output

Each tick prints the timestamp column plus one value per column. Missing,
stale, or not-yet-published data produces an **empty cell** — never `0`,
never a crash. Floats are formatted with 2 decimals.

**Human format** (default on a terminal): the header is pinned to the top of
the screen via an ANSI scroll region, so rows scroll beneath it and the
header never moves. `width` is a *minimum* column width; a value longer than
it is truncated with `…` at the end; a header wider than its column is
truncated too, keeping its *tail* (`…` at the front) so a distinguishing
suffix like `cpu_nav2`'s `…_nav2` survives. Quitting restores the screen and
leaves the shell prompt below the output. Rows that scroll off the pinned
region are **not** kept in the terminal's scrollback — redirect `csv` output
to a file for a full record.

**CSV format** (default when piped or redirected): pure RFC 4180 — bare
commas, no padding, full untruncated values; any cell containing a comma,
quote, or newline is quoted (inner quotes doubled). No pinned header, no
escape sequences.

## Examples

- `metawtf/metawtf.conf` — the minimal sample copied by "Quick start" above.
- `conf/metawtf.conf` — a fuller example touching every column type
  (multi-field echo, JSON subfields, `hz` by topic and by `match`, `sys_cpu`).

## Troubleshooting

- **No data showing / every cell is empty.** Confirm the topic is actually
  publishing (`ros2 topic hz <topic>`) and that `field=` matches the message
  type — a typo shows as a permanently empty cell, not an error, by design.
- **Edited the code but behavior didn't change.** `colcon build
  --packages-select metawtf && source install/setup.bash` — the installed
  console script does not track the source tree automatically.
- **Rows vanish when I scroll up.** Expected: the pinned header uses an ANSI
  scroll region, and xterm-style terminals do not add rows scrolled off it to
  scrollback. Redirect to CSV for a record you can scroll or grep.
- **A `match=` hz column's header keeps reprinting.** By design — the column
  set grows as new matching topics appear on the graph, and each growth
  re-emits the header so CSV output stays parseable per section.

## Development

```bash
source /opt/ros/jazzy/setup.bash
python3 -m pytest test/ -v
```

Tests run with plain `pytest` (no `colcon test` dependency); sourcing ROS2
first lets the `rclpy`-dependent tests run instead of skipping. For the
internal architecture and design rationale, see `01-literate/00-overview.md`
and the numbered chapters alongside it — each module gets its own literate
walkthrough.

## License

MIT — see [LICENSE](LICENSE)
