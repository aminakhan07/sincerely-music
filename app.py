"""Pink Petal Records — Flask + Spotify Web API + SQLite notes."""
from __future__ import annotations
import base64, io, json, os, secrets, sqlite3, time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen
from dotenv import load_dotenv
import keyring
from flask import Flask, jsonify, redirect, render_template, request, session, url_for
from PIL import Image

BASE_DIR = Path(__file__).resolve().parent
DATABASE = BASE_DIR / "pink_petal.db"
load_dotenv(BASE_DIR / ".env")
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY")
CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID", "")
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET", "")
REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI", "http://127.0.0.1:5000/callback")
SCOPES = "user-read-currently-playing user-read-playback-state user-modify-playback-state"

KEYRING_SERVICE = "Sincerely Music"
KEYRING_USER = "spotify_refresh_token" 

def db_connection():
    connection = sqlite3.connect(DATABASE); connection.row_factory = sqlite3.Row; return connection
def initialize_database():
    with db_connection() as connection:
        connection.execute("CREATE TABLE IF NOT EXISTS notes (id INTEGER PRIMARY KEY AUTOINCREMENT, body TEXT NOT NULL, track_name TEXT, artist_name TEXT, created_at TEXT NOT NULL)")
def spotify_token_request(payload):
    basic = base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()
    token_request = Request("https://accounts.spotify.com/api/token", data=urlencode(payload).encode(), headers={"Authorization": f"Basic {basic}", "Content-Type": "application/x-www-form-urlencoded"}, method="POST")
    with urlopen(token_request, timeout=10) as response: return json.load(response)
def spotify_request(url, token, method="GET", body=None):
    data = json.dumps(body).encode() if body is not None else None
    headers = {"Authorization": f"Bearer {token}"}
    if data: headers["Content-Type"] = "application/json"
    with urlopen(Request(url, data=data, headers=headers, method=method), timeout=10) as response: return {} if response.status == 204 else json.load(response)
def active_spotify_token():
    token = session.get("spotify_token")

    if token and session.get("spotify_expires_at", 0) > time.time() + 30:
        return token

    refresh_token = session.get("spotify_refresh_token")

    if not refresh_token:
        refresh_token = keyring.get_password(KEYRING_SERVICE, KEYRING_USER)

    if not refresh_token:
        return None

    refreshed = spotify_token_request({
        "grant_type": "refresh_token",
        "refresh_token": refresh_token
    })

    session["spotify_token"] = refreshed["access_token"]
    session["spotify_expires_at"] = time.time() + refreshed.get("expires_in", 3600)

    if refreshed.get("refresh_token"):
        refresh_token = refreshed["refresh_token"]
        keyring.set_password(KEYRING_SERVICE, KEYRING_USER, refresh_token)

    session["spotify_refresh_token"] = refresh_token

    return session["spotify_token"]

@app.get("/")
def index(): return render_template("player.html")
@app.get("/login")
def spotify_login():
    if not CLIENT_ID or not CLIENT_SECRET: return "Add your Spotify Client ID and Client Secret to .env first.", 500
    state = secrets.token_urlsafe(24); session["spotify_state"] = state
    query = urlencode({"response_type": "code", "client_id": CLIENT_ID, "scope": SCOPES, "redirect_uri": REDIRECT_URI, "state": state})
    return redirect(f"https://accounts.spotify.com/authorize?{query}")
@app.get("/callback")
def spotify_callback():
    if request.args.get("state") != session.pop("spotify_state", None):
        return "Spotify login could not be verified. Please try again.", 400

    try:
        tokens = spotify_token_request({
            "grant_type": "authorization_code",
            "code": request.args["code"],
            "redirect_uri": REDIRECT_URI
        })
    except (KeyError, HTTPError, OSError):
        return "Spotify login failed. Check your app's redirect URI and try again.", 400

    session["spotify_token"] = tokens["access_token"]
    session["spotify_expires_at"] = time.time() + tokens.get("expires_in", 3600)

    refresh_token = tokens.get("refresh_token")

    if refresh_token:
        keyring.set_password(KEYRING_SERVICE, KEYRING_USER, refresh_token)
        session["spotify_refresh_token"] = refresh_token

    return redirect(url_for("index"))
@app.get("/logout")
def spotify_logout():
    try:
        keyring.delete_password(KEYRING_SERVICE, KEYRING_USER)
    except keyring.errors.PasswordDeleteError:
        pass

    session.clear()
    return redirect(url_for("index"))
@app.get("/api/spotify/session")
def spotify_session(): return jsonify({"authenticated": bool(active_spotify_token()), "client_configured": bool(CLIENT_ID and CLIENT_SECRET)})
@app.get("/api/search")
def search_music():
    query, token = request.args.get("q", "").strip(), active_spotify_token()
    if len(query) < 2: return jsonify({"error": "Type at least two characters to search."}), 400
    if not token: return jsonify({"error": "Connect Spotify to search its catalogue."}), 401
    try: payload = spotify_request(f"https://api.spotify.com/v1/search?{urlencode({'q': query, 'type': 'track', 'market': 'IN', 'limit': 12})}", token)
    except (HTTPError, OSError): return jsonify({"error": "Spotify search is unavailable right now."}), 503
    tracks = [{"id": x["id"], "uri": x["uri"], "title": x["name"], "artist": ", ".join(a["name"] for a in x["artists"]), "album": x["album"]["name"], "artwork": x["album"].get("images", [{}])[0].get("url", ""), "spotify_url": x["external_urls"]["spotify"]} for x in payload.get("tracks", {}).get("items", [])]
    return jsonify({"tracks": tracks})
