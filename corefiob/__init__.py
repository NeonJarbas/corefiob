from nltk import pos_tag
from quebra_frases import word_tokenize
import spacy
import enum
from corefiob.lang import *

# TODO this is WIP! postagger will be configurable as it is the most important piece of this pipeline
nlp = spacy.load("en_core_web_sm")


# different langs may use different subsets only
# eg, portuguese does not have inanimate or neutral
#     english does not have plural_(fe)male
class CorefIOB(str, enum.Enum):
    COREF_MALE = "B-COREF-MALE"
    COREF_FEMALE = "B-COREF-FEMALE"
    COREF_PLURAL = "B-COREF-PLURAL"
    COREF_PLURAL_MALE = "B-COREF-PLURAL-MALE"
    COREF_PLURAL_FEMALE = "B-COREF-PLURAL-FEMALE"
    COREF_NEUTRAL = "B-COREF-NEUTRAL"
    COREF_INANIMATE = "B-COREF-INANIMATE"

    ENTITY_MALE = "B-ENTITY-MALE"
    ENTITY_FEMALE = "B-ENTITY-FEMALE"
    ENTITY_PLURAL = "B-ENTITY-PLURAL"
    ENTITY_PLURAL_MALE = "B-ENTITY-PLURAL-MALE"
    ENTITY_PLURAL_FEMALE = "B-ENTITY-PLURAL-FEMALE"
    ENTITY_NEUTRAL = "B-ENTITY-NEUTRAL"
    ENTITY_INANIMATE = "B-ENTITY-INANIMATE"

    ENTITY_MALE_I = "I-ENTITY-MALE"
    ENTITY_FEMALE_I = "I-ENTITY-FEMALE"
    ENTITY_PLURAL_I = "I-ENTITY-PLURAL"
    ENTITY_PLURAL_MALE_I = "I-ENTITY-PLURAL-MALE"
    ENTITY_PLURAL_FEMALE_I = "I-ENTITY-PLURAL-FEMALE"
    ENTITY_NEUTRAL_I = "I-ENTITY-NEUTRAL"
    ENTITY_INANIMATE_I = "I-ENTITY-INANIMATE"


class DummyParser:
    def tokenize(self, sentence):
        return word_tokenize(sentence)

    def pos_tag(self, tokens):
        if isinstance(tokens, str):
            # tokens = self.tokenize(tokens)
            doc = nlp(tokens)
            return [(token.text, token.pos_) for token in doc]
        return pos_tag(tokens, tagset="universal")

    def iob_tag(self, postagged_toks):
        if isinstance(postagged_toks, str):
            postagged_toks = self.pos_tag(postagged_toks)
        iob = [(token, tag, "O") for (token, tag) in postagged_toks]
        return iob


