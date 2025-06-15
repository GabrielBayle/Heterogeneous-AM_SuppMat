import random
from collections import deque

from otree.api import *

from .understanding import UNDERSTANDING

doc = """
Mécanisme approbation avec inégalités
"""

pairs = None


class C(BaseConstants):
    NAME_IN_URL = 'ampga'
    PLAYERS_PER_GROUP = 2
    NUM_ROUNDS = 19

    # traitements
    EQUAL = "equal"
    LOW = "low"
    HIGH = "high"

    # PARAMETERS -------------------------------------------------------------------------------------------------------
    # dotations
    EQUAL_ENDOW = (20, 20)
    LOW_ENDOW = (22, 18)
    HIGH_ENDOW = (30, 10)

    ACTIV_A_PAY = 0.7
    ACTIV_B_PAY = 1
    DECISION_TIME = 60

    CONVERSION_RATE = 1


class Subsession(BaseSubsession):
    conversion_rate = models.FloatField()
    treatment = models.StringField()
    approbation = models.BooleanField()


class Group(BaseGroup):
    total_activite_A = models.IntegerField()
    approbation = models.IntegerField()
    total_activite_A_apres_approb = models.IntegerField()


class Player(BasePlayer):
    understanding_1 = models.StringField()
    understanding_2 = models.StringField()
    understanding_3 = models.StringField()
    understanding_4 = models.StringField()
    understanding_5 = models.StringField()
    understanding_6 = models.StringField()
    understanding_faults = models.IntegerField(initial=0)

    dotation = models.IntegerField()
    activite_A = models.IntegerField(min=0)
    activite_A_other = models.IntegerField(min=0)
    activite_B = models.IntegerField()
    approbation = models.IntegerField()
    activite_A_apres_approb = models.IntegerField()
    activite_B_apres_approb = models.IntegerField()
    payoff_ecus = models.FloatField()
    paid_round = models.IntegerField()


