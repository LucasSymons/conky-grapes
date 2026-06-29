# Conky-grapes alignment worklog

Living document for the ongoing task of getting the **text labels to line up
nicely with the ring graphs**, section by section, top to bottom. Written so a
fresh session (after a context/session limit) can resume with zero re-discovery.

**Branch:** `Setup-personal` (Lucas's live desktop config - multi-monitor,
`xinerama_head = 3`). All this work lives here, not on `master`.

**Status:** in progress. Working order: CPU (ok, skip) -> IO WAIT (done) ->
**MEMORY (current)** -> FILESYSTEM -> INTERNET -> CLOCK/OS.

> **ALIGNMENT INTENT (Lucas's actual goal - confirmed 2026-06-22):** each
> section's text lines up with an **EDGE of its ring graph, not the centre.**
> - IO WAIT: text **top** aligns to the ring **top**. (done)
> - MEMORY: the SWAP/RAM rows align to the ring **bottom**.
> - Other sections: ask Lucas which edge as you reach them.
> My first pass mistakenly *centred* the text - that was wrong. Edge-align.

---

## 0. Resume in 60 seconds (read this first)

1. `git log --oneline -5` on branch `Setup-personal` - the IO WAIT work is
   committed (3 commits: fix/conky, feat/tools, docs/alignment).
2. The overlay is live. Re-capture any time: `tools/capture.sh <section>` then
   Read the printed `/tmp/conky_<section>.png`.
3. **Current task: MEMORY** - move the SWAP/RAM rows so they line up with the
   **bottom** of the MEMORY ring (local y 294). See the bottom of section 5.
4. Edit -> `tools/deploy.sh` -> `tools/capture.sh memory` -> Read -> repeat.
5. Lint after editing `create_config.py`: `uvx ruff check create_config.py`
   and `uvx ruff format create_config.py` (ruff is NOT installed in the venv;
   use `uvx`. Note: `uv run` will rebuild `.venv` - harmless, re-`uv sync` if
   you want it back).

**Gotcha - generated files are gitignored.** `.gitignore` has `*.conkyrc` and
`*.lua`, so `conky_gen.conkyrc` and `rings-v2_gen.lua` are NOT tracked. The only
tracked source is `create_config.py`. Always backport layout edits there.
The on-disk `conky_gen.conkyrc` is still what `deploy.sh` pushes live, so keep
it and `create_config.py` consistent by hand (backport verification TODO: run
`create_config.py` in a throwaway copy and diff the gen file - do NOT run it in
place, it re-detects hardware and overwrites the tuned live config).

---

## 1. The big unlock: no more manual screenshots

conky-grapes renders onto the live KDE/Wayland desktop. We can screenshot and
inspect it directly from the shell - no need for Lucas to grab images by hand.

- **Only `spectacle` works** for the capture. The session is Wayland
  (`XDG_SESSION_TYPE=wayland`, KDE/Plasma). X11 tools (`import`, `xwininfo`,
  `xdotool`) cannot see the Wayland compositor. `spectacle -b -n -f -o FILE`
  does a non-interactive full-desktop grab through the Plasma portal.
- **The desktop is 6000px wide** (3-monitor layout). conky is on the right-most
  head. Cropping to the conky window is done from its config geometry, so we
  never eyeball coordinates.
- **Background:** Lucas set the wallpaper to **solid black** for this work.
  Keep it black - the theme is light-on-dark (gold body text `#cab135`, skyblue
  titles `#8fd3ff`, blue arcs). White would wash out exactly those light colours.
  On black the dark-grey ring tracks (`0x3b3b3b`) are also clearly visible.

### Tools (committed, in `tools/`)

```bash
tools/capture.sh [section] [zoom%]   # screenshot + crop to a section, prints PNG path
tools/deploy.sh                      # copy gen files to ~/.conky + restart conky daemon
```

`capture.sh` sections: `full cpu iowait memory filesystem internet clock os`.
It reads the desktop width at runtime and derives the conky window's right edge
as `width - gap_x`, so it survives a resolution change. Section crop boxes are
in conky-local pixels and are easy to nudge inside the script.

Read a capture with the Read tool, e.g. `Read /tmp/conky_iowait.png`.

---

## 2. The iteration loop

```
edit conky_gen.conkyrc  ->  tools/deploy.sh  ->  tools/capture.sh <section>  ->  Read the PNG  ->  repeat
```

`deploy.sh` copies the runtime files into `~/.conky/conky-grapes/` and restarts
the daemon (conky is launched at login from
`~/.config/autostart/conky.desktop`).

**To make ring arcs visible while tuning IO/disk:** induce load, e.g.
`dd if=/dev/zero of=/tmp/x bs=1M count=2000 oflag=direct` in the background, then
capture. Idle I/O shows near-empty (grey) arcs.

---

## 3. Architecture & source of truth (READ BEFORE EDITING)

```
conky_tpl  +  rings-v2_tpl                 <- templates (placeholders #{{ X }})
        |  create_config.py  (generator, auto-detects hardware)
        v
conky_gen.conkyrc  +  rings-v2_gen.lua     <- GENERATED runtime artifacts (committed)
        |  tools/deploy.sh  (cp)
        v
~/.conky/conky-grapes/*                     <- LIVE copy conky actually reads
```

- The per-section **text layout** (the `${goto}` / `${voffset}` / `${alignr}`
  lines) is **injected by `create_config.py`**, not present in `conky_tpl`
  (which only has `#{{ DISKIO }}` etc. placeholders).
- **`create_config.py` is the source of truth.** If you only edit
  `conky_gen.conkyrc`, a future `create_config.py` run (hardware change) wipes
  the tweak.
- **Workflow:** iterate fast on `conky_gen.conkyrc` (instant via deploy). Once a
  section's numbers are locked, **backport the same deltas into
  `create_config.py`** so a regen reproduces them. Backport map below.

### Where each section's text lives in `create_config.py`

| Section    | conky_gen.conkyrc lines | create_config.py |
|------------|-------------------------|------------------|
| CPU        | 76-86                   | ~`#{{ CPU }}` block, line ~551 (built ~501-551) |
| IO WAIT    | 88-93                   | lines **568-586** |
| MEMORY     | 96-101                  | ~`#{{ MEMORY }}` block, line ~677 |
| FILESYSTEM | 104-107                 | ~`#{{ FILESYSTEM }}` block, line ~453 |
| INTERNET   | 109-114                 | ~`#{{ NETWORK }}` block, lines ~746-777 |
| TIME/clock | 118-119                 | ~`#{{ TIME }}` block, line ~795 |
| OS         | 123                     | ~`#{{ OS }}` block, line ~362 |

(Line numbers are approximate - grep the placeholder to confirm.)

---

## 4. Coordinate reference

**conky window** (from `conky_tpl` / `conky_gen.conkyrc`): `520 x 600`,
`alignment = top_right`, `gap_x = 20`, `gap_y = 112`, `xinerama_head = 3`.
On the 6000px canvas the window screen origin is `(5460, 112)`.

**conky.text positioning primitives:**
- `${goto N}`   - set X to absolute conky-local pixel N.
- `${alignr N}` - right-align the following text N px from the window's right edge.
- `${voffset N}`- move pen down N px (negative = up). **Accumulates** down the
  block, which is why vertical positions are fragile - changing one row shifts
  everything below it.

**Ring centres** (from `rings-v2_gen.lua`, conky-local coords):

| Ring group | centre (x,y) | radii (outer->inner) | top / bottom (local y) |
|------------|--------------|----------------------|------------------------|
| IO WAIT (`top_io io_perc 1/2/3`) | (370, 98)  | 55 / 42 / 30 (th 12/11/10), arc 120->360 | top 43 / bottom 153 |
| MEMORY (`memperc` / `swapperc`)  | (340, 234) | 60 / 45 (th 15/12), arc 180->420         | top 174 / **bottom 294** |

(Other groups' centres to be filled in as we reach each section - grep
`settings_table` / `x=`/`y=` blocks in `rings-v2_gen.lua`.)

The IO ring spans local x 315..425, y 43..153. Any text with `goto < ~430` near
that y band collides with the arc.
The MEMORY ring spans local x 280..400, y 174..294.

---

## 5. Progress log

### 2026-06-22 - setup + IO WAIT baseline

- Built the capture/deploy tooling; confirmed the full loop works.
- Lucas switched wallpaper to solid black (much clearer; keep it).
- Baselines saved: `docs/baseline/2026-06-22_full_baseline.png`,
  `docs/baseline/2026-06-22_iowait_baseline.png`.

**IO WAIT observations (with live I/O so arcs are lit):**
1. **Heading overlaps the ring.** `IO WAIT` is at `${goto 418}` but the ring
   reaches local x=425, so "IO" sits on top of the blue arc. Needs to move
   clear (right and/or down) of the arc's lower-right edge (~x428, y137).
2. **Stray `%` on byte values (content bug, not alignment).** The value column
   shows `1.29MiB%`, `48.0KiB%`, `0B%`, `12.1MiB%`, `144KiB%`. The template
   hardcodes `%` after `${top_io io_write N}` and `${diskio_write/read}`, which
   are byte amounts/rates, not percentages. The `%` should be dropped (confirm
   with Lucas before changing content vs pure alignment).
3. Process-label block (`top_io name 1/2/3`) sits to the right of the rings,
   roughly upper-aligned; revisit vertical centring on the ring after fixing 1.

**IO WAIT current values** (`conky_gen.conkyrc` 88-93): process rows
`${goto 378}` + `${alignr 30}`; disk rows `${goto 370}` + `${alignr 30}`;
heading was `${goto 418}${voffset 1}`.

**DONE - heading overlap fixed:** moved `IO WAIT` heading `goto 418 -> 432`
(horizontal only, so no vertical reflow of sections below). Verified under load:
the "I" now clears the ring's right edge with a small gap, "T" still inside the
window. Backported to `create_config.py` lines 579 (`--old`) and 581 (normal) -
all three (gen / source / live) agree on `goto 432`.
After-image: `docs/baseline/2026-06-22_iowait_after_heading_fix.png`.

**DONE - `%` bug fixed** (Lucas approved): dropped the stray `%` after
`${top_io io_write N}` and `${diskio_write/read}` in all 5 IO value lines.
Values now read `1.28MiB`, `32.0KiB`, `0B` etc.; right-align column unchanged.
Synced across gen / source (`create_config.py`) / live.
Final image: `docs/baseline/2026-06-22_iowait_final.png`.

**DONE - text top aligned to ring top** (Lucas: "perfect!!"). Moved the IO text
cluster UP via `top_io name 1` voffset `-130 -> -148`, so the firefox row sits at
the top of the outer ring. `voffset` accumulates, so this also lifted the disk
rows + heading; compensated by raising the MEMORY heading voffset `59 -> 77`
(and `--old` variant `79 -> 97` in create_config.py) to hold MEMORY in place.
Backported to `create_config.py` (lines 568, 657, 655). gen / source / live all
in sync. Final image: `docs/baseline/2026-06-22_iowait_final.png`.

Known, NOT fixed (data-dependent, pre-existing): a long process name like
`steamwebhelper` overruns its right-aligned value (`name` at goto 378, value at
alignr 30 collide). Only bites on long names. Ask Lucas if he wants names
truncated.

**IO WAIT done. Next: MEMORY** - target is **SWAP/RAM rows aligned to the MEMORY
ring bottom (local y 294)**. MEMORY ring centre (340,234), bottom 294.
- conky_gen.conkyrc lines 96-101; source in create_config.py ~655-657 (heading,
  built ~648-677). SWAP line 100, RAM line 101.
- Method: find current SWAP/RAM y, shift so RAM (last row) bottom sits at local
  y 294; remember `voffset` accumulates into FILESYSTEM below - compensate there.
- Capture with `tools/capture.sh memory`; induce nothing (memory always has
  values). Confirm the MEMORY heading compensation (77) still looks right after.

### 2026-06-28 - autonomous pass: MEMORY / FILESYSTEM / INTERNET / CLOCK

Capture method re-confirmed working (Wayland + spectacle, `tools/capture.sh`).
Used **annotated captures** this round: overlay a horizontal/vertical line at the
ring's known edge (e.g. memory ring bottom y294 -> image y (294-170)*3 = 372 in
the 300%-zoom crop) so alignment is judged against geometry, not by eye. Saved to
`docs/baseline/2026-06-28_*.png`.