class HeuristicParser(DummyParser):
    def __init__(self, lang="en"):
        self.lang = lang
        self.JOINER_TOKENS = JOINER_TOKENS.get(self.lang, [])
        self.PREV_TOKENS = PREV_TOKENS.get(self.lang, [])
        self.MALE_TOKENS = MALE_TOKENS.get(self.lang, [])
        self.FEMALE_TOKENS = FEMALE_TOKENS.get(self.lang, [])
        self.INANIMATE_TOKENS = INANIMATE_TOKENS.get(self.lang, [])
        self.NEUTRAL_COREF_TOKENS = NEUTRAL_COREF_TOKENS.get(self.lang, [])
        self.MALE_COREF_TOKENS = MALE_COREF_TOKENS.get(self.lang, [])
        self.FEMALE_COREF_TOKENS = FEMALE_COREF_TOKENS.get(self.lang, [])
        self.INANIMATE_COREF_TOKENS = INANIMATE_COREF_TOKENS.get(self.lang, [])
        self.HUMAN_TOKENS = HUMAN_TOKENS.get(self.lang, [])

    def iob_tag(self, postagged_toks):
        if isinstance(postagged_toks, str):
            postagged_toks = self.pos_tag(postagged_toks)
        iob = [(token, tag, "O") for (token, tag) in postagged_toks]
        prons = {}
        ents = {}

        valid_helper_tags = ["ADJ", "DET", "NUM"]
        valid_noun_tags = ["NOUN", "PROPN"]

        # first pass - tag entities
        # print("### FIRST PASS - entity candidates")
        def tag_entities():
            for idx, (token, tag, previob) in enumerate(iob):
                # the last token can never be a valid coreference entity
                if idx == len(iob) - 1:
                    break
                is_plural = token.endswith("s")
                clean_token = token.lower().rstrip("s ")

                prev = iob[idx - 1] if idx > 0 else ("", "", "")
                prev2 = iob[idx - 2] if idx > 1 else ("", "", "")
                nxt = iob[idx + 1] if idx + 1 < len(iob) else ("", "", "")

                is_noun = tag in valid_noun_tags and prev[0] not in self.JOINER_TOKENS
                # plurals of the format NOUN and NOUN
                is_conjunction = token in self.JOINER_TOKENS and \
                                 prev[1] in valid_noun_tags and \
                                 nxt[1] in valid_noun_tags
                # nouns of the form "NOUN of NOUN" or "NOUN of the ADJ NOUN"
                is_adp = tag == "ADP" and "ENTITY" in prev[2] and nxt[1] in valid_noun_tags

                if is_adp:
                    newtag = prev[2].replace("B-", "I-")
                    iob[idx] = (token, tag, newtag)
                    iob[idx + 1] = (nxt[0], nxt[1], newtag)
                    ents[idx] = ents[idx + 1] = newtag

                elif is_conjunction:
                    iob[idx - 1] = (prev[0], prev[1], CorefIOB.ENTITY_PLURAL)
                    iob[idx] = (token, tag, CorefIOB.ENTITY_PLURAL_I)
                    iob[idx + 1] = (nxt[0], nxt[1], CorefIOB.ENTITY_PLURAL_I)

                    ents[idx - 1] = CorefIOB.ENTITY_PLURAL
                    ents[idx] = CorefIOB.ENTITY_PLURAL_I
                    ents[idx + 1] = CorefIOB.ENTITY_PLURAL_I
                elif is_noun:
                    first = True
                    # join multi word nouns
                    if prev[1] == tag:
                        t = prev[2].replace("B-", "I-")
                        iob[idx] = (token, tag, t)
                        ents[idx] = t
                        continue

                    # include adjectives and determinants
                    if prev[1] in valid_helper_tags or \
                            prev[0].lower() in self.PREV_TOKENS:
                        first = False

                    # implicitly gendered words, eg sister/brother mother/father
                    if clean_token in self.FEMALE_TOKENS:
                        if first:
                            iob[idx] = (token, tag, CorefIOB.ENTITY_FEMALE)
                            ents[idx] = CorefIOB.ENTITY_FEMALE
                        else:
                            iob[idx - 1] = (prev[0], prev[1], CorefIOB.ENTITY_FEMALE)
                            iob[idx] = (token, tag, CorefIOB.ENTITY_FEMALE_I)
                            ents[idx - 1] = CorefIOB.ENTITY_FEMALE
                            ents[idx] = CorefIOB.ENTITY_FEMALE_I
                    elif clean_token in self.MALE_TOKENS:
                        if first:
                            iob[idx] = (token, tag, CorefIOB.ENTITY_MALE)
                            ents[idx] = CorefIOB.ENTITY_MALE
                        else:
                            iob[idx - 1] = (prev[0], prev[1], CorefIOB.ENTITY_MALE)
                            iob[idx] = (token, tag, CorefIOB.ENTITY_MALE_I)
                            ents[idx - 1] = CorefIOB.ENTITY_MALE
                            ents[idx] = CorefIOB.ENTITY_MALE_I

                    # known reference inanimate token, eg, iot device types "light"
                    elif clean_token in self.INANIMATE_TOKENS:
                        if first:
                            iob[idx] = (token, tag, CorefIOB.ENTITY_INANIMATE)
                            ents[idx] = CorefIOB.ENTITY_INANIMATE
                        elif prev2[1] in valid_helper_tags:
                            iob[idx - 2] = (prev2[0], prev2[1], CorefIOB.ENTITY_INANIMATE)
                            iob[idx - 1] = (prev[0], prev[1], CorefIOB.ENTITY_INANIMATE_I)
                            iob[idx] = (token, tag, CorefIOB.ENTITY_INANIMATE_I)

                            ents[idx - 2] = CorefIOB.ENTITY_INANIMATE
                            ents[idx - 1] = CorefIOB.ENTITY_INANIMATE_I
                            ents[idx] = CorefIOB.ENTITY_INANIMATE_I
                        else:
                            iob[idx - 1] = (prev[0], prev[1], CorefIOB.ENTITY_INANIMATE)
                            iob[idx] = (token, tag, CorefIOB.ENTITY_INANIMATE_I)

                            ents[idx - 1] = CorefIOB.ENTITY_INANIMATE
                            ents[idx] = CorefIOB.ENTITY_INANIMATE_I

                    # ends with "s" its a plural noun
                    elif is_plural:
                        if first:
                            iob[idx] = (token, tag, CorefIOB.ENTITY_PLURAL)
                            ents[idx] = CorefIOB.ENTITY_PLURAL
                        else:
                            iob[idx - 1] = (prev[0], prev[1], CorefIOB.ENTITY_PLURAL)
                            iob[idx] = (token, tag, CorefIOB.ENTITY_PLURAL_I)
                            ents[idx - 1] = CorefIOB.ENTITY_PLURAL
                            ents[idx] = CorefIOB.ENTITY_PLURAL_I

                    # if its a unknown noun, its a neutral entity
                    else:
                        if first:
                            iob[idx] = (token, tag, CorefIOB.ENTITY_NEUTRAL)
                            ents[idx] = CorefIOB.ENTITY_NEUTRAL
                        elif prev2[1] in valid_helper_tags:
                            iob[idx - 2] = (prev2[0], prev2[1], CorefIOB.ENTITY_NEUTRAL)
                            iob[idx - 1] = (prev[0], prev[1], CorefIOB.ENTITY_NEUTRAL_I)
                            iob[idx] = (token, tag, CorefIOB.ENTITY_NEUTRAL_I)

                            ents[idx - 2] = CorefIOB.ENTITY_NEUTRAL
                            ents[idx - 1] = CorefIOB.ENTITY_NEUTRAL_I
                            ents[idx] = CorefIOB.ENTITY_NEUTRAL_I
                        else:
                            iob[idx - 1] = (prev[0], prev[1], CorefIOB.ENTITY_NEUTRAL)
                            iob[idx] = (token, tag, CorefIOB.ENTITY_NEUTRAL_I)

                            ents[idx - 1] = CorefIOB.ENTITY_NEUTRAL
                            ents[idx] = CorefIOB.ENTITY_NEUTRAL_I

        tag_entities()

        # second pass - tag pronouns
        # print("### SECOND PASS - coref candidates")
        def tag_prons():
            for idx, (token, tag, _) in enumerate(iob):
                clean_token = token.lower().strip()
                if clean_token in self.INANIMATE_COREF_TOKENS:
                    iob[idx] = (token, tag, CorefIOB.COREF_INANIMATE)
                    prons[idx] = CorefIOB.COREF_INANIMATE
                elif clean_token in self.FEMALE_COREF_TOKENS:
                    iob[idx] = (token, tag, CorefIOB.COREF_FEMALE)
                    prons[idx] = CorefIOB.COREF_FEMALE
                elif clean_token in self.MALE_COREF_TOKENS:
                    iob[idx] = (token, tag, CorefIOB.COREF_MALE)
                    prons[idx] = CorefIOB.COREF_MALE
                elif clean_token in self.NEUTRAL_COREF_TOKENS:
                    has_plural = any(v == CorefIOB.ENTITY_PLURAL for e, v in ents.items())
                    if has_plural:
                        iob[idx] = (token, tag, CorefIOB.COREF_PLURAL)
                        prons[idx] = CorefIOB.COREF_PLURAL
                    else:
                        iob[idx] = (token, tag, CorefIOB.COREF_NEUTRAL)
                        prons[idx] = CorefIOB.COREF_NEUTRAL

        tag_prons()

        # print("### THIRD PASS - disambiguation")
        # untag entities that can not possibly corefer
        # if there is no pronoun after the entity, then nothing can corefer to it
        bad_ents = [idx for idx in ents.keys() if not any(i > idx for i in prons.keys())]
        #if bad_ents:
        #    print("  - impossible corefs", bad_ents)

        # disambiguate
        def disambiguate():
            for ent, tag in ents.items():
                if ent in bad_ents:
                    continue
                possible_coref = {k: v for k, v in prons.items() if k > ent}
                token, ptag, _ = iob[ent]
                prevtoken, prevptag, prevtag = iob[ent - 1]
                prev2 = iob[ent - 2] if ent > 1 else ("", "", "")
                clean_token = token.lower().rstrip("s ")

                neutral_corefs = any(t.endswith("NEUTRAL") for t in possible_coref.values())
                inanimate_corefs = any(t.endswith("INANIMATE") for t in possible_coref.values())
                female_corefs = {k: t for k, t in possible_coref.items() if t.endswith("-FEMALE")}
                male_corefs = {k: t for k, t in possible_coref.items() if t.endswith("-MALE")}

                # disambiguate neutral
                if tag.endswith("ENTITY-NEUTRAL") and ptag in valid_noun_tags:
                    is_human = clean_token in self.HUMAN_TOKENS or ptag in ["PROPN"]

                    # disambiguate neutral/inanimate
                    if not neutral_corefs and inanimate_corefs and not is_human:
                        if tag.startswith("I-") or prevtag in [tag, CorefIOB.ENTITY_INANIMATE,
                                                               CorefIOB.ENTITY_INANIMATE_I]:
                            tag = CorefIOB.ENTITY_INANIMATE_I
                            if prev2[1] in valid_helper_tags:
                                iob[ent - 2] = (prev2[0], prev2[1], CorefIOB.ENTITY_INANIMATE)
                                iob[ent - 1] = (prevtoken, prevptag, CorefIOB.ENTITY_INANIMATE_I)
                                ents[ent - 2] = CorefIOB.ENTITY_INANIMATE
                                ents[ent - 1] = CorefIOB.ENTITY_INANIMATE_I
                            else:
                                iob[ent - 1] = (prevtoken, prevptag, CorefIOB.ENTITY_INANIMATE)
                                ents[ent - 1] = CorefIOB.ENTITY_INANIMATE
                            # print("  - replacing NEUTRAL -> INANIMATE ", iob[ent - 1])
                        else:
                            tag = CorefIOB.ENTITY_INANIMATE
                        iob[ent] = (token, ptag, tag)
                        ents[ent] = tag
                        # print("  - replacing NEUTRAL -> INANIMATE ", iob[ent])

                    elif is_human:
                        if male_corefs and not female_corefs:
                            if tag.startswith("I-") or prevtag in [tag, CorefIOB.ENTITY_MALE, CorefIOB.ENTITY_MALE_I]:
                                tag = CorefIOB.ENTITY_MALE_I
                                if prevtag not in [CorefIOB.ENTITY_MALE, CorefIOB.ENTITY_MALE_I]:
                                    iob[ent - 1] = (prevtoken, prevptag, CorefIOB.ENTITY_MALE)
                                    ents[ent - 1] = CorefIOB.ENTITY_MALE
                                    # print("  - replacing NEUTRAL -> MALE ", iob[ent - 1])
                            else:
                                tag = CorefIOB.ENTITY_MALE
                            iob[ent] = (token, ptag, tag)
                            ents[ent] = tag
                            # print("  - replacing NEUTRAL -> MALE ", iob[ent])
                        elif female_corefs and not male_corefs:
                            if tag.startswith("I-") or prevtag in [tag, CorefIOB.ENTITY_MALE, CorefIOB.ENTITY_MALE_I]:
                                tag = CorefIOB.ENTITY_FEMALE_I
                                iob[ent - 1] = (prevtoken, prevptag, CorefIOB.ENTITY_FEMALE)
                                ents[ent - 1] = CorefIOB.ENTITY_FEMALE
                                # print("  - replacing NEUTRAL -> FEMALE ", iob[ent - 1])
                            else:
                                tag = CorefIOB.ENTITY_FEMALE
                            iob[ent] = (token, ptag, tag)
                            ents[ent] = tag
                            # print("  - replacing NEUTRAL -> FEMALE ", iob[ent])

                    if (prevptag in valid_helper_tags or prevptag == "ADP") and \
                            (prev2[1] in valid_helper_tags or prev2[1] in valid_noun_tags):
                        iob[ent - 1] = (prevtoken, prevptag, tag.replace("B-", "I-"))
                        ents[ent - 1] = tag.replace("B-", "I-")
                        iob[ent] = (token, ptag, tag.replace("B-", "I-"))
                        ents[ent] = tag.replace("B-", "I-")

        disambiguate()

        # untag mismatched entities with coref gender
        def filter_mismatches():
            for ent, tag in ents.items():
                if ent in bad_ents:
                    continue

                possible_coref = {k: v for k, v in prons.items() if k > ent}
                token, ptag, _ = iob[ent]
                prevtoken, prevptag, _ = iob[ent - 1]
                clean_token = token.lower().rstrip("s ")

                neutral_corefs = any(t.endswith("NEUTRAL") for t in possible_coref.values())
                inanimate_corefs = any(t.endswith("INANIMATE") for t in possible_coref.values())
                plural_corefs = any(t.endswith("PLURAL") for t in possible_coref.values())

                female_corefs = {k: t for k, t in possible_coref.items() if t.endswith("-FEMALE")}
                male_corefs = {k: t for k, t in possible_coref.items() if t.endswith("-MALE")}

                # untag plural entities if there are no plural corefs
                if tag.endswith("ENTITY-PLURAL") and not plural_corefs:
                    # print("  - impossible plural ", ent)
                    bad_ents.append(ent)
                # untag male entities if there are no male corefs
                elif tag.endswith("ENTITY-MALE") and not male_corefs:
                    # print("  - impossible male ", ent)
                    bad_ents.append(ent)
                # untag female entities if there are no female corefs
                elif tag.endswith("ENTITY-FEMALE") and not female_corefs:
                    # print("  - impossible female ", ent)
                    bad_ents.append(ent)
                # untag neutral entities
                # if there are no neutral corefs AND there are inanimate corefs
                elif tag.endswith("ENTITY-NEUTRAL") and \
                        not neutral_corefs and \
                        (inanimate_corefs or male_corefs or
                         female_corefs or plural_corefs):
                    # print("  - impossible neutral ", ent)
                    bad_ents.append(ent)

        filter_mismatches()

        # print("### FOURTH PASS - filter invalid corefs")
        # untag impossible entity corefs
        def untag_bad_candidates():
            for e in bad_ents:
                if e in ents:
                    # print("  - impossible coref ", e)
                    ents.pop(e)
                token, ptag, _ = iob[e]
                iob[e] = (token, ptag, "O")

        untag_bad_candidates()
        return iob
