import random

from otree.api import *

doc = """
Inequality Aversion Test
"""


class C(BaseConstants):
    NAME_IN_URL = 'iat'
    PLAYERS_PER_GROUP = 2
    NUM_ROUNDS = 1

    DECIDEUR_ROLE = "decideur"
    RECEVEUR_ROLE = "receveur"

    # ETGD (Equality Threshold Dictator Game) --------------------------------------------------------------------------
    ETDG_OPTION_A = [(20, 0) for _ in range(21)]
    ETDG_OPTION_B = [(i, i) for i in range(21)]
    ETDG_OPTIONS = list(zip(ETDG_OPTION_A, ETDG_OPTION_B))

    # MUG (Modified Ultimatum Game) ------------------------------------------------------------------------------------
    MUG_OPTIONS = [(20 - i, i) for i in range(11)]

    # MDG (Modified Dictator Game) -------------------------------------------------------------------------------------
    MDG_OPTIONS = MUG_OPTIONS


# TABLES ===============================================================================================================

class Subsession(BaseSubsession):
    conversion_rate = models.FloatField()


class Group(BaseGroup):
    ETDG_selected_row = models.IntegerField()
    ETDG_applied_option = models.StringField()
    MUG_applied_option = models.StringField()
    MDG_applied_option = models.StringField()


class Player(BasePlayer):
    ETDG_switch = models.IntegerField()
    ETDG_payoff = models.IntegerField()
    MUG_decideur_option = models.IntegerField()
    MUG_receveur_option = models.IntegerField()
    MUG_payoff = models.IntegerField()
    MDG_option = models.IntegerField()
    MDG_payoff = models.IntegerField()
    paid_game = models.IntegerField()
    payoff_ecus = models.FloatField()


# FUNCTION =============================================================================================================
def creating_session(subsession: Subsession):
    subsession.conversion_rate = subsession.session.config.get("inequalityAversionTest_conversion", 1)

def set_payoffs(subsession: Subsession):
    for group in subsession.get_groups():
        decideur = group.get_player_by_role(C.DECIDEUR_ROLE)
        receveur = group.get_player_by_role(C.RECEVEUR_ROLE)

        # ETDG -----------------------------------------------------------------------------
        group.ETDG_selected_row = random.randint(1, len(C.ETDG_OPTIONS))
        if decideur.ETDG_switch == 0 or decideur.ETDG_switch > group.ETDG_selected_row:
            group.ETDG_applied_option = str(C.ETDG_OPTION_A[group.ETDG_selected_row - 1])
            decideur.ETDG_payoff = C.ETDG_OPTION_A[group.ETDG_selected_row - 1][0]
            receveur.ETDG_payoff = C.ETDG_OPTION_A[group.ETDG_selected_row - 1][1]
        else:
            group.ETDG_applied_option = str(C.ETDG_OPTION_B[group.ETDG_selected_row - 1])
            decideur.ETDG_payoff = C.ETDG_OPTION_B[group.ETDG_selected_row - 1][0]
            receveur.ETDG_payoff = C.ETDG_OPTION_B[group.ETDG_selected_row - 1][1]

        # MUG --------------------------------------------------------------------------------
        group.MUG_applied_option = str(C.MUG_OPTIONS[decideur.MUG_decideur_option])
        if receveur.MUG_receveur_option > decideur.MUG_decideur_option:
            decideur.MUG_payoff = 0
            receveur.MUG_payoff = 0
        else:
            decideur.MUG_payoff = C.MUG_OPTIONS[decideur.MUG_decideur_option][0]
            receveur.MUG_payoff = C.MUG_OPTIONS[decideur.MUG_decideur_option][1]

        # MDG --------------------------------------------------------------------------------
        group.MDG_applied_option = str(C.MDG_OPTIONS[decideur.MDG_option])
        decideur.MDG_payoff = C.MDG_OPTIONS[decideur.MDG_option][0]
        receveur.MDG_payoff = C.MDG_OPTIONS[decideur.MDG_option][1]

        for p in group.get_players():
            set_individual_payoffs(p)


