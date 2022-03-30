PLURAL_ENDINGS = {"en": ["s"], "pt": ["s"]}
JOINER_TOKENS = {"en": ["and"], "pt": ["e"]}
PREV_TOKENS = {"en": ["my", "the"], "pt": ["o", "a", "os", "as"]}

MALE_COREF_TOKENS = {"en": ["he", "him", "his"]}
FEMALE_COREF_TOKENS = {"en": ["she", "her", "hers"]}
INANIMATE_COREF_TOKENS = {"en": ["it", "them"]}
NEUTRAL_COREF_TOKENS = {"en": ["they", "them", "their", "theirs"]}
PLURAL_COREF_TOKENS = {"en": ["they", "them", "their", "theirs"]}
PLURAL_MALE_COREF_TOKENS = {"en": [], "pt": ["eles"]}
PLURAL_FEMALE_COREF_TOKENS = {"en": [], "pt": ["elas"]}

HUMAN_TOKENS = {
    "en": ["cousin", "family", "friend", "neighbour", "person"]
}
MALE_TOKENS = {
    "en": ["boy", "man", "men", "male",
           "father", "grandfather", "brother", "uncle", "son", "dad"]
}
FEMALE_TOKENS = {
    "en": ["girl", "woman", "women", "female",
           "mother", "grandmother", "sister", "aunt", "daughter", "mom"]
}
INANIMATE_TOKENS = {
    "en": ["cat", "dog", "bird", "lizard", "turtle", "spider", "snake", "fish",
           "light", "tv", "computer", "door", "window", "music"]
}