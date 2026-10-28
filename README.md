# bfport-releases

Ready-to-run builds of **[OpenBF](https://github.com/sprucey149/openbf)** for Linux handhelds. OpenBF is an open-source engine that plays the PS2 versions of *Star Wars: Battlefront* (2004) and *Star Wars: Battlefront II* (2005).

These builds are tuned for small ARM devices: the framebuffer display path, lower 3D resolution, the bots' AI spread over several cores, and a memory-capped sound cache. Tested on an **Anbernic RG35XX-H running Knulli** (Allwinner H700, Mali-G31, 1 GB RAM), at about 30–35 fps in Conquest battles. Other aarch64 Linux handhelds with a Mali GPU and glibc 2.30 or newer should work too.

**Unofficial fan project.** Not affiliated with or endorsed by Lucasfilm, Disney, Electronic Arts, LucasArts or Pandemic Studios.

**No game data is included.** You need your own PS2 discs of both games (NTSC-U: SLUS-20898 and SLUS-21240) and a PC to turn them into the data file once. Never upload or share that file.

## What is in a release
| File | What it is |
|---|---|
| `openbf-handheld-<version>.zip` | Everything for the SD card except your data file: `ports/openbf.sh`, `ports/openbf/openbf-aarch64`, `lib/`, a controller layout and the README |
| `openbf-aarch64` | The game binary alone |
| `openbf.sh` | The launcher alone |
| `manifest.json` | The version, the OpenBF upstream commit it is built on, and the **bake id** of the data it reads |

Releases are named `YYYYMMDD-<commit>`. Each is built automatically from the handheld branch, which tracks OpenBF upstream.

## 1. Bake your data (PC, once per data change)
The data file is made on a PC (Windows or Linux) from your disc images. It takes a while the first time.

**Requirements**
- Python 3, Git, ffmpeg on your `PATH`, and Rust (https://rustup.rs)
- Windows: the Visual Studio C++ Build Tools (rustup offers them) and Git for Windows (the bake runs in its bash)
- Linux: the ALSA and udev development libraries (Debian/Ubuntu: `libasound2-dev libudev-dev`)

**Steps**
1. Get the OpenBF source at the release's upstream commit (the `upstream_commit` in its `manifest.json`):
   ```
   git clone https://github.com/sprucey149/openbf.git
   cd openbf
   git checkout <upstream_commit>
   ```
2. Copy this repo's two `tools/` scripts (`pack-handheld.py`, `bake_id.py`) into `openbf/scripts/handheld/`.
3. Put your disc images in `openbf/iso/` as `SWBF1.iso` and `SWBF2.iso` (or pass `--iso1 <path> --iso2 <path>` in the next step).
4. Bake: `python scripts/pack.py`. It extracts the discs, bakes the assets and writes `dist/openbf(.exe)`.
5. Pack for the handheld: `python scripts/handheld/pack-handheld.py`. It writes two files:
   - `builds/openbf/openbf.pak`: the game data, about 3.5 GB
   - `builds/openbf/openbf.pak.bake`: its bake id, which the updater checks

To check whether a release reads your pack, compare `openbf.pak.bake` with the release's `bake_id`; equal means compatible. Later releases usually keep the same bake id. A new one is only needed when OpenBF changes how the data is made, and the handheld tells you when that happens (see Updates).

## 2. Install (SD card)
1. Unzip `openbf-handheld-<version>.zip` into the root of your ROMs folder, so its `ports/` merges with yours. On Knulli that is `/userdata/roms/` (the `ports/` folder appears as Ports).
2. Copy `openbf.pak` and `openbf.pak.bake` from step 1 into `ports/openbf/`.
3. **RG35XX-H only:** in `ports/openbf/`, rename `pad-rg35xxh.txt` to `pad.txt`. That is the tested button layout. On other devices, leave it out, and the firmware's own controller mapping is used.
4. Refresh the game list in your firmware's menu and start **openbf** from Ports.

The card should end up like this:
```
ports/openbf.sh
ports/openbf/openbf-aarch64
ports/openbf/lib/
ports/openbf/openbf.pak
ports/openbf/openbf.pak.bake
ports/openbf/pad.txt          (RG35XX-H)
```
The first start takes a little longer. The game keeps its profile, logs and settings in `ports/openbf/openbf_data/`.

## Controls
The game plays like the PS2 versions, with their aim assist. Button names below are the RG35XX-H's, with the PS2 equivalent in brackets.

**In battle**
| Action | Button |
|---|---|
| Move / look and aim | Left stick / right stick |
| Fire / secondary fire | R2 / L2 |
| Jump | B (×) |
| Crouch, prone, roll | A (○) |
| Reload | Y (□) |
| Use: enter or leave a vehicle | X (△) |
| Sprint / zoom | L3 / R3 (stick clicks) |
| Next weapon / switch secondary weapon | R1 / L1 |
| Squad orders | D-pad: up move out, down hold, left at ease, right follow |
| Pause menu | Start |

**Spawn screen:** D-pad picks a command post, R1 / Select picks the class, B spawns, X goes back.

**Menus:** D-pad or left stick to move, B to accept, A to go back (X too on the main menu). To quit, choose Quit from the main menu or the pause menu.

Vehicles: in a hover tank, speeder or flyer the right stick steers; in a walker it aims; in a turret or gunner's seat it turns the gun.

## Updates
When the handheld is online, the launcher checks this repo for a newer build at each start (5 s at most; skipped entirely when offline). The result shows on the main menu:
- **A line at the bottom left that fades after a few seconds:** up to date, offline, updated, a download that will retry next start.
- **A window that stays until you press Select,** only when you need to act:
  - **"An update needs a new data pack":** that build reads a different bake id from yours. Redo step 1 with the new release's upstream commit and copy both files over. Until then, your current build keeps running. The window shows once per build; later starts show a fading line instead.
  - **"The new build failed to start":** the previous build was put back, and that build is skipped.

What the updater does:
- It downloads the binary, checks its sha256, keeps the old binary as `openbf-aarch64.prev`, and swaps in the new one.
- A new launcher replaces `openbf.sh` after the game exits.
- Every step is written to `ports/openbf/openbf_data/update.log`.

To turn the check off, put `OPENBF_UPDATE=off` in `ports/openbf/launch.env`.

## Settings (optional)
`ports/openbf/launch.env` takes one `KEY=VALUE` per line:

| Setting | Effect |
|---|---|
| `OPENBF_RENDER_SCALE=0.6` | 3D resolution, 0.25–1 (default 0.7; the HUD and menus stay sharp) |
| `OPENBF_QUALITY=full` | OpenBF's full quality: grass, specular, point lights and glow (slower) |
| `OPENBF_Q_DISTANCE=150` | don't draw static props farther than 150 m |
| `OPENBF_AI_THREADS=1` | the bots' thinking on one core (default 3) |
| `OPENBF_GOVERNOR=0` | leave the CPU and GPU clocks as the firmware set them (by default the launcher runs them at full speed while you play) |
| `OPENBF_UPDATE=off` | no update check |
| `OPENBF_FRAME_PROFILE=openbf_data/frames.csv` | a per-frame timing file, for performance reports |

## Troubleshooting
- **Logs:** `ports/openbf/openbf_data/launch.log` (each start: the device, display, controller and frame rate), `update.log` (updates).
- **Buttons are wrong:** on an RG35XX-H, make sure `pad.txt` is there. On another device, `launch.log` lists each button's name and code as you press it, which is enough to write a `pad.txt`: one SDL GameController mapping line.
- **It quits while loading a big map:** check `launch.log` for exit 137 (out of memory). Close anything else that runs in the background and try again.

## License
MIT, as OpenBF. The builds contain code only.
