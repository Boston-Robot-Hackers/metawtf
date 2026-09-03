# F09 — Clear the screen when the pinned header first appears
**Priority**: Low
**Date Created:** 2026-07-25
**Done:** yes
**Tasks File Created:** yes
**Tests Written:** yes
**Test Passing:** yes
**Description**: In human/tty mode the pinned header sets up a scroll region at
the top of the current screen, so the header often prints amid whatever was
already on the terminal and is easy to miss. On first setup, clear the screen
before drawing the header so it starts clean and obvious at the top. Only the
pinned (tty, human) path is affected; csv/redirected output and the plain
non-tty print path are untouched (clearing a redirected stream would corrupt
it).

## How to Demo
**Setup**: A cluttered terminal, then run metawtf in human mode against a live
topic.

**Steps**:
1. Fill the terminal with prior output.
2. Run metawtf.

**Expected output**: The screen clears and the pinned header appears alone at
the top, with data rows scrolling below it.

## Process Gate
After creating this feature file and the corresponding task file, **stop and present the plan to the user**. Do not write any code or content until the user gives explicit approval to proceed.