@app.get("/api/spotify/current")
def spotify_current():
    token = active_spotify_token()
    if not token: return jsonify({"error": "Connect Spotify first."}), 401
    try: playback = spotify_request("https://api.spotify.com/v1/me/player", token)
    except HTTPError as error:
        if error.code == 204: return jsonify({"playing": False, "track": None})
        return jsonify({"error": "Spotify could not read your current song."}), error.code
    item = playback.get("item") or {}
    if not item: return jsonify({"playing": False, "track": None})
    return jsonify({"playing": playback.get("is_playing", False), "progress_ms": playback.get("progress_ms", 0), "duration_ms": item.get("duration_ms", 0), "track": {"title": item.get("name"), "artist": ", ".join(a.get("name", "") for a in item.get("artists", [])), "album": item.get("album", {}).get("name", ""), "artwork": item.get("album", {}).get("images", [{}])[0].get("url", ""), "spotify_url": item.get("external_urls", {}).get("spotify", "")}})
@app.post("/api/spotify/control")
def spotify_control():
    token, data = active_spotify_token(), request.get_json(silent=True) or {}

    if not token:
        return jsonify({"error": "Connect Spotify first."}), 401

    action = data.get("action")

    try:
        if action == "toggle":
            playing = bool(data.get("playing"))
            spotify_request(
                "https://api.spotify.com/v1/me/player/pause" if playing
                else "https://api.spotify.com/v1/me/player/play",
                token,
                method="PUT"
            )

        elif action == "seek":
            spotify_request(
                f"https://api.spotify.com/v1/me/player/seek?{urlencode({'position_ms': data.get('position_ms', 0)})}",
                token,
                method="PUT"
            )

        elif action == "previous":
            spotify_request(
                "https://api.spotify.com/v1/me/player/previous",
                token,
                method="POST"
            )

        elif action == "next":
            spotify_request(
                "https://api.spotify.com/v1/me/player/next",
                token,
                method="POST"
            )

        else:
            return jsonify({"error": "Unknown Spotify control."}), 400

    except HTTPError as error:
        return jsonify({"error": "Spotify could not control your active device. Open Spotify on your laptop."}), error.code

    return jsonify({"ok": True})
@app.get("/api/mood")
def album_mood():
    """Return a small palette calculated from the current Spotify album artwork."""
    artwork = request.args.get("artwork", "")
    host = urlparse(artwork).hostname or ""

    if not artwork.startswith("https://") or not ("spotify" in host or host.endswith("scdn.co")):
        return jsonify({
            "primary": "#e85b9a",
            "secondary": "#5d2449",
            "light": "#fff0f6"
        })

    try:
        with urlopen(artwork, timeout=8) as response:
            image = Image.open(
                io.BytesIO(response.read())
            ).convert("RGB").resize((80, 80))

        palette_image = image.quantize(colors=8)
        palette = palette_image.getpalette()
        swatches = sorted(palette_image.getcolors() or [], reverse=True)

        colours = []

        for _, index in swatches:
            red, green, blue = palette[index * 3:index * 3 + 3]

            if max(red, green, blue) - min(red, green, blue) > 18 and max(red, green, blue) > 55:
                colour = f"#{red:02x}{green:02x}{blue:02x}"

                if colour not in colours:
                    colours.append(colour)

        primary = colours[0] if colours else "#e85b9a"
        secondary = colours[1] if len(colours) > 1 else "#5d2449"

        return jsonify({
            "primary": primary,
            "secondary": secondary,
            "light": "#fff5f9"
        })

    except (OSError, ValueError):
        return jsonify({
            "primary": "#e85b9a",
            "secondary": "#5d2449",
            "light": "#fff0f6"
        })
@app.get("/api/notes")
def get_notes():
    with db_connection() as connection: rows = connection.execute("SELECT id, body, track_name, artist_name, created_at FROM notes ORDER BY id DESC LIMIT 30").fetchall()
    return jsonify({"notes": [dict(row) for row in rows]})
@app.post("/api/notes")
def create_note():
    data = request.get_json(silent=True) or {}; body = str(data.get("body", "")).strip()
    if not body or len(body) > 500: return jsonify({"error": "Write a note between 1 and 500 characters."}), 400
    track, artist, created = str(data.get("track_name", ""))[:120], str(data.get("artist_name", ""))[:120], datetime.now(timezone.utc).isoformat()
    with db_connection() as connection: cursor = connection.execute("INSERT INTO notes (body, track_name, artist_name, created_at) VALUES (?, ?, ?, ?)", (body, track, artist, created))
    return jsonify({"note": {"id": cursor.lastrowid, "body": body, "track_name": track, "artist_name": artist, "created_at": created}}), 201
if __name__ == "__main__": initialize_database(); app.run(debug=True)
