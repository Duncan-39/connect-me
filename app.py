import os
import re
import secrets
import shutil
import uuid
from datetime import datetime
from io import BytesIO

from flask import (Flask, abort, flash, redirect, render_template, request,
                   send_from_directory, url_for)
from flask_login import (LoginManager, UserMixin, current_user, login_required,
                         login_user, logout_user)
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from PIL import Image, ImageOps, UnidentifiedImageError
from werkzeug.security import check_password_hash, generate_password_hash

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_ROOT = os.path.join(BASE_DIR, "uploads")
MAX_PHOTOS = 6
MAX_FILE_BYTES = 5 * 1024 * 1024
GENDERS = ["Man", "Woman", "Non-binary", "Prefer not to say"]
FORMAT_EXT = {"JPEG": "jpg", "PNG": "png", "WEBP": "webp"}
USERNAME_RE = re.compile(r"^[A-Za-z0-9_]{3,20}$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

app = Flask(__name__)
app.config.update(
    # No published fallback: random per-process key if unset/empty (logins reset on restart).
    SECRET_KEY=os.environ.get("SECRET_KEY") or secrets.token_hex(32),
    SQLALCHEMY_DATABASE_URI="sqlite:///" + os.path.join(BASE_DIR, "app.db"),
    # Room for MAX_PHOTOS files in one request; each file is checked separately.
    MAX_CONTENT_LENGTH=MAX_PHOTOS * MAX_FILE_BYTES + 1024 * 1024,
)

db = SQLAlchemy(app)
csrf = CSRFProtect(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)  # stored lowercase
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    display_name = db.Column(db.String(50))
    age = db.Column(db.Integer)
    gender = db.Column(db.String(20))
    bio = db.Column(db.String(500), default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    photos = db.relationship("Photo", backref="user", cascade="all, delete-orphan",
                             order_by="Photo.id")

    @property
    def profile_complete(self):
        return bool(self.display_name and self.age and self.gender)

    @property
    def main_photo(self):
        return self.photos[0] if self.photos else None

    @property
    def upload_dir(self):
        return os.path.join(UPLOAD_ROOT, self.username)


class Photo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    filename = db.Column(db.String(64), nullable=False)


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


@app.before_request
def require_complete_profile():
    """Send users with an unfinished profile to the profile form."""
    if (current_user.is_authenticated and not current_user.profile_complete
            and request.endpoint not in ("edit_profile", "logout", "static", "delete_account",
                                         "upload_photos", "delete_photo", "photo_file")):
        flash("Please complete your profile to continue.")
        return redirect(url_for("edit_profile"))


@app.route("/")
def index():
    return redirect(url_for("browse" if current_user.is_authenticated else "login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("browse"))
    if request.method == "POST":
        username = request.form.get("username", "").strip().lower()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        errors = []
        if not USERNAME_RE.match(username):
            errors.append("Username must be 3-20 characters: letters, digits, underscore.")
        if not EMAIL_RE.match(email):
            errors.append("Enter a valid email address.")
        if len(password) < 8:
            errors.append("Password must be at least 8 characters.")
        if not errors and User.query.filter_by(username=username).first():
            errors.append("That username is taken.")
        if not errors and User.query.filter_by(email=email).first():
            errors.append("That email is already registered.")
        if errors:
            for e in errors:
                flash(e)
            return render_template("register.html", username=username, email=email)
        user = User(username=username, email=email,
                    password_hash=generate_password_hash(password))
        db.session.add(user)
        db.session.commit()
        login_user(user)
        return redirect(url_for("edit_profile"))
    return render_template("register.html", username="", email="")


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("browse"))
    if request.method == "POST":
        username = request.form.get("username", "").strip().lower()
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, request.form.get("password", "")):
            login_user(user)
            return redirect(url_for("browse"))
        flash("Invalid username or password.")
    return render_template("login.html")


@app.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


@app.route("/browse")
@login_required
def browse():
    users = (User.query
             .filter(User.id != current_user.id,
                     User.display_name.isnot(None), User.display_name != "",
                     User.age.isnot(None), User.gender.isnot(None))
             .order_by(User.created_at.desc(), User.id.desc()).all())
    return render_template("browse.html", users=users)


@app.route("/user/<int:user_id>")
@login_required
def profile(user_id):
    user = db.get_or_404(User, user_id)
    if not user.profile_complete and user.id != current_user.id:
        abort(404)
    return render_template("profile.html", user=user)


@app.route("/photos/<int:photo_id>")
@login_required
def photo_file(photo_id):
    photo = db.get_or_404(Photo, photo_id)
    return send_from_directory(photo.user.upload_dir, photo.filename)


@app.route("/me", methods=["GET", "POST"])
@login_required
def edit_profile():
    if request.method == "POST":
        display_name = request.form.get("display_name", "").strip()
        gender = request.form.get("gender", "")
        bio = request.form.get("bio", "").strip()
        errors = []
        try:
            age = int(request.form.get("age", ""))
            if not 18 <= age <= 99:
                raise ValueError
        except ValueError:
            age = None
            errors.append("Age must be a number between 18 and 99.")
        if not 1 <= len(display_name) <= 50:
            errors.append("Display name is required (max 50 characters).")
        if gender not in GENDERS:
            errors.append("Choose a gender from the list.")
        if len(bio) > 500:
            errors.append("Bio must be 500 characters or fewer.")
        if errors:
            for e in errors:
                flash(e)
            return render_template("edit_profile.html", genders=GENDERS, form=request.form)
        current_user.display_name = display_name
        current_user.age = age
        current_user.gender = gender
        current_user.bio = bio
        db.session.commit()
        flash("Profile saved.")
        return redirect(url_for("edit_profile"))
    return render_template("edit_profile.html", genders=GENDERS, form=None)


def clean_image(data):
    """Validate an upload and re-encode it without metadata (EXIF/GPS).

    Returns (bytes, extension) or None if it is not a real JPEG, PNG or WebP.
    """
    try:
        with Image.open(BytesIO(data)) as img:
            fmt = img.format
            if fmt not in FORMAT_EXT:
                return None
            img.verify()
        # verify() invalidates the image, so reopen it for re-encoding.
        with Image.open(BytesIO(data)) as img:
            img = ImageOps.exif_transpose(img)
            out = BytesIO()
            kwargs = {"quality": 90} if fmt == "JPEG" else {}
            img.save(out, format=fmt, **kwargs)
    except (UnidentifiedImageError, OSError, SyntaxError, ValueError,
            Image.DecompressionBombError):
        return None
    return out.getvalue(), FORMAT_EXT[fmt]


@app.route("/me/photos", methods=["POST"])
@login_required
def upload_photos():
    files = [f for f in request.files.getlist("photos") if f and f.filename]
    if not files:
        flash("Choose at least one image.")
        return redirect(url_for("edit_profile"))
    room = MAX_PHOTOS - len(current_user.photos)
    if len(files) > room:
        flash(f"You can have at most {MAX_PHOTOS} photos ({room} slot(s) left).")
        return redirect(url_for("edit_profile"))

    saved = []
    for f in files:
        data = f.read(MAX_FILE_BYTES + 1)
        if len(data) > MAX_FILE_BYTES:
            flash(f"{f.filename}: larger than 5 MB.")
            continue
        cleaned = clean_image(data)
        if cleaned is None:
            flash(f"{f.filename}: only real JPG, PNG or WebP images are allowed.")
            continue
        saved.append(cleaned)

    if saved:
        os.makedirs(current_user.upload_dir, exist_ok=True)
        for data, ext in saved:
            name = f"{uuid.uuid4().hex}.{ext}"
            with open(os.path.join(current_user.upload_dir, name), "wb") as out:
                out.write(data)
            db.session.add(Photo(user_id=current_user.id, filename=name))
        db.session.commit()
        flash(f"Uploaded {len(saved)} photo(s).")
    return redirect(url_for("edit_profile"))


@app.route("/me/photos/<int:photo_id>/delete", methods=["POST"])
@login_required
def delete_photo(photo_id):
    photo = db.get_or_404(Photo, photo_id)
    if photo.user_id != current_user.id:
        abort(403)
    path = os.path.join(current_user.upload_dir, photo.filename)
    db.session.delete(photo)
    db.session.commit()
    if os.path.exists(path):
        os.remove(path)
    flash("Photo deleted.")
    return redirect(url_for("edit_profile"))


@app.route("/me/delete", methods=["POST"])
@login_required
def delete_account():
    user = db.session.get(User, current_user.id)
    folder = user.upload_dir
    logout_user()
    db.session.delete(user)
    db.session.commit()
    shutil.rmtree(folder, ignore_errors=True)
    flash("Your account has been deleted.")
    return redirect(url_for("login"))


@app.errorhandler(413)
def too_large(_):
    flash("Upload too large.")
    return redirect(url_for("edit_profile"))


with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)