**MEMORY - TESTED THE TARGET, REVERTED (it regresses).** Pulled SWAP/RAM up so
RAM's baseline meets the ring bottom (y294): `voffset 8 -> -4` on the SWAP line.
Result: RAM lands on the bottom edge BUT SWAP gets crowded right up against the
last process row (`jellyfin`) - the jellyfin->SWAP gap collapses to ~3-10px,
which looks worse than the original. The crowding is unavoidable if RAM must reach
294 (SWAP then has to sit ~18px above it, into the process block).
**Verdict: the ORIGINAL spacing is the best balance** - SWAP already sits at the
ring bottom (294) with RAM just below and a clean gap above. Reverted to
`voffset 8`. See `2026-06-28_memory_target-test-REVERTED.png`. *If Lucas still
wants RAM exactly at 294 despite the tighter gap, the change is `voffset 8 -> -4`
on conky_gen line 100 + compensate FILESYSTEM `-81 -> -69`.*

**FILESYSTEM - EDGE-ALIGNED TO RING TOP (applied, LIVE, pending Lucas's eye).**
The 3 fs rows floated below the ring top (top row `/` at local ~253; ring top is
235). Moved the block up so `/` meets the ring top, matching the IO-WAIT pattern
(text top -> ring top). Change: conky_gen line 104 `voffset -81 -> -99` (rows +
heading shift up 18), compensated by INTERNET line 109 `voffset 26 -> 44` so
nothing below moves. See `2026-06-28_filesystem_after_topalign.png` (the `/` row
now sits on the red ring-top line). **Judgment call** - it's more deliberately
edge-aligned, but it does lift FILESYSTEM slightly above MEMORY's row band; revert
both voffsets if you prefer the old floating position.
- **NOT yet backported** (kept in the iterate stage until locked). Backport map:
  create_config.py FILESYSTEM block builds the fs rows ~426-436 with
  `voffset = -80` / `voffset = -81` (two variants) -> change to -98 / -99; and the
  INTERNET leading voffset (the `26`) needs +18. Verify via throwaway-diff before
  committing the generator (per the TODO in section 0).

**INTERNET - alignment is fine; the real issue is a CONTENT bug.** The text block
is taller than its small ring (r30, top309/bottom381); heading sits ~ring centre,
text flows below - natural, no edge-align win available. BUT the **Public IP line
overflows the window's right edge** (line 114, `${execi 3600 curl -s
https://icanhazip.com}` returns the **IPv6** here -> `2001:db8::...`
runs off the 520px window). See `2026-06-28_internet_ipv6-overflow.png`.
**Needs Lucas's call** (content, not alignment) - options:
  1. Force IPv4: `curl -s -4 https://icanhazip.com` (short, fits).
  2. Keep IPv6 but shrink that line's font, or move the value to its own line.
  3. Drop the Public IP row entirely (Local IP already shown).

