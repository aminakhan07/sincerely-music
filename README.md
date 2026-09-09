# Sincerely, Music

A dreamy, vinyl-inspired Spotify companion for Windows.

Sincerely, Music mirrors the song currently playing in your Spotify desktop app. The album artwork becomes the vinyl label, the record spins while the song plays, and the controls let you interact with Spotify directly from the companion window.

## Features

- 🎵 Syncs with the song currently playing on Spotify
- 💿 Album artwork displayed as the vinyl label
- ✦ Vinyl animation while music is playing
- ⏮ Previous track
- ▶ Play / pause
- ⏭ Next track
- 🎚 Seek through the current song
- 📝 Save notes for songs
- 🎨 Album-based mood colors
- 🔐 Spotify login with persistent authentication
- 🖥️ Runs as a Windows desktop app
- 🌸 Custom Sincerely, Music interface

## Tech Stack

- **HTML** — player interface in `templates/player.html`
- **CSS** — visual design in `static/css/`
- **JavaScript** — Spotify sync and player controls in `static/js/player.js`
- **Python / Flask** — Spotify OAuth, API routes, and application logic in `app.py`
- **SQLite** — local storage for song notes
- **pywebview** — desktop application window

## Running the App

### 1. Set up Spotify

Create an application in the Spotify Developer Dashboard.

Add this Redirect URI to your Spotify app:

`http://127.0.0.1:5000/callback`

### 2. Configure environment variables

Create a `.env` file in the project folder containing your Spotify Client ID and Client Secret.

Never commit your `.env` file.

### 3. Install dependencies

Create and activate a virtual environment:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```