def set_individual_payoffs(player: Player):
    player.paid_game = random.randint(1, 3)
    txt_final = f"C'est le jeu {player.paid_game} qui a été aléatoirement sélectionné pour déterminer votre gain de " \
                f"cette partie."

    if player.paid_game == 1:
        txt_final += " " + f"C'est la ligne {player.group.ETDG_selected_row} qui a été tirée au sort et c'est "
        if player.role == C.DECIDEUR_ROLE:
            txt_final += "votre décision"
        else:
            txt_final += "la décision de l'autre joueur"
        txt_final += " " + f"qui a été appliquée {player.group.ETDG_applied_option}. Votre gain est donc de " \
                           f"{player.ETDG_payoff} ECUs"
        player.payoff_ecus = player.ETDG_payoff

    elif player.paid_game == 2:
        if player.role == C.DECIDEUR_ROLE:
            txt_final += " " + f"C'est votre décision qui a été appliquée. Vous avez choisi la répartition " \
                         f"{player.group.MUG_applied_option}. L'autre joueur a déclaré accepter à " \
                         f"partir de {str(C.MUG_OPTIONS[player.get_others_in_group()[0].MUG_receveur_option])}. Votre " \
                         f"gain est donc de {player.MUG_payoff} ECUs"

        else:
            txt_final += " " + f"C'est la décision de l'autre joueur qui a été appliquée. Il a choisi la répartition " \
                         f"{player.group.MUG_applied_option}. Vous avez déclaré accepter à partir de " \
                         f"{str(C.MUG_OPTIONS[player.MUG_receveur_option])}. Votre gain est donc de {player.MUG_payoff} " \
                         f"ECUs"
        player.payoff_ecus = player.MUG_payoff

    elif player.paid_game == 3:
        if player.role == C.DECIDEUR_ROLE:
            txt_final += " " + f"C'est votre décision qui a été appliquée {player.group.MDG_applied_option}. Votre gain est " \
                        f"donc de {player.MDG_payoff} ECUs"
        else:
            txt_final += " " + f"C'est la décision de l'autre joueur qui a été appliquée ({player.group.MDG_applied_option}). " \
                        f"Votre gain est donc de {player.MDG_payoff} ECUs"
        player.payoff_ecus = player.MDG_payoff

    player.payoff = player.payoff_ecus * player.subsession.conversion_rate
    txt_final += f", soit {player.payoff}."

    player.participant.vars["inequalityAversionTest"] = dict(
        txt_final=txt_final,
        payoff=player.payoff
    )


# PAGES ================================================================================================================
class MyPage(Page):
    def vars_for_template(player: Player):
        return dict()

    def js_vars(player: Player):
        return dict(
            fill_auto=player.session.config.get("fill_auto", False)
        )


class BeforeStartWaitForAll(WaitPage):
    wait_for_all_groups = True


class Presentation(MyPage):
    pass


class EqualityThresholdDictator(MyPage):
    form_model = "player"
    form_fields = ["ETDG_switch"]

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        if timeout_happened:
            player.ETDG_switch = random.randint(0, len(C.ETDG_OPTIONS))


class ModifiedUltimatum(MyPage):
    form_model = "player"
    form_fields = ["MUG_decideur_option", "MUG_receveur_option"]

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        if timeout_happened:
            player.MUG_decideur_option = random.randint(0, len(C.MUG_OPTIONS) - 1)
            player.MUG_receveur_option = random.randint(0, len(C.MUG_OPTIONS) - 1)


class ModifiedDictator(MyPage):
    form_model = "player"
    form_fields = ["MDG_option"]

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        if timeout_happened:
            player.MDG_option = random.randint(0, len(C.MDG_OPTIONS) - 1)


class BeforeResultsWaitForAll(WaitPage):
    wait_for_all_groups = True

    def after_all_players_arrive(subsession: Subsession):
        set_payoffs(subsession)


page_sequence = [
    BeforeStartWaitForAll,
    Presentation,
    EqualityThresholdDictator,
    ModifiedUltimatum,
    ModifiedDictator,
    BeforeResultsWaitForAll
]
