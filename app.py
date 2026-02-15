from flask import Flask, render_template, request, redirect, url_for, abort, jsonify
import os
import re
import random
import json

import psycopg
from psycopg.rows import dict_row

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
PEOPLE_DIR = os.path.join(BASE_DIR, "people")

# Local fallback files (only used if DATABASE_URL is NOT set)
CHAR_FILE = os.path.join(DATA_DIR, "characters.json")
NOTES_FILE = os.path.join(DATA_DIR, "dm_notes.json")

PLACEHOLDER_IMAGE = "placeholder.jpg"

_tables_ready = False


def get_db_url() -> str | None:
    return os.environ.get("DATABASE_URL")


def using_db() -> bool:
    return bool(get_db_url())


def ensure_dirs():
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(PEOPLE_DIR, exist_ok=True)

    # Local fallback init
    if not os.path.exists(CHAR_FILE):
        with open(CHAR_FILE, "w", encoding="utf-8") as f:
            json.dump([], f, indent=2, ensure_ascii=False)

    if not os.path.exists(NOTES_FILE):
        with open(NOTES_FILE, "w", encoding="utf-8") as f:
            json.dump(
                {"hooks": "", "previous_session": "", "misc": ""},
                f,
                indent=2,
                ensure_ascii=False
            )


def db_conn():
    db_url = get_db_url()
    if not db_url:
        raise RuntimeError("DATABASE_URL is not set")
    return psycopg.connect(db_url, row_factory=dict_row)


def ensure_tables():
    # Only if DATABASE_URL exists
    if not using_db():
        return

    with db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS dm_notes (
                    id INTEGER PRIMARY KEY,
                    hooks TEXT NOT NULL DEFAULT '',
                    previous_session TEXT NOT NULL DEFAULT '',
                    misc TEXT NOT NULL DEFAULT ''
                );
            """)
            cur.execute("""
                INSERT INTO dm_notes (id, hooks, previous_session, misc)
                VALUES (1, '', '', '')
                ON CONFLICT (id) DO NOTHING;
            """)

            cur.execute("""
                CREATE TABLE IF NOT EXISTS characters (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    role TEXT NOT NULL,
                    bio TEXT NOT NULL,
                    image TEXT NOT NULL DEFAULT 'placeholder.jpg',
                    available BOOLEAN NOT NULL DEFAULT FALSE
                );
            """)
        conn.commit()


@app.before_request
def _init_once():
    global _tables_ready
    if _tables_ready:
        return
    ensure_dirs()
    if using_db():
        ensure_tables()
    _tables_ready = True


def slugify(name: str) -> str:
    s = name.strip().lower()
    s = re.sub(r"[^a-z0-9]+", "_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    return s or "character"


# ===== Characters (DB or fallback) =====
def load_characters():
    if using_db():
        with db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, name, role, bio, image, available
                    FROM characters
                    ORDER BY name ASC
                """)
                return cur.fetchall()

    with open(CHAR_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def character_id_exists(char_id: str) -> bool:
    if using_db():
        with db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1 FROM characters WHERE id=%s LIMIT 1;", (char_id,))
                return cur.fetchone() is not None

    chars = load_characters()
    return any(c["id"] == char_id for c in chars)


def insert_character(new_char: dict):
    if using_db():
        with db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO characters (id, name, role, bio, image, available)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    new_char["id"],
                    new_char["name"],
                    new_char["role"],
                    new_char["bio"],
                    new_char["image"],
                    new_char["available"],
                ))
            conn.commit()
        return

    chars = load_characters()
    chars.append(new_char)
    with open(CHAR_FILE, "w", encoding="utf-8") as f:
        json.dump(chars, f, indent=2, ensure_ascii=False)


def set_character_availability(available_ids: set):
    if using_db():
        with db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("UPDATE characters SET available = FALSE;")
                if available_ids:
                    cur.execute("""
                        UPDATE characters
                        SET available = TRUE
                        WHERE id = ANY(%s)
                    """, (list(available_ids),))
            conn.commit()
        return

    chars = load_characters()
    for c in chars:
        c["available"] = c["id"] in available_ids
    with open(CHAR_FILE, "w", encoding="utf-8") as f:
        json.dump(chars, f, indent=2, ensure_ascii=False)


