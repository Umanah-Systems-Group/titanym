# Titanym — SiGe-on-Sapphire Process Qualification Website

## Project Overview

**Titanym** is a static marketing/program website for a Umanah Systems Group technical program focused on reproducing and qualifying a SiGe-on-sapphire semiconductor growth process for future extreme-environment electronics.

The site is designed to feel technical, restrained, institutional, and credible — aligned with a technical program review document rather than a venture/startup landing page.

---

## Completed Features

- ✅ Full single-page website with 6 distinct sections
- ✅ Fixed-width boxed layout (max-width 1080px)
- ✅ Deep navy hero with DM Serif Display wordmark in muted orange
- ✅ Scroll-triggered reveal animations on all content blocks
- ✅ Sticky header with scroll-spy active nav highlighting
- ✅ Mobile hamburger menu with animated icon
- ✅ Smooth scroll navigation
- ✅ Staggered card entrance animations (stat, scope, qual, exec grids)
- ✅ Animated SVG gauge needle (Go / No-Go) triggered by IntersectionObserver
- ✅ Hero grid parallax effect
- ✅ Scroll indicator bouncing animation
- ✅ Full responsive layout (1080px / 900px / 640px / 420px breakpoints)
- ✅ All SEO meta tags, Open Graph, and Twitter Card meta
- ✅ Three images integrated: titanym1.jpg (hero banner), titanym3.jpg (post-qualification), titanym2 content referenced in qual cards
- ✅ Institutional color scheme: 70% off-white/cream, 20% navy/blue, 10% muted orange

---

## File Structure

```
index.html              — Main self-contained page (CSS + JS inline)
css/
  ├── style.css         — Full design system stylesheet
  └── enhancements.css  — Micro-detail CSS enhancements
js/
  └── main.js           — Scroll, reveal, navigation JS
images/
  ├── titanym1.jpg      — Hero banner / social preview image
  ├── titanym2.jpg      — Qualification framework reference
  └── titanym3.jpg      — Post-qualification path banner
README.md
```

---

## Entry Points

| Path | Description |
|------|-------------|
| `index.html` | Main page (self-contained) |
| `#hero` | Hero section |
| `#program` | Program overview |
| `#phase1` | Phase 1 scope |
| `#qualification` | Qualification path |
| `#qual-detail` | Measurement framework |
| `#execution` | Execution section |
| `#contact` | Contact / CTA |

---

## Color Palette

| Role | Hex |
|------|-----|
| Deep navy (header/footer) | `#0B2847` |
| Mid blue | `#2D5D86` |
| Slate blue | `#6E8FAE` |
| Soft powder blue | `#DCE8F2` |
| Warm sand | `#EAD9B0` |
| Light cream | `#F5EEDC` |
| Muted orange accent | `#D97A4A` |
| Off-white background | `#F7F7F5` |
| Dark text | `#1D2A3A` |

---

## Not Yet Implemented

- Contact form with backend submission
- Multi-page routing (Program Detail, About, etc.)
- Blog / technical updates section
- Document/PDF downloads

---

## Recommended Next Steps

1. Replace `mailto:contact@titanym.com` with a real contact endpoint or form
2. Add `titanym-preview.jpg` at site root for exact OG/Twitter preview image
3. Set real canonical URL in meta tags (replace `https://titanym.com`)
4. Add a favicon (`/favicon.ico` or SVG)
5. Consider a Phase 2 / Roadmap section as the program progresses

---

*Titanym — A Umanah Systems Group Program*
