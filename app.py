import os
import smtplib
import uuid
from email.mime.text import MIMEText
from functools import wraps
from urllib.parse import parse_qsl, urlparse, urlencode, urlunparse

import psycopg2
import psycopg2.extras
from werkzeug.utils import secure_filename

from dotenv import load_dotenv
from flask import (Flask, g, jsonify, redirect, render_template,
                   request, session, url_for)

load_dotenv()

app = Flask(__name__, static_folder=".", static_url_path="")
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-change-in-production")
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "img", "uploads")
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp", "gif"}

SPORT_EMOJI = {
    "soccer":          "⚽",
    "flag football":   "🏈",
    "football":        "🏈",
    "basketball":      "🏀",
    "ice hockey":      "🏒",
    "roller hockey":   "🏒",
    "softball":        "🥎",
    "baseball":        "⚾",
    "volleyball":      "🏐",
    "tennis":          "🎾",
    "swimming":        "🏊",
    "running":         "🏃‍♀️",
    "cycling":         "🚴",
    "bowling":         "🎳",
    "golf":            "⛳",
    "wrestling":       "🤼",
    "boxing":          "🥊",
    "yoga":            "🧘",
    "climbing":        "🧗",
    "roller derby":    "🛼",
    "roller skating":    "🛼",
    "kickball":        "☄️",
    "ultimate frisbee":"🥏",
    "frisbee":         "🥏",
    "lacrosse":        "🥍",
    "rugby":           "🏉",
    "pickleball":      "🏓",
    "snowboarding":    "🏂",
    "martial arts":    "🥋",
    "birding":         "🐦",
    "pool":            "🎱"
}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def normalize_database_url(database_url: str) -> str:
    if not database_url:
        return database_url
    database_url = database_url.strip()
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    parsed = urlparse(database_url)
    query = dict(parse_qsl(parsed.query, keep_blank_values=True))
    query.pop("channel_binding", None)
    if "sslmode" not in query:
        query["sslmode"] = "require"
    return urlunparse(parsed._replace(query=urlencode(query)))


DATABASE_URL = normalize_database_url(os.environ.get("DATABASE_URL", ""))
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL environment variable is required.")


def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = psycopg2.connect(DATABASE_URL, connect_timeout=10)
    return db


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()


def _connect():
    return psycopg2.connect(DATABASE_URL, connect_timeout=10)


def _table_exists():
    conn = _connect()
    cur = conn.cursor()
    cur.execute("SELECT to_regclass('public.clubs')")
    result = cur.fetchone()
    cur.close()
    conn.close()
    return result[0] is not None


def send_submission_email(club_name, sport):
    notify_email = os.environ.get("NOTIFY_EMAIL")
    smtp_host    = os.environ.get("SMTP_HOST")
    smtp_user    = os.environ.get("SMTP_USER")
    smtp_pass    = os.environ.get("SMTP_PASS")
    smtp_port    = int(os.environ.get("SMTP_PORT", "587"))

    if not all([notify_email, smtp_host, smtp_user, smtp_pass]):
        print(f"[SUBMISSION] New pending club: {club_name} ({sport})")
        return

    body = (
        f"A new club has been submitted and is waiting for your review.\n\n"
        f"  Club:  {club_name}\n"
        f"  Sport: {sport}\n\n"
        f"Review it at: {request.host_url}admin"
    )
    msg = MIMEText(body)
    msg["Subject"] = f"[Queer Sports DB] New submission: {club_name}"
    msg["From"]    = smtp_user
    msg["To"]      = notify_email

    try:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)
    except Exception as e:
        print(f"[SUBMISSION] Email failed: {e}")


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("admin"):
            return redirect(url_for("admin_login"))
        return f(*args, **kwargs)
    return decorated


_db_ready = False


