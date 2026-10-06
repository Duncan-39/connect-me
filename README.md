# Connect Me

A small dating web app built with Flask. Users register, log in, complete a profile, upload up to 6 photos, and browse other users' profiles.

This is a local demo. It has no moderation or real age verification and is not meant for public deployment as is.

## Features

- Register and log in with username and password (passwords are hashed)
- Profile with display name, age (18-99), gender and bio
- Upload up to 6 photos (JPG, PNG or WebP, max 5 MB each); the oldest photo is the main one
- Browse a grid of other users and open a full profile page
- Photos are visible only to logged-in users
- Delete individual photos or your whole account

Not included: likes, matches, chat, search, filters, password reset.

## Requirements

- Python 3.10 or newer
- The packages in `requirements.txt` (Flask, Flask-SQLAlchemy, Flask-Login, Flask-WTF, Pillow)

## Setup and run

### Create your own .venv

The `.venv` folder is not stored in the repository (it is git-ignored), so create your own after cloning. A virtual environment keeps this project's packages separate from the rest of your system.

1. Get the code and enter the project folder:

   ```
   git clone https://github.com/Duncan-39/connect-me.git
   cd connect-me
   ```

2. Check that Python is 3.10 or newer:

   ```
   python --version
   ```

3. Create the environment. This makes a `.venv` folder in the project:

   ```
   python -m venv .venv
   ```

4. Activate it. Your prompt should then start with `(.venv)`:

   | Shell                   | Command                      |
   |-------------------------|------------------------------|
   | Command Prompt          | `.venv\Scripts\activate.bat` |
   | PowerShell              | `.venv\Scripts\Activate.ps1` |
   | macOS / Linux / Git Bash | `source .venv/bin/activate` (Git Bash on Windows: `source .venv/Scripts/activate`) |

   If PowerShell refuses with "running scripts is disabled", run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once, then try again.

5. Confirm it is active. The path printed should point inside the project's `.venv` folder:

   ```
   python -c "import sys; print(sys.executable)"
   ```

To leave the environment later, run `deactivate`. To start over, delete the `.venv` folder and repeat from step 3.

### Option 1: venv (any terminal)

With the `.venv` created and activated as above:

```
pip install -r requirements.txt
python app.py
```

Next time, you only need to activate the `.venv` and run `python app.py`.

### Option 2: Anaconda Prompt

```
cd /d path\to\connect-me
conda create -n connectme python=3.12 -y
conda activate connectme
pip install -r requirements.txt
python app.py
```

Next time, only `conda activate connectme` and `python app.py` are needed.

Then open http://127.0.0.1:5000 in your browser. Stop the server with Ctrl+C.

On Windows, if `python` opens the Microsoft Store, use the venv or conda environment's Python (for example `.venv\Scripts\python app.py`).

## Demo users (optional)

```
python seed.py
```

This creates `alice`, `bob`, `sam` and `dana`, all with the password `password123` and no photos. You can also just register your own account.

## Configuration

| Variable     | Purpose                                                  | Default                 |
|--------------|----------------------------------------------------------|-------------------------|
| `SECRET_KEY` | Signs session cookies. Set your own for anything non-local. | a random per-process key (logins reset on restart) |

Windows (Command Prompt): `set SECRET_KEY=something-long-and-random`
macOS/Linux: `export SECRET_KEY=something-long-and-random`

## Where data is stored

- Users and photo records: SQLite file `app.db`, created automatically on first run
- Photo files: `uploads/<username>/<random-name>.<ext>`

To reset everything, stop the app and delete `app.db` and the `uploads` folder. The tables carry no migrations, so if you change the models, delete `app.db` as well.
