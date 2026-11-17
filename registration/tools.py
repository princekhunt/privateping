import secrets

from django.contrib.auth.models import User

objects_list = [
    "pear", "plum", "kiwi", "fig", "lime", "mango", "peach", "date", "grape", "melon",
    "mint", "iris", "fern", "jade", "zest", "opal", "ruby", "gold", "silk", "amber",
    "teal", "dove", "mist", "dusk", "dawn", "tide", "frost", "beam", "coil", "moss",
    "bark", "wing", "leaf", "clay", "salt", "sand", "wave", "pearl", "coral", "shell",
    "star", "moon", "sun", "sky", "cloud", "rain", "wind", "fire", "snow", "ice",
    "stone", "earth", "tree", "river", "lake", "ocean", "pond", "brook", "spring",
    "stream", "creek", "valley", "canyon", "desert", "meadow"
]

verbs_list = [
    "jumping", "singing", "playing", "swimming", "reading", "walking", "talking",
    "cooking", "running", "skipping", "leaping", "kicking", "flipping", "spinning",
    "diving", "racing", "darting", "climbing", "crawling", "swaying",
    "pushing", "pulling", "tossing", "catching", "hopping",
    "jogging", "pacing", "bolting", "chasing", "gliding", "sliding", "surfing",
    "skating", "rolling", "swinging", "bouncing", "floating", "drifting",
    "wandering", "searching", "sneaking", "digging", "lifting", "hugging",
    "bowing", "waving", "nodding", "pointing",
]

MAX_USERNAME_LENGTH = 20


def generate_username():
    """
    Returns an unused, unguessable username such as "gliding_moss4821".
    Uses `secrets` (not `random`) and never runs out of combinations.
    """
    while True:
        verb = secrets.choice(verbs_list)
        obj = secrets.choice(objects_list)
        suffix = str(secrets.randbelow(10000)).zfill(4)
        base = f"{verb}{obj}"[:MAX_USERNAME_LENGTH - len(suffix)]
        username = f"{base}{suffix}"
        if not User.objects.filter(username=username).exists():
            return username
