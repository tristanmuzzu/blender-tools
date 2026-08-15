# Blender Tools

Twelve small Blender add-ons for hard-surface modelling and game asset work.
Each is a single `.py` file. MIT licensed.

**Site:** https://tristanmuzzu.github.io/blender-tools/

## Install

Download any `.py` from [`addons/`](addons/), then in Blender:
**Edit → Preferences → Add-ons → Install**, pick the file, tick it on.
The panels appear in the 3D viewport sidebar (press <kbd>N</kbd>) under **BTools**.

## The tools

| Add-on | What it does |
|---|---|
| [Asset Check](addons/bt_asset_check.py) | Pre-export validation — transforms, scale, manifold geometry, UVs — plus a mechanical auto-fix |
| [Surface Scatter](addons/bt_surface_scatter.py) | Area-weighted scatter across a surface with slope limits and per-instance jitter |
| [Quick Export](addons/bt_quick_export.py) | glTF or FBX with Unity and Unreal axis presets, optionally one file per object |
| [Mesh Stats](addons/bt_mesh_stats.py) | Live triangle, n-gon, loose vertex and manifold readout |
| [Auto Frame](addons/bt_auto_frame.py) | Fits the camera to a selection by projecting real vertices |
| [Seam by Angle](addons/bt_seam_by_angle.py) | Marks UV seams on sharp edges, then unwraps |
| [Turntable](addons/bt_turntable.py) | One-click orbit animation on a reusable pivot |
| [Origin Tools](addons/bt_origin_tools.py) | Origin to bottom, centre or world zero, and drop to floor |
| [Batch Rename](addons/bt_batch_rename.py) | Pattern renaming with numbering, plus find and replace |
| [Material Slots](addons/bt_material_slots.py) | Removes unused slots, repoints `.001` duplicates |
| [Collection Sort](addons/bt_collection_sort.py) | Groups objects by type, name prefix or first material |
| [Align & Distribute](addons/bt_align_distribute.py) | Aligns on any axis, spaces objects evenly |

## Blender support

Tested on **3.6 LTS, 4.2 LTS, 4.5 LTS, 5.0 and 5.2**.

`test_all.py` installs each add-on, enables it, runs its operators against real
geometry, and unloads it again — 12 tools x 5 versions = 60 combinations.
Registration alone is not a useful test; an add-on that registers and then
throws on first click is worse than one that fails to install.

```bash
blender --background --factory-startup --python test_all.py
```

This is not busywork. The turntable tool worked on 3.6 and 4.2 and threw on
5.x, because `Action.fcurves` stopped existing when Blender restructured
Actions into layers and slots in 4.4.