# ===== Notes (DB or fallback) =====
def load_notes():
    if using_db():
        with db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT hooks, previous_session, misc FROM dm_notes WHERE id=1;")
                row = cur.fetchone()
        return row or {"hooks": "", "previous_session": "", "misc": ""}

    try:
        with open(NOTES_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return {
            "hooks": data.get("hooks", ""),
            "previous_session": data.get("previous_session", ""),
            "misc": data.get("misc", ""),
        }
    except (FileNotFoundError, json.JSONDecodeError):
        return {"hooks": "", "previous_session": "", "misc": ""}


def save_notes(hooks: str, previous_session: str, misc: str):
    if using_db():
        with db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE dm_notes
                    SET hooks=%s, previous_session=%s, misc=%s
                    WHERE id=1
                """, (hooks, previous_session, misc))
            conn.commit()
        return

    with open(NOTES_FILE, "w", encoding="utf-8") as f:
        json.dump(
            {"hooks": hooks, "previous_session": previous_session, "misc": misc},
            f,
            indent=2,
            ensure_ascii=False
        )


@app.route("/api/dbcheck")
def dbcheck():
    db_url_set = using_db()
    ok = False
    err = None
    if db_url_set:
        try:
            with db_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1;")
                    cur.fetchone()
            ok = True
        except Exception as e:
            err = str(e)
    return jsonify({"DATABASE_URL_set": db_url_set, "db_connect_ok": ok, "error": err})


@app.route("/")
def index():
    poster_dir = os.path.join(app.static_folder, "posters")
    posters = []
    if os.path.isdir(poster_dir):
        posters = [
            f for f in os.listdir(poster_dir)
            if f.lower().endswith((".jpg", ".jpeg", ".png", ".webp"))
        ]
    poster = random.choice(posters) if posters else None
    return render_template("index.html", poster=poster)


@app.route("/dm")
def dm_home():
    return render_template("dm_home.html")


@app.route("/api/notes", methods=["GET", "POST"])
def api_notes():
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        hooks = data.get("hooks", "")
        previous_session = data.get("previous_session", "")
        misc = data.get("misc", "")

        if not all(isinstance(x, str) for x in [hooks, previous_session, misc]):
            return jsonify({"error": "All fields must be strings"}), 400

        save_notes(hooks, previous_session, misc)
        return jsonify({"status": "ok"})

    return jsonify(load_notes())


@app.route("/dm/add", methods=["GET", "POST"])
def dm_add_character():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        role = request.form.get("role", "").strip()
        bio = request.form.get("bio", "").strip()

        if not name or not role or not bio:
            return render_template("dm_add.html", error="Fill out name, role, and bio.")

        new_id = slugify(name)
        if character_id_exists(new_id):
            i = 2
            while character_id_exists(f"{new_id}_{i}"):
                i += 1
            new_id = f"{new_id}_{i}"

        new_char = {
            "id": new_id,
            "name": name,
            "role": role,
            "bio": bio,
            "image": PLACEHOLDER_IMAGE,
            "available": False
        }

        insert_character(new_char)
        return redirect(url_for("dm_home"))

    return render_template("dm_add.html", error=None)


@app.route("/dm/toggles", methods=["GET", "POST"])
def dm_toggles():
    if request.method == "POST":
        available_ids = set(request.form.getlist("available"))
        set_character_availability(available_ids)
        return redirect(url_for("dm_toggles"))

    chars = load_characters()
    return render_template("dm_toggles.html", characters=chars)

@app.route("/dm/import", methods=["GET", "POST"])
def dm_import_characters():
    if not using_db():
        return "DATABASE_URL not set. DB import requires Neon.", 400

    if request.method == "POST":
        raw = request.form.get("json_blob", "").strip()
        if not raw:
            return render_template("dm_import.html", error="Paste your characters.json content.", ok=None)

        try:
            chars = json.loads(raw)
            if not isinstance(chars, list):
                return render_template("dm_import.html", error="JSON must be a list of characters.", ok=None)
        except json.JSONDecodeError as e:
            return render_template("dm_import.html", error=f"Invalid JSON: {e}", ok=None)

        inserted = 0
        with db_conn() as conn:
            with conn.cursor() as cur:
                for c in chars:
                    if not isinstance(c, dict):
                        continue
                    char_id = (c.get("id") or "").strip()
                    name = (c.get("name") or "").strip()
                    role = (c.get("role") or "").strip()
                    bio = (c.get("bio") or "").strip()
                    image = (c.get("image") or "placeholder.jpg").strip()
                    available = bool(c.get("available", False))

                    if not char_id or not name or not role or not bio:
                        continue

                    cur.execute("""
                        INSERT INTO characters (id, name, role, bio, image, available)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        ON CONFLICT (id) DO NOTHING
                    """, (char_id, name, role, bio, image, available))

                    if cur.rowcount == 1:
                        inserted += 1
            conn.commit()

        return render_template("dm_import.html", error=None, ok=f"Imported {inserted} characters into Neon.")

    return render_template("dm_import.html", error=None, ok=None)



@app.route("/phonebook")
def phonebook():
    chars = load_characters()
    visible = [c for c in chars if c.get("available")]
    return render_template("phonebook.html", characters=visible)


@app.route("/character/<char_id>")
def character_page(char_id):
    if using_db():
        with db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, name, role, bio, image, available
                    FROM characters
                    WHERE id=%s
                    LIMIT 1
                """, (char_id,))
                character = cur.fetchone()
    else:
        chars = load_characters()
        character = next((c for c in chars if c["id"] == char_id), None)

    if character is None:
        abort(404)

    return render_template("character.html", character=character)


@app.route("/map")
def map_page():
    return render_template("map.html")


@app.route("/info")
def info_index():
    return render_template("info/index.html")


@app.route("/info/<page>")
def info_page(page):
    return render_template(f"info/{page}.html")


@app.route("/places/<page>")
def place_page(page):
    return render_template(f"places/{page}.html")


if __name__ == "__main__":
    app.run(debug=True)