import random

from otree.api import *

doc = """
Final app - Tirage des parties
"""


class C(BaseConstants):
    NAME_IN_URL = 'apf'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 1


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    paid_part = models.IntegerField()
    comments = models.LongStringField()


# METHODS --------------------------------------------------------------------------------------------------------------
def vars_for_admin_report(subsession: Subsession):
    infos = list()
    for p in subsession.get_players():
        infos.append(
            dict(
                label=p.participant.label,
                part_1=cu(0) if not "approbation_publicgoods" in p.participant.vars.keys() else
                p.participant.vars["approbation_publicgoods"]["payoff"],
                part_2=cu(0) if not "targetNLE" in p.participant.vars.keys() else
                p.participant.vars["targetNLE"]["payoff"],
                part_3=cu(0) if not "inequalityAversionTest" in p.participant.vars.keys() else
                p.participant.vars["inequalityAversionTest"]["payoff"],
                paid_part=p.field_maybe_none("paid_round"),
                payoff=p.participant.payoff
            )
        )
    return dict(infos=infos)

def compute_final_payoff(player: Player):
    player.paid_part = random.randint(2, 3)

    player.payoff = player.participant.vars["approbation_publicgoods"]["payoff"]
    if player.paid_part == 2:
        player.payoff += player.participant.vars["targetNLE"]["payoff"]
    else:
        player.payoff += player.participant.vars["inequalityAversionTest"]["payoff"]

    player.participant.payoff = player.payoff

    txt_final = f"C'est la partie {player.paid_part} qui a été sélectionnée pour être rémunérée, en plus de la " \
                f"partie 1. Votre gain final pour l'expérience est de {player.participant.payoff}."

    player.participant.vars["txt_final"] = txt_final


# PAGES ----------------------------------------------------------------------------------------------------------------

class BeforeFinal(Page):
    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        compute_final_payoff(player)


# PAGES
class Final(Page):
    form_model = "player"
    form_fields = ["comments"]

    @staticmethod
    def js_vars(player: Player):
        return dict(
            fill_auto=player.session.config.get("fill_auto", False)
        )


class FinalAfterComments(Page):
    @staticmethod
    def js_vars(player: Player):
        return dict(
            fill_auto=False
        )


page_sequence = [BeforeFinal, Final, FinalAfterComments]
