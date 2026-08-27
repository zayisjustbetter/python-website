# Python in Practice

A small Flask website with an editorial landing page, responsive layout, and a working email signup form.

## Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000 in your browser.

## Windows download

Use the **Windows download** link on the website to download the source ZIP package. Extract it, then double-click `run_windows.bat`.

To create the standalone Windows executable, run the **Build Windows executable** workflow in GitHub Actions, then download the `PythonInPractice-windows` artifact. The ZIP contains `PythonInPractice.exe` and the bundled templates and static files. You can also run `build_windows.bat` on a Windows machine with Python installed.

# DO NOT USE THIS WITHOUT CREDITING ME OR WITHOUT MY PERMISSION, AS THIS IS A COPYRIGHTED BUILD.

## Accounts

Create an account from the **Log in** button with an email such as `you@example.com` to save editor files to a local SQLite workspace. Set `SECRET_KEY` in the environment before deploying anywhere beyond local development.