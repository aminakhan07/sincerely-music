const audio = document.querySelector('#audio');
const record = document.querySelector('#record');
const turntable = document.querySelector('#turntable');
const playButton = document.querySelector('#playButton');
const restartButton = document.querySelector('#restartButton');
const songTitle = document.querySelector('#songTitle');
const songArtist = document.querySelector('#songArtist');
const recordLabel = document.querySelector('#recordLabel span');
const searchForm = document.querySelector('#searchForm');
const searchInput = document.querySelector('#searchInput');
const results = document.querySelector('#results');
const status = document.querySelector('#searchStatus');
const noteInput = document.querySelector('#noteInput');
const counter = document.querySelector('#counter');
const saveNoteButton = document.querySelector('#saveNoteButton');
const notesList = document.querySelector('#notesList');
let selectedTrack = null;

function setPlayerState(isPlaying) {
  record.classList.toggle('spinning', isPlaying);
  turntable.classList.toggle('playing', isPlaying);
  playButton.textContent = isPlaying ? 'Ⅱ' : '▶';
  playButton.setAttribute('aria-label', isPlaying ? 'Pause song preview' : 'Play song preview');
}

function chooseTrack(track) {
  selectedTrack = track;
  audio.src = track.preview_url;
  songTitle.textContent = track.title;
  songArtist.textContent = `${track.artist} · ${track.album}`;
  recordLabel.innerHTML = `${track.title.split(' ').slice(0, 3).join('<br>')}<i></i>`;
  record.style.setProperty('--cover', `url("${track.artwork}")`);
  playButton.disabled = false;
  restartButton.disabled = false;
  document.querySelectorAll('.track-result').forEach((item) => item.classList.toggle('selected', item.dataset.id === String(track.id)));
  audio.play().catch(() => setPlayerState(false));
}

async function searchMusic(query) {
  status.textContent = 'Looking through the record crate…';
  results.replaceChildren();
  try {
    const response = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
    const data = await response.json();
    if (!response.ok) throw new Error(data.error);
    if (!data.tracks.length) { status.textContent = 'No previews found — try a different artist or song.'; return; }
    status.textContent = `Found ${data.tracks.length} little treasures.`;
    data.tracks.forEach((track) => {
      const button = document.createElement('button');
      button.className = 'track-result'; button.dataset.id = track.id;
      button.innerHTML = `<img src="${track.artwork}" alt=""><span><b>${track.title}</b><small>${track.artist}</small></span><strong>play</strong>`;
      button.addEventListener('click', () => chooseTrack(track));
      results.append(button);
    });
  } catch (error) { status.textContent = error.message || 'Something went wrong. Please try again.'; }
}

searchForm.addEventListener('submit', (event) => { event.preventDefault(); searchMusic(searchInput.value.trim()); });
playButton.addEventListener('click', () => audio.paused ? audio.play() : audio.pause());
restartButton.addEventListener('click', () => { audio.currentTime = 0; audio.play(); });
audio.addEventListener('play', () => setPlayerState(true));
audio.addEventListener('pause', () => setPlayerState(false));
audio.addEventListener('ended', () => setPlayerState(false));
audio.addEventListener('error', () => { status.textContent = 'That preview could not load. Please choose another track.'; setPlayerState(false); });

function updateCounter() { counter.textContent = `${noteInput.value.length} / 500`; }
function formatDate(isoDate) { return new Intl.DateTimeFormat(undefined, { month: 'short', day: 'numeric' }).format(new Date(isoDate)); }
function renderNote(note, prepend = false) {
  const item = document.createElement('article'); item.className = 'saved-note';
  item.innerHTML = `<p></p><footer>${note.track_name ? `♪ ${note.track_name} — ${note.artist_name}` : 'a little thought'} <time>${formatDate(note.created_at)}</time></footer>`;
  item.querySelector('p').textContent = note.body;
  prepend ? notesList.prepend(item) : notesList.append(item);
}
async function loadNotes() {
  const response = await fetch('/api/notes'); const data = await response.json();
  data.notes.forEach((note) => renderNote(note));
}
noteInput.addEventListener('input', updateCounter);
saveNoteButton.addEventListener('click', async () => {
  const body = noteInput.value.trim(); if (!body) { noteInput.focus(); return; }
  saveNoteButton.disabled = true;
  try {
    const response = await fetch('/api/notes', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ body, track_name: selectedTrack?.title || '', artist_name: selectedTrack?.artist || '' }) });
    const data = await response.json(); if (!response.ok) throw new Error(data.error);
    renderNote(data.note, true); noteInput.value = ''; updateCounter(); saveNoteButton.textContent = 'saved! ♡';
    setTimeout(() => saveNoteButton.textContent = 'save note ♡', 1200);
  } catch (error) { status.textContent = error.message || 'Your note could not be saved.'; }
  finally { saveNoteButton.disabled = false; }
});
updateCounter(); loadNotes(); searchMusic('Laufey');
