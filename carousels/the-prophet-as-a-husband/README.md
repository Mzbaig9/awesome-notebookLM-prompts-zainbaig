# The Prophet as a Husband, Instagram carousel

Ten slide carousel built from the transcript of the bayan "The Prophet as a Husband".

- carousel.html is the source, one section per slide.
- fonts/ holds Cormorant Garamond, Inter and Amiri so it renders offline.
- render.mjs screenshots each slide to export/slide-NN.png at 2x.
- pdf.mjs writes export/the-prophet-as-a-husband-carousel.pdf.
- caption.md has the post caption and hashtags.

Render with `node render.mjs carousel.html export` then `node pdf.mjs` from this folder. Both scripts use the Playwright Chromium already installed in the session environment.
