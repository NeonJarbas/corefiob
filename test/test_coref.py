import unittest

from corefiob import HeuristicParser

solver = HeuristicParser()


class TestHeuristicParser(unittest.TestCase):

    def test_gender(self):
        # test implicit gender word list
        # girl/boy/woman...
        self.assertEqual(solver.iob_tag("The girl said she would take the trash out"),
                         [('The', 'DET', 'B-ENTITY-FEMALE'),
                          ('girl', 'NOUN', 'I-ENTITY-FEMALE'),
                          ('said', 'VERB', 'O'),
                          ('she', 'PRON', 'B-COREF-FEMALE'),
                          ('would', 'AUX', 'O'),
                          ('take', 'VERB', 'O'),
                          ('the', 'DET', 'O'),
                          ('trash', 'NOUN', 'O'),
                          ('out', 'ADP', 'O')])

        # plural word
        self.assertEqual(solver.iob_tag("I have many friends. They are an important part of my life"),
                         [('I', 'PRON', 'O'),
                          ('have', 'VERB', 'O'),
                          ('many', 'ADJ', 'B-ENTITY-PLURAL'),
                          ('friends', 'NOUN', 'I-ENTITY-PLURAL'),
                          ('.', 'PUNCT', 'O'),
                          ('They', 'PRON', 'B-COREF-PLURAL'),
                          ('are', 'AUX', 'O'),
                          ('an', 'DET', 'O'),
                          ('important', 'ADJ', 'O'),
                          ('part', 'NOUN', 'O'),
                          ('of', 'ADP', 'O'),
                          ('my', 'PRON', 'O'),
                          ('life', 'NOUN', 'O')])

        # test 3 words joined and cast to male (only coref)
        self.assertEqual(solver.iob_tag(
            "George von Doomson is the best. His ideas are unique compared to Joe's"),
            [('George', 'PROPN', 'B-ENTITY-MALE'),
             ('von', 'PROPN', 'I-ENTITY-MALE'),
             ('Doomson', 'PROPN', 'I-ENTITY-MALE'),
             ('is', 'AUX', 'O'),
             ('the', 'DET', 'O'),
             ('best', 'ADJ', 'O'),
             ('.', 'PUNCT', 'O'),
             ('His', 'PRON', 'B-COREF-MALE'),
             ('ideas', 'NOUN', 'O'),
             ('are', 'AUX', 'O'),
             ('unique', 'ADJ', 'O'),
             ('compared', 'VERB', 'O'),
             ('to', 'ADP', 'O'),
             ('Joe', 'PROPN', 'O'),
             ("'s", 'PART', 'O')]
        )

    def test_neutral2inanimate(self):
        # "it" makes entities inanimate instead of neutral
        # test 2word - DET included
        self.assertEqual(solver.iob_tag("Here is the book now take it"),
                         [('Here', 'ADV', 'O'),
                          ('is', 'AUX', 'O'),
                          ('the', 'DET', 'B-ENTITY-INANIMATE'),
                          ('book', 'NOUN', 'I-ENTITY-INANIMATE'),
                          ('now', 'ADV', 'O'),
                          ('take', 'VERB', 'O'),
                          ('it', 'PRON', 'B-COREF-INANIMATE')])
        # test 3 words - DET + ADJ included
        self.assertEqual(solver.iob_tag("Here is the awesome machine now take it"),
                         [('Here', 'ADV', 'O'),
                          ('is', 'AUX', 'O'),
                          ('the', 'DET', 'B-ENTITY-INANIMATE'),
                          ('awesome', 'ADJ', 'I-ENTITY-INANIMATE'),
                          ('machine', 'NOUN', 'I-ENTITY-INANIMATE'),
                          ('now', 'ADV', 'O'),
                          ('take', 'VERB', 'O'),
                          ('it', 'PRON', 'B-COREF-INANIMATE')])

    def test_plural2inanimate(self):
        # "them" could also be a neutral or plural coref
        # some words are known to be inanimate, eg, iot stuff (lights) and animals (dog)
        self.assertEqual(solver.iob_tag("Turn on the lights and make them blue"),
                         [('Turn', 'VERB', 'O'),
                          ('on', 'ADP', 'O'),
                          ('the', 'DET', 'B-ENTITY-INANIMATE'),
                          ('lights', 'NOUN', 'I-ENTITY-INANIMATE'),
                          ('and', 'CCONJ', 'O'),
                          ('make', 'VERB', 'O'),
                          ('them', 'PRON', 'B-COREF-INANIMATE'),
                          ('blue', 'ADJ', 'O')])
        self.assertEqual(solver.iob_tag("I have many dogs, I love them"),
                         [('I', 'PRON', 'O'),
                          ('have', 'VERB', 'O'),
                          ('many', 'ADJ',  'B-ENTITY-INANIMATE'),
                          ('dogs', 'NOUN', 'I-ENTITY-INANIMATE'),
                          (',', 'PUNCT', 'O'),
                          ('I', 'PRON', 'O'),
                          ('love', 'VERB', 'O'),
                          ('them', 'PRON', 'B-COREF-INANIMATE')])

    def test_ignore_gender_mismatch(self):
        # coref is inanimate, ignore plural "neighbors"
        self.assertEqual(solver.iob_tag("My neighbors have a cat. It has a bushy tail"),
                         [('My', 'PRON', 'O'),
                          ('neighbors', 'NOUN', 'O'),
                          ('have', 'VERB', 'O'),
                          ('a', 'DET', 'B-ENTITY-INANIMATE'),
                          ('cat', 'NOUN', 'I-ENTITY-INANIMATE'),
                          ('.', 'PUNCT', 'O'),
                          ('It', 'PRON', 'B-COREF-INANIMATE'),
                          ('has', 'VERB', 'O'),
                          ('a', 'DET', 'O'),
                          ('bushy', 'ADJ', 'O'),
                          ('tail', 'NOUN', 'O')])
        # coref is inanimate, ignore female "the woman"
        self.assertEqual(solver.iob_tag("The coin was too far away for the woman to reach it"),
                         [('The', 'DET', 'B-ENTITY-INANIMATE'),
                          ('coin', 'NOUN', 'I-ENTITY-INANIMATE'),
                          ('was', 'AUX', 'O'),
                          ('too', 'ADV', 'O'),
                          ('far', 'ADV', 'O'),
                          ('away', 'ADV', 'O'),
                          ('for', 'ADP', 'O'),
                          ('the', 'DET', 'O'),
                          ('woman', 'NOUN', 'O'),
                          ('to', 'PART', 'O'),
                          ('reach', 'VERB', 'O'),
                          ('it', 'PRON', 'B-COREF-INANIMATE')])
        # coref is inanimate, ignore male "the boy"
        self.assertEqual(solver.iob_tag("The sign was too far away for the boy to read it"),
                         [('The', 'DET', 'B-ENTITY-INANIMATE'),
                          ('sign', 'NOUN', 'I-ENTITY-INANIMATE'),
                          ('was', 'AUX', 'O'),
                          ('too', 'ADV', 'O'),
                          ('far', 'ADV', 'O'),
                          ('away', 'ADV', 'O'),
                          ('for', 'ADP', 'O'),
                          ('the', 'DET', 'O'),
                          ('boy', 'NOUN', 'O'),
                          ('to', 'PART', 'O'),
                          ('read', 'VERB', 'O'),
                          ('it', 'PRON', 'B-COREF-INANIMATE')])
        # coref is inanimate, ignore neutral "best friend" and male "man"
        self.assertEqual(solver.iob_tag("Dog is man's best friend. It is always loyal"),
                         [('Dog', 'PROPN', 'B-ENTITY-INANIMATE'),
                          ('is', 'AUX', 'O'),
                          ('man', 'NOUN', 'O'),
                          ("'s", 'PART', 'O'),
                          ('best', 'ADJ', 'O'),
                          ('friend', 'NOUN', 'O'),
                          ('.', 'PUNCT', 'O'),
                          ('It', 'PRON', 'B-COREF-INANIMATE'),
                          ('is', 'AUX', 'O'),
                          ('always', 'ADV', 'O'),
                          ('loyal', 'ADJ', 'O')])
        # corefs are male, ignore neutral "the nation" and "a majority"
        self.assertEqual(solver.iob_tag(
            "I voted for Bob because he is clear about his values. His ideas represent a majority of the nation. He is better than Alice"),
            [('I', 'PRON', 'O'),
             ('voted', 'VERB', 'O'),
             ('for', 'ADP', 'O'),
             ('Bob', 'PROPN', 'B-ENTITY-MALE'),
             ('because', 'SCONJ', 'O'),
             ('he', 'PRON', 'B-COREF-MALE'),
             ('is', 'VERB', 'O'),
             ('clear', 'ADJ', 'O'),
             ('about', 'ADP', 'O'),
             ('his', 'PRON', 'B-COREF-MALE'),
             ('values', 'NOUN', 'O'),
             ('.', 'PUNCT', 'O'),
             ('His', 'PRON', 'B-COREF-MALE'),
             ('ideas', 'NOUN', 'O'),
             ('represent', 'VERB', 'O'),
             ('a', 'DET', 'O'),
             ('majority', 'NOUN', 'O'),
             ('of', 'ADP', 'O'),
             ('the', 'DET', 'O'),
             ('nation', 'NOUN', 'O'),
             ('.', 'PUNCT', 'O'),
             ('He', 'PRON', 'B-COREF-MALE'),
             ('is', 'AUX', 'O'),
             ('better', 'ADJ', 'O'),
             ('than', 'SCONJ', 'O'),
             ('Alice', 'PROPN', 'O')])
        # coref is male, ignore "top candidates" and "the elections"
        self.assertEqual(solver.iob_tag(
            "Jack Glass is one of the top candidates in the elections. His ideas are unique compared to Joe's"),
            [('Jack', 'PROPN', 'B-ENTITY-MALE'),
             ('Glass', 'PROPN', 'I-ENTITY-MALE'),
             ('is', 'AUX', 'O'),
             ('one', 'NUM', 'O'),
             ('of', 'ADP', 'O'),
             ('the', 'DET', 'O'),
             ('top', 'ADJ', 'O'),
             ('candidates', 'NOUN', 'O'),
             ('in', 'ADP', 'O'),
             ('the', 'DET', 'O'),
             ('elections', 'NOUN', 'O'),
             ('.', 'PUNCT', 'O'),
             ('His', 'PRON', 'B-COREF-MALE'),
             ('ideas', 'NOUN', 'O'),
             ('are', 'AUX', 'O'),
             ('unique', 'ADJ', 'O'),
             ('compared', 'VERB', 'O'),
             ('to', 'ADP', 'O'),
             ('Joe', 'PROPN', 'O'),
             ("'s", 'PART', 'O')])
        # coref is plural, ignore neutral "the world"
        self.assertEqual(solver.iob_tag(
            "Leaders around the world say they stand for peace"),
            [('Leaders', 'NOUN', 'B-ENTITY-PLURAL'),
             ('around', 'ADP', 'O'),
             ('the', 'DET', 'O'),
             ('world', 'NOUN', 'O'),
             ('say', 'VERB', 'O'),
             ('they', 'PRON', 'B-COREF-PLURAL'),
             ('stand', 'VERB', 'O'),
             ('for', 'ADP', 'O'),
             ('peace', 'NOUN', 'O')])

    def test_multiple_corefs(self):
        # plural + inanimate
        # they is cast neutral -> plural
        # puppy is cast neutral -> inanimate
        self.assertEqual(solver.iob_tag(
            "My neighbours just adopted a puppy. They care for it like a baby"),
            [('My', 'PRON', 'B-ENTITY-PLURAL'),
             ('neighbours', 'NOUN', 'I-ENTITY-PLURAL'),
             ('just', 'ADV', 'O'),
             ('adopted', 'VERB', 'O'),
             ('a', 'DET', 'B-ENTITY-INANIMATE'),
             ('puppy', 'NOUN', 'I-ENTITY-INANIMATE'),
             ('.', 'PUNCT', 'O'),
             ('They', 'PRON', 'B-COREF-PLURAL'),
             ('care', 'VERB', 'O'),
             ('for', 'ADP', 'O'),
             ('it', 'PRON', 'B-COREF-INANIMATE'),
             ('like', 'ADP', 'O'),
             ('a', 'DET', 'O'),
             ('baby', 'NOUN', 'O')])
        # plural + male
        # they is cast neutral -> plural
        self.assertEqual(solver.iob_tag(
            "Members voted for John because they see him as a good leader"),
            [('Members', 'NOUN', 'B-ENTITY-PLURAL'),
             ('voted', 'VERB', 'O'),
             ('for', 'ADP', 'O'),
             ('John', 'PROPN', 'B-ENTITY-MALE'),
             ('because', 'SCONJ', 'O'),
             ('they', 'PRON', 'B-COREF-PLURAL'),
             ('see', 'VERB', 'O'),
             ('him', 'PRON', 'B-COREF-MALE'),
             ('as', 'ADP', 'O'),
             ('a', 'DET', 'O'),
             ('good', 'ADJ', 'O'),
             ('leader', 'NOUN', 'O')])
