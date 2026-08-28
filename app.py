import json
import os
import re
import sqlite3
import sys
import threading
import webbrowser
from io import BytesIO
from functools import wraps
from zipfile import ZIP_DEFLATED, ZipFile

from flask import Flask, jsonify, render_template, request, send_file, session
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "python-in-practice-local-key")
if getattr(sys, "frozen", False):
    data_directory = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "PythonInPractice")
    os.makedirs(data_directory, exist_ok=True)
    app.config["DATABASE"] = os.path.join(data_directory, "python_practice.sqlite3")
else:
    app.config["DATABASE"] = os.path.join(os.path.dirname(__file__), "python_practice.sqlite3")

DEFAULT_FILES = {
    "scratch.py": "from datetime import datetime\n\ndef greet(name):\n    return f\"Hello, {name}.\"\n\nprint(greet(\"curious human\"))\nprint(f\"It is {datetime.now():%A}.\")",
    "README.md": "# Python in Practice\n\nA small place to write, run, and keep your Python ideas.\n",
}


def get_db():
    database = sqlite3.connect(app.config["DATABASE"])
    database.row_factory = sqlite3.Row
    return database


def init_db():
    database = get_db()
    database.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS workspaces (
            user_id INTEGER PRIMARY KEY,
            files TEXT NOT NULL,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        );
        """
    )
    database.commit()
    database.close()


def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if "user_id" not in session:
            return jsonify(error="Please log in to continue."), 401
        return view(*args, **kwargs)

    return wrapped_view


def valid_email(email):
    return len(email) <= 254 and bool(re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email))


init_db()


@app.route("/", methods=["GET", "POST"])
def home():
    submitted = request.method == "POST"
    return render_template("index.html", submitted=submitted, username=session.get("username"), workbench_page=False)


@app.get("/download/windows")
def download_windows():
    bundle = BytesIO()
    files = ("app.py", "requirements.txt", "README.md", "run_windows.bat", "static/styles.css", "static/supabase-config.js", "templates/index.html")
    with ZipFile(bundle, "w", ZIP_DEFLATED) as archive:
        for relative_path in files:
            archive.write(os.path.join(os.path.dirname(__file__), relative_path), os.path.join("python-in-practice", relative_path))
    bundle.seek(0)
    return send_file(bundle, mimetype="application/zip", as_attachment=True, download_name="python-in-practice-windows.zip")


@app.get("/workbench")
def workbench():
    return render_template("index.html", submitted=False, username=session.get("username"), workbench_page=True)


@app.post("/api/auth/register")
def register():
    payload = request.get_json(silent=True) or {}
    username = str(payload.get("email", payload.get("username", ""))).strip().lower()
    password = str(payload.get("password", ""))
    if not valid_email(username):
        return jsonify(error="Enter a valid email address, like you@example.com."), 400
    if len(password) < 8:
        return jsonify(error="Your password must be at least 8 characters."), 400

    database = get_db()
    try:
        cursor = database.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (username, generate_password_hash(password)),
        )
        user_id = cursor.lastrowid
        database.execute("INSERT INTO workspaces (user_id, files) VALUES (?, ?)", (user_id, json.dumps(DEFAULT_FILES)))
        database.commit()
    except sqlite3.IntegrityError:
        database.close()
        return jsonify(error="That email is already registered."), 409
    database.close()
    session.clear()
    session["user_id"] = user_id
    session["username"] = username
    return jsonify(username=username, files=DEFAULT_FILES), 201


@app.post("/api/auth/login")
def login():
    payload = request.get_json(silent=True) or {}
    username = str(payload.get("email", payload.get("username", ""))).strip().lower()
    password = str(payload.get("password", ""))
    database = get_db()
    user = database.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    if user is None or not check_password_hash(user["password_hash"], password):
        database.close()
        return jsonify(error="Username or password is incorrect."), 401
    workspace = database.execute("SELECT files FROM workspaces WHERE user_id = ?", (user["id"],)).fetchone()
    database.close()
    session.clear()
    session["user_id"] = user["id"]
    session["username"] = user["username"]
    return jsonify(username=user["username"], files=json.loads(workspace["files"]))


@app.post("/api/auth/logout")
def logout():
    session.clear()
    return jsonify(message="Logged out.")


@app.get("/api/session")
def current_session():
    if "user_id" not in session:
        return jsonify(authenticated=False)
    return jsonify(authenticated=True, username=session["username"])


@app.get("/api/workspace")
@login_required
def get_workspace():
    database = get_db()
    workspace = database.execute("SELECT files FROM workspaces WHERE user_id = ?", (session["user_id"],)).fetchone()
    database.close()
    return jsonify(files=json.loads(workspace["files"]))


@app.post("/api/workspace")
@login_required
def save_workspace():
    payload = request.get_json(silent=True) or {}
    files = payload.get("files")
    if not isinstance(files, dict) or len(files) > 50 or any(not isinstance(name, str) or not isinstance(content, str) for name, content in files.items()):
        return jsonify(error="Workspace data is invalid."), 400
    if sum(len(name) + len(content) for name, content in files.items()) > 500_000:
        return jsonify(error="Workspace is too large."), 400
    database = get_db()
    database.execute(
        "UPDATE workspaces SET files = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?",
        (json.dumps(files), session["user_id"]),
    )
    database.commit()
    database.close()
    return jsonify(saved=True)


if __name__ == "__main__":
    threading.Timer(1.25, lambda: webbrowser.open("http://127.0.0.1:5000")).start()
    app.run(debug=True)
