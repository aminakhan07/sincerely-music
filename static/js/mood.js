// Recolour the player with a small palette extracted from each album cover.
const cover = document.querySelector('#art');
let lastArtwork = '';

cover.addEventListener('load', async () => {
  if (!cover.src || cover.src === lastArtwork) return;
  lastArtwork = cover.src;
  try {
    const response = await fetch(`/api/mood?artwork=${encodeURIComponent(cover.src)}`);
    const palette = await response.json();
    const root = document.documentElement.style;
    root.setProperty('--mood-a', palette.primary);
    root.setProperty('--mood-b', palette.secondary);
    root.setProperty('--mood-deep', palette.secondary);
    root.setProperty('--mood-light', palette.light);
  } catch {
    // Keep the default pink palette if artwork colour extraction is unavailable.
  }
});