def ensure_db_ready():
    global _db_ready
    if _db_ready:
        return True
    try:
        if not _table_exists():
            return False
        conn = _connect()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS contact_messages (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                club_id INTEGER,
                subject TEXT,
                message TEXT NOT NULL,
                completed BOOLEAN NOT NULL DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # Fix the clubs id sequence to prevent duplicate key errors
        cur.execute("SELECT setval('clubs_id_seq', (SELECT COALESCE(MAX(id), 0) + 1 FROM clubs))")
        conn.commit()
        cur.close()
        conn.close()
        _db_ready = True
        return True
    except Exception as e:
        print(f"[DB] Connection failed: {e}")
        return False


# ── Public routes ────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return app.send_static_file("index.html")


@app.route("/sports-database")
def sports_database():
    if not ensure_db_ready():
        return "Database unavailable — please try again shortly.", 503
    db = get_db()
    cur = db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT * FROM clubs WHERE status = 'approved' ORDER BY club_name ASC")
    clubs = cur.fetchall()
    cur.execute("SELECT DISTINCT sport FROM clubs WHERE status = 'approved' ORDER BY sport")
    sports = [r["sport"] for r in cur.fetchall()]
    cur.execute("SELECT DISTINCT city FROM clubs WHERE status = 'approved' AND city IS NOT NULL ORDER BY city")
    cities = [r["city"] for r in cur.fetchall()]
    return render_template("sports_database.html", clubs=clubs, sports=sports, cities=cities,
                           sport_emoji=SPORT_EMOJI)


@app.route("/sports-database/<int:club_id>")
def club_detail(club_id):
    if not ensure_db_ready():
        return "Database unavailable — please try again shortly.", 503
    db = get_db()
    cur = db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT * FROM clubs WHERE id = %s AND status = 'approved'", [club_id])
    club = cur.fetchone()
    if club is None:
        return "Club not found", 404
    return render_template("club_detail.html", club=club, sport_emoji=SPORT_EMOJI)


@app.route("/submit", methods=["GET", "POST"])
@app.route("/contributor", methods=["GET", "POST"])
def submit():
    if not ensure_db_ready():
        return "Database unavailable — please try again shortly.", 503
    error = None
    if request.method == "POST":
        club_name   = request.form.get("club_name", "").strip()
        sport       = request.form.get("sport", "").strip()
        city        = request.form.get("city", "").strip() or None
        is_comp     = request.form.get("is_comp") == "on"
        is_rec      = request.form.get("is_rec") == "on"
        is_pickup   = request.form.get("is_pickup") == "on"
        is_league   = request.form.get("is_league") == "on"
        is_tournament = request.form.get("is_tournament") == "on"
        is_travel          = request.form.get("is_travel") == "on"
        is_trans_inclusive  = request.form.get("is_trans_inclusive") == "on"
        is_lesbian_centered = request.form.get("is_lesbian_centered") == "on"
        instagram   = request.form.get("instagram", "").strip().lstrip("@") or None
        website     = request.form.get("website", "").strip() or None
        notes       = request.form.get("notes", "").strip() or None

        if not all([club_name, sport]):
            error = "Club name and sport are required."
        elif not (is_comp or is_rec):
            error = "Please select at least one skill level (Competitive or Recreational)."
        else:
            photo_url = None
            photo = request.files.get("photo")
            if photo and photo.filename:
                if not allowed_file(photo.filename):
                    error = "Photo must be a JPG, PNG, WebP, or GIF."
                else:
                    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
                    ext = photo.filename.rsplit(".", 1)[1].lower()
                    filename = f"{uuid.uuid4().hex}.{ext}"
                    photo.save(os.path.join(UPLOAD_FOLDER, filename))
                    photo_url = f"img/uploads/{filename}"

            if not error:
                db = get_db()
                cur = db.cursor()
                try:
                    cur.execute(
                        """INSERT INTO clubs
                           (club_name, sport, city, is_comp, is_rec, is_pickup, is_league, is_tournament, is_travel,
                            is_trans_inclusive, is_lesbian_centered, instagram, website, notes, photo_url, status)
                           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'pending')""",
                        [club_name, sport, city, is_comp, is_rec, is_pickup, is_league, is_tournament, is_travel,
                         is_trans_inclusive, is_lesbian_centered, instagram, website, notes, photo_url],
                    )
                    db.commit()
                    send_submission_email(club_name, sport)
                    return redirect(url_for("submit_thanks"))
                except Exception as e:
                    db.rollback()
                    print(f"[SUBMIT ERROR] {e}")
                    error = f"Submission failed (DB error): {e}"

    return render_template("submit.html", error=error)


@app.route("/submit/thanks")
def submit_thanks():
    return render_template("submit_thanks.html")


@app.route("/contact", methods=["GET", "POST"])
def contact():
    if not ensure_db_ready():
        return "Database unavailable — please try again shortly.", 503
    db = get_db()
    error = None
    sent  = False
    preselect_club_id = request.args.get("club_id", type=int)

    if request.method == "POST":
        name    = request.form.get("name", "").strip()
        email   = request.form.get("email", "").strip()
        club_id = request.form.get("club_id", "").strip()
        subject = request.form.get("subject", "").strip() or None
        message = request.form.get("message", "").strip()
        club_id_val = int(club_id) if club_id.isdigit() else None

        if not all([name, email, message]):
            error = "Name, email, and message are required."
        else:
            cur = db.cursor()
            try:
                cur.execute(
                    """INSERT INTO contact_messages (name, email, club_id, subject, message)
                       VALUES (%s, %s, %s, %s, %s)""",
                    [name, email, club_id_val, subject, message],
                )
                db.commit()
                sent = True
            except Exception as e:
                db.rollback()
                print(f"[CONTACT ERROR] {e}")
                error = f"Could not send message: {e}"

    cur = db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT id, club_name FROM clubs WHERE status = 'approved' ORDER BY club_name ASC")
    clubs = cur.fetchall()
    return render_template("contact.html", clubs=clubs, error=error, sent=sent,
                           preselect_club_id=preselect_club_id)


@app.route("/api/stats")
def api_stats():
    if not ensure_db_ready():
        return jsonify({"error": "Database unavailable"}), 503
    db = get_db()
    cur = db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("""SELECT sport, city,
                          is_comp, is_rec,
                          is_pickup, is_league, is_tournament, is_travel,
                          is_trans_inclusive, is_lesbian_centered
                   FROM clubs WHERE status = 'approved'""")
    clubs = cur.fetchall()

    by_sport, by_city = {}, {}
    for c in clubs:
        by_sport[c["sport"]] = by_sport.get(c["sport"], 0) + 1
        if c["city"]:
            by_city[c["city"]] = by_city.get(c["city"], 0) + 1

    trans_count   = sum(1 for c in clubs if c["is_trans_inclusive"])
    lesbian_count = sum(1 for c in clubs if c["is_lesbian_centered"])
    both_count    = sum(1 for c in clubs if c["is_trans_inclusive"] and c["is_lesbian_centered"])
    either_count  = sum(1 for c in clubs if c["is_trans_inclusive"] or c["is_lesbian_centered"])
    no_flag_count = len(clubs) - either_count

    travel_reach_count = sum(
        1 for c in clubs
        if c["is_travel"] or c["is_tournament"] or c["is_league"]
    )

    return jsonify({
        "total":      len(clubs),
        "num_cities": len(by_city),
        "num_sports": len(by_sport),
        "by_sport":   sorted(by_sport.items(), key=lambda x: -x[1]),
        "by_city":    sorted(by_city.items(), key=lambda x: -x[1]),
        "competitive":  sum(1 for c in clubs if c["is_comp"]),
        "recreational": sum(1 for c in clubs if c["is_rec"]),
        "pickup":       sum(1 for c in clubs if c["is_pickup"]),
        "league":       sum(1 for c in clubs if c["is_league"]),
        "tournament":   sum(1 for c in clubs if c["is_tournament"]),
        "travel":       sum(1 for c in clubs if c["is_travel"]),
        "trans_inclusive":   trans_count,
        "lesbian_centered":  lesbian_count,
        "both_flags":        both_count,
        "either_flag":       either_count,
        "no_flag":           no_flag_count,
        "travel_reach":      travel_reach_count,
    })


# ── Admin routes ─────────────────────────────────────────────────────────────

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    error = None
    if request.method == "POST":
        if request.form.get("password") == os.environ.get("ADMIN_PASSWORD", ""):
            session["admin"] = True
            return redirect(url_for("admin"))
        error = "Incorrect password."
    return render_template("admin_login.html", error=error)


@app.route("/admin/logout")
def admin_logout():
    session.pop("admin", None)
    return redirect(url_for("admin_login"))


@app.route("/admin")
@admin_required
def admin():
    if not ensure_db_ready():
        return "Database unavailable — please try again shortly.", 503
    db = get_db()
    cur = db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT * FROM clubs WHERE status = 'pending' ORDER BY created_at DESC")
    pending = cur.fetchall()
    cur.execute("SELECT * FROM clubs WHERE status = 'approved' ORDER BY club_name ASC")
    approved = cur.fetchall()
    messages = []
    try:
        cur.execute("""
            SELECT m.*, c.club_name
            FROM contact_messages m
            LEFT JOIN clubs c ON c.id = m.club_id
            WHERE m.completed = FALSE
            ORDER BY m.created_at DESC
        """)
        messages = cur.fetchall()
    except Exception as e:
        print(f"[ADMIN MESSAGES] {e}")
        db.rollback()
    return render_template("admin.html", pending=pending, approved=approved, messages=messages)


@app.route("/admin/message/<int:message_id>/complete", methods=["POST"])
@admin_required
def admin_message_complete(message_id):
    if not ensure_db_ready():
        return "Database unavailable — please try again shortly.", 503
    db = get_db()
    cur = db.cursor()
    cur.execute("UPDATE contact_messages SET completed = TRUE WHERE id = %s", [message_id])
    db.commit()
    return redirect(url_for("admin"))


@app.route("/admin/approve/<int:club_id>", methods=["POST"])
@admin_required
def admin_approve(club_id):
    if not ensure_db_ready():
        return "Database unavailable — please try again shortly.", 503
    db = get_db()
    cur = db.cursor()
    cur.execute("UPDATE clubs SET status = 'approved' WHERE id = %s", [club_id])
    db.commit()
    return redirect(url_for("admin"))


@app.route("/admin/reject/<int:club_id>", methods=["POST"])
@admin_required
def admin_reject(club_id):
    if not ensure_db_ready():
        return "Database unavailable — please try again shortly.", 503
    db = get_db()
    cur = db.cursor()
    cur.execute("DELETE FROM clubs WHERE id = %s AND status = 'pending'", [club_id])
    db.commit()
    return redirect(url_for("admin"))


@app.route("/admin/edit/<int:club_id>", methods=["GET", "POST"])
@admin_required
def admin_edit(club_id):
    if not ensure_db_ready():
        return "Database unavailable — please try again shortly.", 503
    db = get_db()
    if request.method == "POST":
        cur = db.cursor()
        instagram = request.form.get("instagram", "").strip().lstrip("@") or None
        try:
            cur.execute(
                """UPDATE clubs SET
                   club_name = %s, sport = %s, city = %s,
                   is_comp = %s, is_rec = %s,
                   is_pickup = %s, is_league = %s, is_tournament = %s, is_travel = %s,
                   is_trans_inclusive = %s, is_lesbian_centered = %s,
                   weekday = %s, cost = %s,
                   instagram = %s, website = %s, notes = %s, status = %s
                   WHERE id = %s""",
                [
                    request.form.get("club_name", "").strip(),
                    request.form.get("sport", "").strip(),
                    request.form.get("city", "").strip() or None,
                    request.form.get("is_comp") == "on",
                    request.form.get("is_rec") == "on",
                    request.form.get("is_pickup") == "on",
                    request.form.get("is_league") == "on",
                    request.form.get("is_tournament") == "on",
                    request.form.get("is_travel") == "on",
                    request.form.get("is_trans_inclusive") == "on",
                    request.form.get("is_lesbian_centered") == "on",
                    request.form.get("weekday", "").strip() or None,
                    request.form.get("cost", "").strip() or None,
                    instagram,
                    request.form.get("website", "").strip() or None,
                    request.form.get("notes", "").strip() or None,
                    request.form.get("status", "approved"),
                    club_id,
                ],
            )
            db.commit()
        except Exception as e:
            db.rollback()
            print(f"[ADMIN EDIT ERROR] club_id={club_id}: {e}")
            return f"<pre>Save failed:\n{e}</pre>", 500
        return redirect(url_for("admin"))
    cur = db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT * FROM clubs WHERE id = %s", [club_id])
    club = cur.fetchone()
    if club is None:
        return "Club not found", 404
    return render_template("admin_edit.html", club=club)


@app.route("/admin/delete/<int:club_id>", methods=["POST"])
@admin_required
def admin_delete(club_id):
    if not ensure_db_ready():
        return "Database unavailable — please try again shortly.", 503
    db = get_db()
    cur = db.cursor()
    cur.execute("DELETE FROM clubs WHERE id = %s", [club_id])
    db.commit()
    return redirect(url_for("admin"))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host="0.0.0.0", port=port)
