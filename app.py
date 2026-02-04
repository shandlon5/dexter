from flask import Flask, render_template, request, redirect, url_for
import os

app = Flask(__name__)

# Ensure the people folder exists
people_folder = 'people'
if not os.path.exists(people_folder):
    os.makedirs(people_folder)

@app.route('/')
def index():
    return render_template('form.html')

@app.route('/add_character', methods=['POST'])
def add_character():
    name = request.form['name']
    role = request.form['role']
    bio = request.form['bio']
    image_file = request.form['image_file']
    
    # Create the HTML content
    html_content = f"""<!DOCTYPE html>
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
        <img src="{image_file}" alt="{name}" class="profile-img">
        <h1>{name}</h1>
        <div class="bio">
            <p>{bio}</p>
        </div>
        <div>
            <h3>Notes:</h3>
            <textarea placeholder="Add your notes here..." rows="4" cols="50"></textarea>
            <h3></h3>
            <a href="{url_for('index')}">Back to DM Tools</a>
        </div>
    </div>
</body>
</html>"""

    # Save the HTML content to a file
    filename = os.path.join(people_folder, f"{name.replace(' ', '_')}.html")
    
    with open(filename, 'w') as file:
        file.write(html_content)

    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
