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

## Website

The public website is hosted on GitHub Pages at https://code.pip.abrdns.com. The landing page and browser workbench are static Pages-compatible files. The workbench runs Python in the browser and stores files locally in that browser; Flask is used for the Windows app and optional server deployment.

### Enable website accounts

1. Create a project at https://supabase.com.
2. In **SQL Editor**, run `supabase-schema.sql`.
3. Copy the project URL and public anon key from **Project Settings** → **API** into `supabase-config.js`.
4. Commit and push the updated config; GitHub Pages will redeploy the site.

The anon key is intended for browser use. Row-level security in the included schema limits each user to their own workspace.

## Windows download

Use the **Windows download** link on the website to download the source ZIP package. Extract it, then double-click `run_windows.bat`.

To create the Windows installer, run the **Build Windows executable** workflow in GitHub Actions, then download the `PythonInPractice-Setup-windows` artifact. It produces `PythonInPractice-Setup.exe`, which installs the app and creates Start Menu and desktop shortcuts. You can also run `build_windows.bat` on a Windows machine with Python installed to build the app files locally.

# DO NOT USE THIS WITHOUT CREDITING ME OR WITHOUT MY PERMISSION, AS THIS IS A COPYRIGHTED BUILD.

## Accounts

Create an account from the **Log in** button with an email such as `you@example.com` to save editor files to a local SQLite workspace. Set `SECRET_KEY` in the environment before deploying anywhere beyond local development.