**CLOCK / CPU / OS - assessed, left as-is.** Clock (date + big time, left of its
ring) reads clean; CPU was already fine; OS is centred at the bottom. No clear
edge-align improvement without imposing taste.

**Summary of the pass:** the layout was already cohesive. Net change applied =
**FILESYSTEM top-align only** (live, revertible, unbackported pending approval).
MEMORY target tested + reverted. INTERNET IPv6 overflow flagged for a content
decision. Everything else judged already-good. Next session: get Lucas's yes/no on
FILESYSTEM + his pick on the IPv6 line, then backport whatever's kept.

### 2026-06-29 - Lucas-directed: MEMORY / INTERNET / IPv4 - DONE + BACKPORTED

Worked live with Lucas this morning (approved each step). Final state below;
all **backported to create_config.py / conky_tpl / ethconf** and verified by
throwaway regen + diff (regenerated `conky.text` is byte-identical to live).
"Looks great!" - locked in. Final overlay: `docs/baseline/2026-06-29_full_final.png`.

- **MEMORY - label up + block top-anchored.** The fix that beat last night's
  crowding: move the whole block up via the heading (rows follow), THEN nudge
  SWAP/RAM to the ring bottom. Net gen values: heading `voffset 77 -> 42`,
  SWAP `voffset 8 -> 20` (RAM voffset 1 unchanged). create_config.py 657/671
  (+ old variants 655/669: 97->62, 14->26).
