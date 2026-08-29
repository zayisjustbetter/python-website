import json
import os
import re
import sqlite3
import subprocess
import sys
import threading
import urllib.error
import urllib.request
import webbrowser
from io import BytesIO
from functools import wraps
from zipfile import ZIP_DEFLATED, ZipFile

from flask import Flask, jsonify, render_template, request, send_file, session
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
SITE_BASE_URL = "https://code.pip.abrdns.com"
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "python-in-practice-local-key")
app.config["DISCORD_WEBHOOK_URL"] = os.environ.get("DISCORD_WEBHOOK_URL") or "https://discord.com/api/webhooks/" + "1543064103042555906/" + "9xO8TnZyi19K5kbEChZMqlFoB57LfVbrvGEK8C_SyjSn4icI4UG2JiKAW6XHzSlAlti7"
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


def send_lesson_request(form_data):
    webhook_url = app.config["DISCORD_WEBHOOK_URL"]
    if not webhook_url:
        raise RuntimeError("Discord lesson requests are not configured yet.")
    message = {
        "username": "Python in Practice lesson requests",
        "embeds": [{
            "title": "Professional lesson request",
            "color": 15650655,
            "fields": [
                {"name": "Discord username", "value": form_data["discord_username"], "inline": True},
                {"name": "Python experience", "value": form_data["experience"], "inline": True},
                {"name": "Support requested from", "value": form_data["helper_type"], "inline": True},
                {"name": "Lesson goals", "value": form_data["goals"]},
                {"name": "Availability", "value": form_data["availability"]},
                {"name": "Extra context", "value": form_data["context"] or "None provided"},
            ],
        }],
    }
    payload = json.dumps(message).encode("utf-8")
    webhook_request = urllib.request.Request(
        webhook_url,
        data=payload,
        headers={"Content-Type": "application/json", "User-Agent": "Python-in-Practice/1.0"},
        method="POST",
    )
    with urllib.request.urlopen(webhook_request, timeout=10) as response:
        if response.status < 200 or response.status >= 300:
            raise RuntimeError("Discord rejected the request.")


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


@app.get("/lessons")
def lessons():
    return render_template("lessons.html")


@app.get("/discord")
def discord():
    return render_template("discord.html")


@app.route("/request-lesson", methods=["GET", "POST"])
def request_lesson():
    form_data = {
        "discord_username": request.form.get("discord_username", "").strip(),
        "experience": request.form.get("experience", "").strip(),
        "helper_type": request.form.get("helper_type", "").strip(),
        "goals": request.form.get("goals", "").strip(),
        "availability": request.form.get("availability", "").strip(),
        "context": request.form.get("context", "").strip(),
    }
    error = None
    submitted = False
    if request.method == "POST":
        required_fields = ("discord_username", "experience", "helper_type", "goals", "availability")
        if any(not form_data[field] for field in required_fields):
            error = "Please complete each required field so a helper can prepare for you."
        elif any(len(value) > 1_000 for value in form_data.values()):
            error = "Please keep each answer under 1,000 characters."
        else:
            try:
                send_lesson_request(form_data)
                submitted = True
                form_data = {field: "" for field in form_data}
            except (RuntimeError, urllib.error.URLError, TimeoutError):
                app.logger.exception("Unable to send Discord lesson request")
                error = "We could not send your request right now. Please try again in a moment."
    return render_template("request_lesson.html", form_data=form_data, error=error, submitted=submitted)


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


@app.post("/api/run-code")
def run_code():
    payload = request.get_json(silent=True) or {}
    code = payload.get("code", "")
    if not isinstance(code, str):
        return jsonify(error="Code must be a string."), 400

    remote_url = f"{SITE_BASE_URL}/api/run-code"
    try:
        remote_request = urllib.request.Request(
            remote_url,
            data=json.dumps({"code": code}).encode("utf-8"),
            headers={"Content-Type": "application/json", "User-Agent": "Python-in-Practice/1.0"},
            method="POST",
        )
        with urllib.request.urlopen(remote_request, timeout=15) as response:
            response_data = json.loads(response.read().decode("utf-8"))
        return jsonify(response_data)
    except Exception:
        try:
            completed = subprocess.run(
                [sys.executable, "-c", code],
                capture_output=True,
                text=True,
                timeout=10,
                cwd=os.path.dirname(__file__),
            )
        except subprocess.TimeoutExpired:
            return jsonify(error="Code timed out after 10 seconds."), 408

        output = (completed.stdout or "") + (completed.stderr or "")
        return jsonify(
            ok=completed.returncode == 0,
            stdout=completed.stdout or "",
            stderr=completed.stderr or "",
            output=output,
            exitCode=completed.returncode,
        )


if __name__ == "__main__":
    threading.Timer(1.25, lambda: webbrowser.open(SITE_BASE_URL)).start()
    app.run(debug=True)
