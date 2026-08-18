# Blender Tools

Twelve small Blender add-ons for hard-surface and game asset work. MIT, one
`.py` file each, no dependencies.

**Site:** https://tristanmuzzu.github.io/blender-tools/

## Why this is one big repo

I'm applying to sell an add-on on a marketplace and they want a portfolio
link, so I put my Blender tools in one place, tidied them up and wrote a test
suite that actually runs them. That's why the whole lot lands in a single
commit rather than trickling in over months. Nothing clever going on, it's
just what happens when you finally organise things.

## Install

Grab any `.py` from [`addons/`](addons/). In Blender:
**Edit → Preferences → Add-ons → Install**, pick the file, tick it on.
Panels show up in the viewport sidebar (press <kbd>N</kbd>) under **BTools**.

## The tools

| Add-on | What it does |
|---|---|
| [Asset Check](addons/bt_asset_check.py) | Checks transforms, scale, manifold geometry and UVs before export, and fixes the mechanical stuff |
| [Surface Scatter](addons/bt_surface_scatter.py) | Scatters instances over a surface, weighted by face area, with a slope limit |
| [Quick Export](addons/bt_quick_export.py) | glTF or FBX with Unity and Unreal axes already right |
| [Mesh Stats](addons/bt_mesh_stats.py) | Live triangle, n-gon, loose vertex and manifold counts |
| [Auto Frame](addons/bt_auto_frame.py) | Puts the camera where your selection fills the frame |
| [Seam by Angle](addons/bt_seam_by_angle.py) | Marks seams on sharp edges, then unwraps |
| [Turntable](addons/bt_turntable.py) | Orbit animation in one click, no stutter on the loop |
| [Origin Tools](addons/bt_origin_tools.py) | Origin to bottom, centre or world zero, plus drop to floor |
| [Batch Rename](addons/bt_batch_rename.py) | Pattern renaming with numbering, find and replace |
| [Material Slots](addons/bt_material_slots.py) | Drops unused slots, repoints `.001` duplicates |
| [Collection Sort](addons/bt_collection_sort.py) | Sorts into collections by type, prefix or material |
| [Align & Distribute](addons/bt_align_distribute.py) | Align on any axis, space things evenly |

## Blender versions

Tested on **3.6 LTS, 4.2 LTS, 4.5 LTS, 5.0 and 5.2**.

```bash
blender --background --factory-startup --python test_all.py
```

`test_all.py` installs each add-on, enables it, runs its operators against
real geometry and unloads it again. Twelve tools across five versions is sixty
combinations. Checking that something registers isn't worth much on its own,
since an add-on that registers and then throws the first time you click it is
worse than one that won't install at all.

It's caught real things. The turntable worked on 3.6 and 4.2 and threw on 5.x,
because `Action.fcurves` stopped existing when Blender moved Actions over to
layers and slots in 4.4.

## The paid one

These twelve are free and stay free. The thing I sell is
**[PanelForge](https://tristaneer2.gumroad.com/l/panelforge?src=freetools-readme)**.
It panels and greebles a hull procedurally, so you get plating, vents and fins
laid out over a mesh instead of modelling each one. $24, same five Blender
versions, same test suite.

Every add-on above has a link to it at the bottom of its sidebar panel. That's
the only string attached, and if you never click it the tools work exactly the
same.

## Licence

MIT. Do what you like with them.
