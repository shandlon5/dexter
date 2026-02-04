import os

# Path to the folder where NPC HTML files will be stored
people_folder = 'people'

def add_character():
    # Prompt for character details
    name = input("Enter character name: ")
    role = input("Enter character role: ")
    bio = input("Enter character bio: ")
    image_file = input("Enter image file name (e.g., 'character_image.jpg'): ")

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
            <a href="phonebook.html">Back to Phonebook</a>
        </div>
    </div>
</body>
</html>"""

    # Save the HTML content to a file
    # Replace spaces with underscores for the file name
    filename = os.path.join(people_folder, f"{name.replace(' ', '_')}.html")
    
    with open(filename, 'w') as file:
        file.write(html_content)

    print(f"Character {name} added successfully! File created: {filename}")

# Ensure the people folder exists
if not os.path.exists(people_folder):
    os.makedirs(people_folder)

# Run the script
if __name__ == '__main__':
    add_character()