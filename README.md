# Titanym website

Static marketing site for Titanym Inc., which is developing a two-sided sapphire semiconductor platform that integrates III-nitride RF and SiGe electronics for defense, space and telecommunications.

## Files

```
index.html          the page
css/site.css        styles (brand tokens at the top)
js/site.js          3D wafer builder, hero signal field, before/after diagram, pinned scroll cutaway, entrances, contact form
js/wafer-gl.js      three.js viewer for the Blender wafer: drag to spin 360°, scroll cutaway (falls back to the CSS wafer without WebGL)
js/vendor/          three.js r170 (MIT) and the GLTF loader, served locally
images/             Awardable badges, favicon, social card, titanym-wafer.glb (the 3D model)
blender/            scripts that build the 3D model in Blender
```

No build step. Vercel serves the repository root as-is.

All illustrations are drawn in code (Blender model, inline SVG scenes, canvas field). No pitch-deck artwork is used.

## 3D wafer model

`images/titanym-wafer.glb` is built in Blender from `blender/`. With the `bpy` package (Blender as a Python module, Python 3.13):

```
pip install bpy
python blender/textures.py /tmp/tex             # draws the wafer face textures
python blender/build_chip.py /tmp/tex /tmp/out  # models the wafer, exports the .glb, renders a still, saves the .blend
cp /tmp/out/titanym-wafer.glb images/
```

The model has named nodes `RF`, `Sapphire`, `SiGe` and `Vias`; `js/wafer-gl.js` moves them apart for the exploded views.

## Contact form

The form posts to Formspree (`https://formspree.io/f/xeelnkqj`), form id `contact-form`, fields `name`, `organization`, `type`, `email`, `message`. Success is shown only after Formspree returns an OK response.

## Content rules

- Show the DARPA ERIS and CDAO Tradewinds statuses as "Assessed as Awardable", with the disclaimer that this is not a contract, funding commitment, endorsement, or guarantee of an award.
- Use the official Tradewinds badge files as supplied, never recoloured. Never use the DARPA logo.
- Do not publish team, financing, roadmap, patent or licensing details, or performance figures that are not backed by qualification data.

## History

The previous site is preserved on the `legacy-site` branch.
