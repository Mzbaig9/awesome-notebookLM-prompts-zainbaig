# The Ihsan Series, cover wraps

`pdf/` holds one print-ready full wrap per book (back, spine, front) at 6x9 trim with 0.125in bleed.
`preview/*-wrap.png` shows trim and spine guides in magenta; `preview/*-front.png` is the front only.

Spine width is page count × 0.002252in (white paper). Every book currently uses a 250-page placeholder
(0.563in spine). Set real counts in `PAGES` at the top of `build.js`, then run `node build.js`.

Back-cover blurbs and hooks are drafts. The barcode box is a placeholder for the ISBN barcode.
`classic/` holds the earlier emerald-and-gold front-only design.

`art/book-N.jpg` are the painted circle illustrations, cropped from the supplied 2048px set to remove the blurred
side padding. `ART_FIT` in `build.js` sets how each portrait painting sits in the circle (width share, focal point).
