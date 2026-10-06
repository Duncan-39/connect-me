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

### Option 1: venv (any terminal)

```
git clone https://github.com/Duncan-39/connect-me.git
cd connect-me

python -m venv .venv
.venv\Scripts\activate          # macOS/Linux: source .venv/bin/activate

pip install -r requirements.txt
python app.py
```

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
| `SECRET_KEY` | Signs session cookies. Set your own for anything non-local. | a dev-only placeholder |

Windows (Command Prompt): `set SECRET_KEY=something-long-and-random`
macOS/Linux: `export SECRET_KEY=something-long-and-random`

## Where data is stored

- Users and photo records: SQLite file `app.db`, created automatically on first run
- Photo files: `uploads/<username>/<random-name>.<ext>`

To reset everything, stop the app and delete `app.db` and the `uploads` folder. The tables carry no migrations, so if you change the models, delete `app.db` as well.
