import random

from otree.api import *

author = 'D. Dubois'

doc = """
Target Number Line Estimate
"""


class C(BaseConstants):
    NAME_IN_URL = 'tnle'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 15
    DECISION_TIME = 10

    CIBLES = dict(
        zip(range(1, 16),
            [12.2, 39.87, 68.02, 77.42, 47.95, 16.33, 26.76, 84.58, 94.21, 5.87, 64.9, 45.49, 74.67, 37.6, 7.76]))

    # pour le gain
    CONSTANTE = 3  # gain si cible exacte
    FACTEUR_DISTANCE = 0.05  # donc gain = CONSTANTE - 0.05 x distance où distance = | cible - valeur sélectionnée |


class Subsession(BaseSubsession):
    constante = models.FloatField()


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    NLE_paid_decision = models.IntegerField()
    NLE_nombre_cible = models.FloatField()
    NLE_curseur_position = models.FloatField()


# METHODS ==============================================================================================================

def creating_session(subsession: Subsession):
    subsession.constante = subsession.session.config.get("targetNLE_constante", C.CONSTANTE)

    for p in subsession.get_players():
        p.NLE_nombre_cible = C.CIBLES[subsession.round_number]

        if subsession.round_number == 1:
            p.NLE_paid_decision = random.randint(1, C.NUM_ROUNDS)
        else:
            p.NLE_paid_decision = p.in_round(1).NLE_paid_decision


def compute_payoff(player: Player):
    player.payoff = cu(
        player.subsession.constante - C.FACTEUR_DISTANCE * abs(player.NLE_curseur_position - player.NLE_nombre_cible))

    if player.payoff < 0:
        player.payoff = cu(0)

    if player.round_number == C.NUM_ROUNDS:
        paid_round = player.in_round(player.NLE_paid_decision)

        txt_final = f"C'est l'exercice {player.NLE_paid_decision} qui a été sélectionné pour déterminer votre gain à " \
                    f"cette partie. A cet exercice la valeur cible était {paid_round.NLE_nombre_cible}. Vous avez " \
                    f"positionné le curseur sur {paid_round.NLE_curseur_position}. Votre gain pour cette partie " \
                    f"est de {paid_round.payoff}."

        player.participant.vars["targetNLE"] = dict(txt_final=txt_final, payoff=paid_round.payoff)


# PAGES ================================================================================================================
class Instructions(Page):
    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == 1

    @staticmethod
    def js_vars(player: Player):
        return dict(fill_auto=player.session.config.get("fill_auto", False))


class Decision(Page):
    timeout_seconds = C.DECISION_TIME
    timer_text = "Temps Restant : "
    form_model = "player"
    form_fields = ["NLE_curseur_position"]

    @staticmethod
    def js_vars(player: Player):
        return dict(fill_auto=player.session.config.get("fill_auto", False))

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        compute_payoff(player)


class Results(Page):
    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == C.NUM_ROUNDS

    @staticmethod
    def js_vars(player: Player):
        return dict(fill_auto=player.session.config.get("fill_auto", False))


page_sequence = [Instructions, Decision,
                 # Results
                 ]
