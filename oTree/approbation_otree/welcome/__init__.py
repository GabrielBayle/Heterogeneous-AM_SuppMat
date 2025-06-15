from otree.api import *

from settings import LANGUAGE_CODE

if LANGUAGE_CODE == "en":
    from .lexicon_en import Lexicon
else:
    from .lexicon_fr import Lexicon

doc = """
Ecran d'accueil avec consentement.
"""


class C(BaseConstants):
    NAME_IN_URL = 'Welcome'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 1


class Subsession(BaseSubsession):
    pass


def creating_session(subsession: Subsession):
    subsession.session.fill_auto = subsession.session.config.get("fill_auto", False)


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    pass


# PAGES
class Welcome(Page):
    @staticmethod
    def vars_for_template(player):
        return dict(
            lexicon=Lexicon
        )

    @staticmethod
    def js_vars(player: Player):
        return dict(
            fill_auto=player.session.config.get("fill_auto", False)
        )


page_sequence = [Welcome]
