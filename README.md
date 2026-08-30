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

## Write-ups

Longer notes live on the site above. They're about things that bit me while
building this lot, with the numbers I measured rather than general advice.

- What broke between Blender 3.6 and 5.2: `Action.fcurves` disappearing in 4.4,
  FBX export behaving differently on 5.0.1, and what a five-version test matrix
  actually catches.
- Sixteen sliders, and what each one actually does. A parameter sweep of a
  generator, written while documenting it, which is how I found that one of my
  own sliders had three behaviours and twelve labels.
- Changing a generator without moving everybody's meshes: hashing vertices
  instead of counting them, keeping a seeded random stream stable through a
  refactor, and picking a new default so the old one lands on the same code
  path.

## The paid ones

These twelve are free and stay free. Three things in here aren't, and all three
run on the same seven Blender versions as the twelve above.

**[PanelForge](https://tristaneer2.gumroad.com/l/panelforge?src=freetools-readme)**
panels and greebles a hull procedurally. You get plating, vents and fins laid
out over a mesh instead of modelling each one. $24, same seven Blender
versions, same test suite.

**[WearForge](https://tristaneer2.gumroad.com/l/wearforge?src=freetools-readme)**
chips and chamfers the hard edges of a model you already have. The chamfer
width changes along the edge, most of the edge is left crisp, and the bites go
where a part actually gets handled rather than everywhere. It writes a `wear`
point attribute so you can drive a mask off it. $14.
Two catches, up front. It changes a close shot and it does not change a
thumbnail, which is measured rather than a guess. And on 3.6 and 4.2 the same
seed gives the same counts but not quite the same vertex positions, median
1.24 mm on a 2 m part, because Blender's own bevel changed at 4.5.

**[Sci-Fi Corridor Kit](https://tristaneer2.gumroad.com/l/scifi-corridor-kit?src=freetools-readme)**
is six modules that tile on a 4 metre grid: a straight, a 90 degree corner, a T
junction, a four way crossroads, a dead end, and a bulkhead doorway you
walk through. .blend and .glb, and the Python that generated the lot is in the
zip, so you can change a number and rebuild rather than edit meshes. $19.
One catch, up front. There are no textures and no PBR maps, just four
material slots per piece with the faces already assigned, which is the part
that takes an afternoon of box-selecting if you do it by hand.

Every add-on above has a link to PanelForge at the bottom of its sidebar panel.
That's the only string attached, and if you never click it the tools work
exactly the same.

## Licence

MIT. Do what you like with them.
