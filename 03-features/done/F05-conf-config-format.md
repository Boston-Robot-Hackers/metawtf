# F05 — Conf-only config format

**Priority**: High
**Date Created:** 2026-07-24
**Done:** yes
**Tasks File Created:** yes
**Tests Written:** yes
**Test Passing:** yes

**Description**: Replace the YAML config with a line-oriented `.conf` format
designed for trivial parsing (stdlib only, no pyyaml). One directive per line:
`name [positional] key=value ...`; `#` comment lines; bare values (no quoting,
no escapes, no spaces inside values); lists comma-separated. Type coercion
lives in the existing per-key validators (they now take strings), so there is
a single schema and a single parse path. All errors carry a line number.

```
sample 2
time width=7 format=%M.%S
echo /cmd_vel field=linear.x name=cmd_vel stale_after=2.0 width=8
hz match=^/tf window=2.0
proc_cpu name=cpu_nav2 process=controller_server
sys_cpu name=cpu_idle mode=idle
```

Correctness rules:
- Blank lines and lines starting with `#` are ignored; no trailing comments.
- At most one positional token per line (the topic for echo/hz); every other
  token is `key=value`; a repeated key is an error.
- Directives: `sample` (positional = sample_hz), `time`, and the four column
  metrics. Unknown directive → error naming the line.
- Same validation as before: required keys, unknown keys, `name` forbidden
  with `match`, `subfields` requires `json=true`, `mode` ∈ {busy, idle},
  regexes compiled at load, default widths per metric.
- Default config path becomes `./metawtf.conf`; `-f` accepts any path.
- pyyaml dependency removed (package.xml, imports).

## How to Demo
**Setup**: Package built and sourced; `~/ros2_ws/metawtf.conf` present.

**Steps**:
1. `metawtf` — starts using `./metawtf.conf`.
2. Introduce a typo on line 3 and rerun.

**Expected output**: Run 1 traces as before. Run 2 exits with
`metawtf: line 3: ...` and no traceback.

## Non-Goals (this feature)
- Quoting/escapes or spaces inside values (use shlex later if ever needed).
- Reading the old YAML files (clean cut, not a compat layer).

## Process Gate
After creating this feature file and the corresponding task file, **stop and
present the plan to the user**. Do not write any code until the user approves.
(Approval given in-session: "implement conf-only and convert metawtf.yaml to
metawtf.conf".)
