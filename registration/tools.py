import random
from django.contrib.auth.models import User

objects_list = [
    "pear", "plum", "kiwi", "fig", "lime", "mango", "peach", "date", "grape", "melon", 
    "mint", "iris", "fern", "jade", "zest", "opal", "ruby", "gold", "silk", "amber", 
    "teal", "dove", "mist", "dusk", "dawn", "tide", "frost", "beam", "coil", "moss", 
    "bark", "wing", "leaf", "clay", "salt", "sand", "wave", "pearl", "coral", "shell", 
    "star", "moon", "sun", "sky", "cloud", "rain", "wind", "fire", "snow", "ice", 
    "stone", "earth", "tree", "river", "lake", "ocean", "pond", "brook", "spring", 
    "stream", "creek", "mountain", "valley", "canyon", "desert", "meadow"
]

verbs_list = [
    "jumping", "singing", "playing", "swimming", "reading", "walking", "talking", 
    "cooking", "running", "skipping", "leaping", "kicking", "flipping", "spinning", 
    "diving", "racing", "darting", "climbing", "sprinting", "crawling", "swaying", 
    "pushing", "pulling", "tossing", "throwing", "catching", "hopping", "skipping", 
    "jogging", "pacing", "bolting", "chasing", "gliding", "sliding", "surfing", 
    "skating", "rolling", "swinging", "shooting", "bouncing", "floating", "drifting", 
    "wandering", "searching", "sneaking", "digging", "lifting", "grabbing", "hugging", 
    "kissing", "bowing", "waving", "nodding", "pointing", "flexing", "kicking", "punching", 
    "slapping"
]

def generate_username():
    random.shuffle(verbs_list)
    random.shuffle(objects_list)
    
    while True:
        username = f"{verbs_list.pop()}{objects_list.pop()}"
        
        if not User.objects.filter(username=username).exists():
            return username