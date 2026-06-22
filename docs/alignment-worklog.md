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
