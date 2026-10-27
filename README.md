# Titanym website

Static marketing site for Titanym Inc., which is developing a two-sided sapphire semiconductor platform that integrates III-nitride RF and SiGe electronics for defense, space and telecommunications.

## Files

```
index.html          the page
css/site.css        styles (brand tokens at the top)
js/site.js          header colour by section, entrances, wafer cutaway tabs, applications list, contact form
images/             deck artwork crops, Awardable badges, favicon, social card
```

No build step. Vercel serves the repository root as-is.

## Contact form

The form posts to Formspree (`https://formspree.io/f/xeelnkqj`), form id `contact-form`, fields `name`, `organization`, `type`, `email`, `message`. Success is shown only after Formspree returns an OK response.

## Content rules

- Show the DARPA ERIS and CDAO Tradewinds statuses as "Assessed as Awardable", with the disclaimer that this is not a contract, funding commitment, endorsement, or guarantee of an award.
- Use the official Tradewinds badge files as supplied, never recoloured. Never use the DARPA logo.
- Do not publish team, financing, roadmap, patent or licensing details, or performance figures that are not backed by qualification data.

## History

The previous site is preserved on the `legacy-site` branch.
