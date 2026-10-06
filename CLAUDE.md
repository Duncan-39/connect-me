# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

The system `python` on this machine is only the Microsoft Store stub. Use the project venv (`.venv`, built from Anaconda Python) or a conda env.

```
.venv\Scripts\python app.py        # run dev server at http://127.0.0.1:5000 (debug=True, auto-reload)
.venv\Scripts\python seed.py       # optional demo users: alice, bob, sam, dana (password: password123)
.venv\Scripts\python -m pip install -r requirements.txt
```

There is no test suite or linter configured. To reset all data, stop the app and delete `app.db` and `uploads/`; both are recreated on demand.

## Architecture

Server-rendered Flask app (Jinja templates, plain CSS, almost no JS). Everything lives in `app.py`: models, routes and validation. `db.create_all()` runs at import time, so there are no migrations. Changing a column means deleting `app.db`.

Cross-cutting behaviours that span several places:

- **Profile gate**: a `before_request` hook redirects any logged-in user whose profile is incomplete (`display_name`, `age`, `gender` all required) to `/me`. Only `edit_profile`, `logout`, `delete_account` and `static` are exempt. New routes are gated automatically. `browse` and `profile` also hide incomplete profiles from other users.
- **Photos span DB and disk**: `Photo` rows store only a random UUID filename. Files live at `uploads/<username>/<uuid>.<ext>`. Photos are never served as static files. They go through the `@login_required` route `/photos/<id>`. The "main" photo is simply the oldest remaining one (`User.photos` is ordered by `Photo.id`, `main_photo` is `photos[0]`), so there is no reorder or primary flag. Deleting a photo or an account must also remove the files on disk (`delete_photo`, `delete_account`).
- **Upload validation**: file type is checked by content with Pillow (`Image.open` plus `verify`, format must be JPEG, PNG or WEBP) and the extension comes from the detected format, never the upload name. Limits are 6 photos per user and 5 MB per file. `MAX_CONTENT_LENGTH` is only the overall request cap.
- **Usernames are stored lowercase** (regex `[A-Za-z0-9_]{3,20}`) and double as folder names, so keep that normalisation and regex intact. It is what prevents path tricks and case-collision on Windows.
- **CSRF**: `CSRFProtect` is global, so every POST form (including logout and delete) needs `<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">`.
- `SECRET_KEY` comes from the environment and falls back to a dev-only value.

## Scope

Browse-only by design. Likes, matches, chat, filters, search, pagination, password change or reset and email verification are intentionally not implemented. Local demo only: no moderation or real age verification (age is self-reported, 18-99).