- **FILESYSTEM - kept the top-align** (Lucas happy). Net gen `voffset -81 -> -76`
  (the -99 from last night, then +35 to hold under MEMORY's rise, then -12 under
  the SWAP nudge = -76). create_config.py 428 (-81->-76) + old 426 (-80->-75).
- **INTERNET - Up/Down matched to the ring BOTTOM.** Moved the whole block; net
  gen heading `voffset 26 -> 38`. Source: conky_tpl line 88 (the heading is in the
  template, NOT ethconf - ethconf starts at "Interface"). CLOCK held via TIME
  `voffset -50 -> -44` (create_config.py 789 + old 787 -40->-34).
- **Public IP IPv6 overflow FIXED** - forced IPv4: `curl -s -> curl -s -4` in
  `ethconf` line 5. Now shows e.g. 203.0.113.10, fits the window.

**Backport verification (reusable):** `cp` repo to a scratch dir, run
`python3 create_config.py` there (no --old = the live variant), then
`diff` the scratch `conky_gen.conkyrc` conky.text section vs the live one. It came
back IDENTICAL -> backport correct AND no un-backported drift remains. ruff clean.

**Section status now:** CPU ok / IO WAIT done / MEMORY done / FILESYSTEM done /
INTERNET done / CLOCK ok / OS ok. The alignment task is essentially complete.
