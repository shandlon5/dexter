from flask import Flask, render_template, request, redirect, url_for, abort
import json
import os
import re

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
PEOPLE_DIR = os.path.join(BASE_DIR, "people")
CHAR_FILE = os.path.join(DATA_DIR, "characters.json")

PLACEHOLDER_IMAGE = "placeholder.jpg"


def ensure_dirs():
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(PEOPLE_DIR, exist_ok=True)
    if not os.path.exists(CHAR_FILE):
        with open(CHAR_FILE, "w", encoding="utf-8") as f:
            json.dump([], f, indent=2, ensure_ascii=False)


def load_characters():
    with open(CHAR_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_characters(chars):
    with open(CHAR_FILE, "w", encoding="utf-8") as f:
        json.dump(chars, f, indent=2, ensure_ascii=False)


def slugify(name: str) -> str:
    s = name.strip().lower()
    s = re.sub(r"[^a-z0-9]+", "_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    return s or "character"


def npc_html_template(name: str, bio: str, image_filename: str) -> str:
    return f"""<!DOCTYPE html>
<html>
<head>
    <title>{name}</title>
    <link rel="stylesheet" href="style.css">
    <style>
        .profile-img {{
            width: 150px;
            height: auto;
            border-radius: 8px;
            margin-bottom: 20px;
        }}
        .bio {{
            font-size: 1em;
            color: #333;
        }}
    </style>
</head>
<body>
    <div class="container">
        <img src="{image_filename}" alt="{name}" class="profile-img">
        <h1>{name}</h1>
        <div class="bio">
            <p>{bio}</p>
        </div>
        <div>
            <h3>Notes:</h3>
            <textarea placeholder="Add your notes here..." rows="4" cols="50"></textarea>
            <h3></h3>
            <a href="/phonebook">Back to Phonebook</a>
        </div>
    </div>
</body>
</html>
"""


def create_npc_page(char):
    filename = f"{char['id']}.html"
    path = os.path.join(PEOPLE_DIR, filename)
    if os.path.exists(path):
        return
    html = npc_html_template(char["name"], char["bio"], char["image"])
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)


ensure_dirs()


@app.route("/")
def index():
    print("ENDPOINTS:", sorted(app.view_functions.keys()))
    return render_template("index.html")



@app.route("/dm")
def dm_home():
    return render_template("dm_home.html")


@app.route("/dm/add", methods=["GET", "POST"])
def dm_add_character():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        role = request.form.get("role", "").strip()
        bio = request.form.get("bio", "").strip()

        if not name or not role or not bio:
            return render_template("dm_add.html", error="Fill out name, role, and bio.")

        chars = load_characters()

        new_id = slugify(name)
        existing_ids = {c["id"] for c in chars}
        if new_id in existing_ids:
            i = 2
            while f"{new_id}_{i}" in existing_ids:
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

        chars.append(new_char)
        save_characters(chars)
        create_npc_page(new_char)

        return redirect(url_for("dm_home"))

    return render_template("dm_add.html", error=None)


@app.route("/dm/toggles", methods=["GET", "POST"])
def dm_toggles():
    chars = load_characters()

    if request.method == "POST":
        available_ids = set(request.form.getlist("available"))

        for c in chars:
            c["available"] = c["id"] in available_ids

        save_characters(chars)
        return redirect(url_for("dm_toggles"))

    return render_template("dm_toggles.html", characters=chars)


@app.route("/phonebook")
def phonebook():
    chars = load_characters()
    visible = [c for c in chars if c.get("available")]
    return render_template("phonebook.html", characters=visible)


@app.route("/character/<char_id>")
def character_page(char_id):
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




