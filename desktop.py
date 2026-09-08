"""Launch Pink Petal Records as a native Windows desktop window."""
from threading import Thread

import webview

from app import app, initialize_database


def start_server():
    initialize_database()
    app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False)


if __name__ == "__main__":
    Thread(target=start_server, daemon=True).start()
    webview.create_window(
        "Pink Petal Records",
        "http://127.0.0.1:5000",
        width=470,
        height=760,
        min_size=(410, 620),
        background_color="#fff5f9",
    )
    webview.start()
