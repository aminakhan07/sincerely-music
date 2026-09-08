# Pink Petal Records

A pink, vinyl-inspired Spotify companion. It mirrors the song currently playing in your Spotify laptop app: album art becomes the vinyl label, the vinyl spins while it plays, and the controls act on Spotify's active device.

## Stack

- **HTML**: mini player template in `templates/companion.html`
- **CSS**: mini player visual design in `static/css/companion.css`
- **JavaScript**: Spotify sync, controls, and notes UI in `static/js/companion.js`
- **Python / Flask**: Spotify OAuth, Spotify API routes, and SQLite persistence in `app.py`

## Run it in VS Code

1. Open this folder in Visual Studio Code.
2. Create a Spotify app in the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard). In its settings add this Redirect URI exactly: `http://127.0.0.1:5000/callback`.
3. Duplicate `.env.example` as `.env`, then paste your Spotify Client ID and Client Secret. Never commit `.env`.
4. Open its terminal and create a virtual environment:
   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```
5. Start the app:
   ```powershell
   python app.py
   ```
6. Open Spotify on your laptop and play any song. Visit `http://127.0.0.1:5000`, choose **link spotify**, then approve the login. The mini player will now follow the music playing in Spotify.

## APIs

- `GET /login` and `GET /callback`: secure Spotify OAuth login. Your secret stays in Python, never JavaScript.
- `GET /api/spotify/current`: reads the track and play state from your active Spotify device.
- `POST /api/spotify/control`: pauses, resumes, or seeks in your active Spotify device.
- `GET /api/notes`: returns saved notes.
- `POST /api/notes`: stores a note with the currently selected song in SQLite.

Spotify Premium is required for Spotify's playback-control endpoints. New developer-mode apps work for the app owner and up to five allowlisted testers, which is perfect for a personal portfolio project.

## Push to GitHub

Create an empty repository on GitHub, then use the VS Code terminal in this project folder:

```powershell
git init
git add .
git commit -m "Build Pink Petal Records"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/pink-petal-records.git
git push -u origin main
```

`pink_petal.db` is intentionally ignored: it is generated locally when you first run the app.
