const el = (id) => document.querySelector(id);

const record = el('#record');
const art = el('#art');
const title = el('#title');
const artist = el('#artist');
const previous = el('#previous');
const play = el('#play');
const next = el('#next');
const loop = el('#loop');
const seek = el('#seek');
const time = el('#time');
const status = el('#status');
const login = el('#login');
let current = null, duration = 0, dragging = false, previousArtwork = '';
const clock = (milliseconds) => `${Math.floor(milliseconds / 60000)}:${String(Math.floor(milliseconds / 1000) % 60).padStart(2, '0')}`;
async function setAlbumMood(artwork) {
  if (!artwork || artwork === previousArtwork) return;
  previousArtwork = artwork;
  try {
    const palette = await fetch(`/api/mood?artwork=${encodeURIComponent(artwork)}`).then((response) => response.json());
    const root = document.documentElement.style;
    root.setProperty('--mood-a', palette.primary); root.setProperty('--mood-b', palette.secondary); root.setProperty('--mood-deep', palette.secondary); root.setProperty('--mood-light', palette.light);
  } catch { /* keep default pink */ }
}
async function update() {
  try {
    const response = await fetch('/api/spotify/current');
    const data = await response.json();

    if (response.status === 401) {
      status.textContent = 'Link Spotify to mirror your laptop player.';
      return;
    }

    if (!response.ok) {
      throw new Error(data.error);
    }

    if (!data.track) {
      record.classList.remove('spinning');
      play.disabled = true;
      seek.disabled = true;
      status.textContent = 'Open Spotify on your laptop and play a song.';
      return;
    }

    current = data;
    duration = data.duration_ms;

    title.textContent = data.track.title;
    artist.textContent = `${data.track.artist} · ${data.track.album}`;
    art.src = data.track.artwork;

    setAlbumMood(data.track.artwork);

    record.classList.toggle('spinning', data.playing);
    play.textContent = data.playing ? 'Ⅱ' : '▶';

    previous.disabled = false;
    play.disabled = false;
    next.disabled = false;
    loop.disabled = false;
    seek.disabled = false;

    const progress = duration
      ? (data.progress_ms / duration) * 100
      : 0;

    if (!dragging) {
      seek.value = progress;
    }

    seek.style.setProperty('--progress', `${progress}%`);

    time.textContent = clock(data.progress_ms);

    status.textContent = data.playing
      ? 'synced with Spotify on your laptop ♡'
      : 'Spotify is paused on your laptop';

  } catch (error) {
    console.error(error);
    status.textContent = 'Open Spotify on your laptop, then refresh this window.';
  }
}
async function control(payload) { await fetch('/api/spotify/control', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) }); setTimeout(update, 500); }
play.onclick = () => current && control({ action: 'toggle', playing: current.playing });
previous.onclick = () => current && control({ action: 'previous' });
next.onclick = () => current && control({ action: 'next' });
let loopEnabled = false;

loop.onclick = async () => {
    if (!current) return;

    loopEnabled = !loopEnabled;
    loop.classList.toggle('active', loopEnabled);

    await control({ action: 'loop', enabled: loopEnabled });
};seek.oninput = () => { dragging = true; time.textContent = clock(duration * seek.value / 100); };
seek.onchange = () => { dragging = false; control({ action: 'seek', position_ms: Math.round(duration * seek.value / 100) }); };
async function init() {
  const session = await fetch('/api/spotify/session').then((response) => response.json());
  if (!session.client_configured) { status.textContent = 'Add your Spotify app details to .env first.'; return; }
  if (session.authenticated) { login.textContent = 'spotify linked'; login.href = '/logout'; update(); setInterval(update, 3500); }
}
init();