# METHODS ==============================================================================================================
def get_pairs(subsession: Subsession):
    players_all = subsession.get_players()
    left = [p.id_in_subsession for p in players_all[: len(players_all) // 2]]
    right = [p.id_in_subsession for p in players_all[len(players_all) // 2:]]
    right = deque(right)
    while True:
        yield list(zip(left, right))
        right.rotate(1)


def creating_session(subsession: Subsession):
    global pairs

    subsession.conversion_rate = subsession.session.config.get("approbation_publicgoods_conversion", C.CONVERSION_RATE)

    if subsession.round_number == 1:
        subsession.treatment = subsession.session.config.get("treatment")
        subsession.approbation = subsession.session.config.get("approbation")
        if "understanding" not in subsession.session.vars.keys():
            key = subsession.treatment + ("_approb" if subsession.approbation else "")
            subsession.session.vars["understanding"] = UNDERSTANDING[key]

        pairs = get_pairs(subsession)
        for p in subsession.get_players():
            p.paid_round = random.randint(1, C.NUM_ROUNDS)

    else:
        subsession.treatment = subsession.in_round(1).treatment
        subsession.approbation = subsession.in_round(1).approbation
        for p in subsession.get_players():
            p.paid_round = p.in_round(1).paid_round

    subsession.set_group_matrix(next(pairs))
    for g in subsession.get_groups():
        set_dotations(g)


def compute_payoffs(subsession: Subsession, after_approbation):
    for g in subsession.get_groups():
        if not after_approbation:
            g.total_activite_A = sum([p.activite_A for p in g.get_players()])
        else:
            g.approbation = sum([p.approbation for p in g.get_players()])
            if g.approbation == 2:
                for p in g.get_players():
                    p.activite_A_apres_approb = p.activite_A
                g.total_activite_A_apres_approb = g.total_activite_A
            else:
                min_A = min([p.activite_A for p in g.get_players()])
                for p in g.get_players():
                    p.activite_A_apres_approb = min_A
                    p.activite_B_apres_approb = p.dotation - p.activite_A_apres_approb
                g.total_activite_A_apres_approb = sum([p.activite_A_apres_approb for p in g.get_players()])

        if not subsession.approbation or (subsession.approbation and after_approbation):
            for p in g.get_players():
                compute_individual_payoffs(p)


def set_dotations(group: Group):
    dotations = C.EQUAL_ENDOW if group.subsession.treatment == C.EQUAL else \
        C.LOW_ENDOW if group.subsession.treatment == C.LOW else \
            C.HIGH_ENDOW
    group.get_player_by_id(1).dotation = dotations[0]
    group.get_player_by_id(2).dotation = dotations[1]


def activite_A_max(player: Player):
    return player.dotation


def compute_understanding_faults(player: Player):
    questionnaire = player.session.vars.get("understanding").copy()
    faults = 0
    for i, q in enumerate(questionnaire):
        if getattr(player, f"understanding_{i + 1}") != q["solution"]:
            faults += 1
    player.understanding_faults = faults


def compute_individual_payoffs(player: Player):
    if player.subsession.approbation:
        player.activite_B_apres_approb = player.dotation - player.activite_A_apres_approb
        player.payoff_ecus = player.group.total_activite_A_apres_approb * C.ACTIV_A_PAY + \
                             player.activite_B_apres_approb * C.ACTIV_B_PAY
    else:
        player.payoff_ecus = player.group.total_activite_A * C.ACTIV_A_PAY + player.activite_B * C.ACTIV_B_PAY

    player.payoff = player.payoff_ecus * player.subsession.conversion_rate

    if player.round_number == C.NUM_ROUNDS:
        txt_final = f"C'est la période {player.paid_round} qui a été sélectionnée aléatoirement par le programme informatique " \
                    f"pour déterminer votre gain de cette partie. A cette période vous avez gagné " \
                    f"{player.in_round(player.paid_round).payoff_ecus:.2f} ECUs, soit " \
                    f"{player.in_round(player.paid_round).payoff}."
        player.participant.vars["approbation_publicgoods"] = dict(
            txt_final=txt_final,
            payoff=player.in_round(player.paid_round).payoff
        )


# PAGES ================================================================================================================
class MyPage(Page):
    @staticmethod
    def vars_for_template(player: Player):
        return dict(
            other_dotation=player.get_others_in_group()[0].dotation
        )

    @staticmethod
    def js_vars(player: Player):
        mydict = dict(C.__dict__)
        mydict.update(dict(
            fill_auto=player.session.config.get("fill_auto", False),
            treatment=player.subsession.treatment,
            approbation=player.subsession.approbation,
            dotations=(C.EQUAL_ENDOW if player.subsession.treatment == C.EQUAL else
                       C.LOW_ENDOW if player.subsession.treatment == C.LOW else
                       C.HIGH_ENDOW)
        ))
        return mydict


class Presentation(MyPage):
    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == 1


class Instructions(MyPage):
    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == 1


class InstructionsWaitMonitor(MyPage):
    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == 1 and player.session.config.get("instructions_relues", True)

    @staticmethod
    def js_vars(player: Player):
        existing = MyPage.js_vars(player)
        existing["fill_auto"] = False
        return existing


class InstructionsWaitForAll(WaitPage):
    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == 1 and not player.session.config.get("instructions_relues", True)


class Understanding(MyPage):
    form_model = "player"
    form_fields = ['understanding_1', 'understanding_2', 'understanding_3', 'understanding_4', 'understanding_5',
                   'understanding_6']

    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == 1

    def vars_for_template(player: Player):
        existing = MyPage.vars_for_template(player).copy()
        existing["understanding"] = player.session.vars["understanding"].copy()
        return existing

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        if timeout_happened:
            for i, q in enumerate(player.session.vars["understanding"]):
                setattr(player, f"understanding_{i + 1}", random.choice(q["propositions"]))
        compute_understanding_faults(player)


class UnderstandingResults(MyPage):
    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == 1

    def vars_for_template(player: Player):
        existing = MyPage.vars_for_template(player).copy()
        questionnaire = player.session.vars["understanding"].copy()

        for i, q in enumerate(questionnaire):
            q["reponse"] = getattr(player, f"understanding_{i+1}")

        existing["understanding"] = questionnaire
        return existing


class UnderstandingWaitForAll(WaitPage):
    wait_for_all_groups = True

    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == 1


class Decision(MyPage):
    form_model = "player"
    form_fields = ["activite_A", "activite_A_other"]

    def vars_for_template(player: Player):
        existing = MyPage.vars_for_template(player)
        other = player.get_others_in_group()[0]
        dotation_max = player.dotation if player.dotation > other.dotation else other.dotation
        existing.update(
            dict(
                pl_dotation=player.dotation,
                ot_dotation=other.dotation,
                pl_width=int(player.dotation / dotation_max * 100),
                ot_width=int(other.dotation / dotation_max * 100)
            )
        )
        return existing

    def js_vars(player: Player):
        existing = MyPage.js_vars(player)
        existing.update(
            dict(
                pl_dotation=player.dotation,
                ot_dotation=player.get_others_in_group()[0].dotation
            )
        )
        return existing

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        if timeout_happened:
            player.activite_A = random.randint(0, player.dotation)
            player.activite_A_other = random.randint(0, player.get_others_in_group()[0].dotation)
        player.activite_B = player.dotation - player.activite_A


class DecisionWaitForAll(WaitPage):
    wait_for_all_groups = True

    @staticmethod
    def after_all_players_arrive(subsession: Subsession):
        compute_payoffs(subsession, after_approbation=False)


class Approbation(MyPage):
    form_model = "player"
    form_fields = ["approbation"]

    @staticmethod
    def is_displayed(player: Player):
        return player.subsession.approbation

    @staticmethod
    def vars_for_template(player: Player):
        existing = MyPage.vars_for_template(player)
        gain_act_A = player.group.total_activite_A * C.ACTIV_A_PAY
        pl_payoff = player.activite_B * C.ACTIV_B_PAY + gain_act_A
        other = player.get_others_in_group()[0]
        ot_payoff = other.activite_B * C.ACTIV_B_PAY + gain_act_A
        min_A = min([player.activite_A, other.activite_A])
        total_min_A = 2 * min_A
        gain_min_A = total_min_A * C.ACTIV_A_PAY
        pl_payoff_min_A = (player.dotation - min_A) * C.ACTIV_B_PAY + gain_min_A
        ot_payoff_min_A = (other.dotation - min_A) * C.ACTIV_B_PAY + gain_min_A
        existing.update(dict(
            other_dec=other.activite_A,
            gain_act_A=gain_act_A,
            pl_payoff=pl_payoff,
            ot_payoff=ot_payoff,
            min_A=min_A,
            total_min_A=total_min_A,
            gain_min_A=gain_min_A,
            pl_payoff_min_A=pl_payoff_min_A,
            ot_payoff_min_A=ot_payoff_min_A
        ))
        return existing

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        if timeout_happened:
            player.approbation = random.random() >= 0.5


class ApprobationWaitForAll(WaitPage):
    wait_for_all_groups = True

    @staticmethod
    def is_displayed(player: Player):
        return player.subsession.approbation

    @staticmethod
    def after_all_players_arrive(subsession: Subsession):
        compute_payoffs(subsession, after_approbation=True)


class Results(MyPage):
    def vars_for_template(player: Player):
        existing = MyPage.vars_for_template(player)
        other = player.get_others_in_group()[0]

        if player.subsession.approbation:
            other_approb = other.approbation
            gain_A_apres_approb = player.group.total_activite_A_apres_approb * C.ACTIV_A_PAY
            gain_B_apres_approb = player.activite_B_apres_approb * C.ACTIV_B_PAY
        else:
            other_approb = None
            gain_A_apres_approb = None
            gain_B_apres_approb = None

        existing.update(
            dict(
                other_dec=other.activite_A,
                other_approb=other_approb,
                other_payoff=other.payoff_ecus,
                gain_A=player.group.total_activite_A * C.ACTIV_A_PAY,
                gain_B=player.activite_B * C.ACTIV_B_PAY,
                gain_A_apres_approb=gain_A_apres_approb,
                gain_B_apres_approb=gain_B_apres_approb
            )
        )
        return existing


class ResultsWaitForAll(WaitPage):
    wait_for_all_groups = True


class Final(MyPage):
    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == C.NUM_ROUNDS

    @staticmethod
    def vars_for_template(player: Player):
        existing = MyPage.vars_for_template(player)
        return existing


page_sequence = [
    Presentation,
    Instructions, InstructionsWaitMonitor, InstructionsWaitForAll,
    Understanding, UnderstandingResults, UnderstandingWaitForAll,
    Decision, DecisionWaitForAll,
    Approbation, ApprobationWaitForAll,
    Results, ResultsWaitForAll,
    # Final
]
