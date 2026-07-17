# Project Notes

Semi-permanent architecture and design notes for metawtf.

## Environment
- ROS2 `ament_python` package, distro **Jazzy**.
- Package name: `metawtf`. Depends: `rclpy`, `std_msgs`.
- Build: `colcon build --packages-select metawtf` from `~/ros2_ws`.
- Test: `colcon test --packages-select metawtf`.

## Architecture
- Single rclpy node, single-threaded executor. Metric callbacks are O(1)
  (store a scalar / append a timestamp); a `sample_hz` timer does all
  formatting and printing. (`ros2 topic hz` prints from a separate thread;
  our callbacks are cheap enough not to need that.)
- Column metrics: `echo` (deserialized field value), `hz` (raw subscription,
  arrival counting only), `proc_cpu` (`/proc` sampling).
- Output: one CSV row per tick to stdout — `HH:MM:SS.mmm` plus one cell per
  column. Header printed once at start, reprinted when the column set grows.
- Wall time everywhere: `time.monotonic()` for intervals/rates,
  `datetime.now()` for the row timestamp. Sim-time support deferred.
- Missing data → empty CSV cell. Never 0, never a crash.

## Research: measuring hz / QoS / CPU correctly (2026-07-17)
Sources: [ros2topic hz.py](https://github.com/ros2/ros2cli/blob/rolling/ros2topic/ros2topic/verb/hz.py),
[ros2cli qos.py](https://github.com/ros2/ros2cli/blob/rolling/ros2cli/ros2cli/qos.py),
[psutil docs](https://psutil.readthedocs.io/en/latest/).

- **QoS**: wrong QoS = silently zero messages. Auto-select per topic like
  `choose_qos`: RELIABLE only if every publisher is RELIABLE, else
  BEST_EFFORT; TRANSIENT_LOCAL only if every publisher is TRANSIENT_LOCAL,
  else VOLATILE. Data source: `node.get_publishers_info_by_topic()`.
- **hz estimator**: inter-arrival times recorded at callback; rate over a
  window = (n−1)/(t_newest − t_oldest) (ros2 computes 1/mean(Δt), same thing).
  Naive count/window under-reports at startup and for sparse topics. Never use
  header stamps — receive rate is what we measure.
- **raw subscriptions**: `create_subscription(..., raw=True)` skips
  deserialization (hz.py does this when no filter is given) — important for
  high-rate image/pointcloud topics.
- **window shape**: ros2 hz uses a count-based window (default 10000 msgs);
  ours is time-based to fit the fixed row cadence.
- **CPU**: cpu% = (Δ(utime+stime) / clk_tck) / Δwall × 100 from
  `/proc/<pid>/stat`; 100% = one core, can exceed 100 (top Irix convention).
  Parse the stat line after the last `)` (comm may contain spaces/parens).
  Match processes by cmdline, not comm — Python ROS nodes all have comm
  `python3`. First sighting of a pid → no value yet (psutil's first
  `cpu_percent()` call returns a meaningless 0.0; we emit an empty cell).
