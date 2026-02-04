class Character:
    def __init__(self, name, role):
        self.name = name
        self.role = role
        self.is_available = False  # By default, not avail

    def mark_available(self):
        self.is_available = True

    def mark_unavailable(self):
        self.is_available = False



class CharacterManager:
    def __init__(self):
        self.characters = []
    
    def add_character(self, character):
        self.characters.append(character)

    def get_available_characters(self):
        return [char for char in self.characters if char.is_available]

    def mark_character_available(self, name):
        for char in self.characters:
            if char.name == name:
                char.mark_available()
                break


# Initialize the CharacterManager
manager = CharacterManager()

# Create and add Characters
characters = [
    Character("Luiz Adams", "Deputy"),
    Character("Zara and Emil Allsup", "Gas Station Market Owners"),
    Character("Hal Bogle", "Rich Guy"),
    Character("Marcus Hensley", "Colonel"),
    Character("Carrol Higgins", "Comic Book Store Owner"),
    Character("Molly Hopper", "Sheriff"),
    Character("Dorris Macintosh", "Librarian"),
    Character("Darnell Mantell", "Science Teacher"),
    Character("Vic Pollard", "Mechanic")
]

# Add each Character to the manager
for char in characters:
    manager.add_Character(char)

# Mark the Colonel as not available
for char in manager.characters:
    if char.name == "Marcus Hensley":
        char.mark_unavailable()