from datetime import date

from otree.api import *
from pycountry import countries

countries_names = list([c.name for c in countries])
countries_names.sort()

doc = """
Demog socio-démographique 
"""


def disciplines():
    items = [
        "Administration", "Archéologie", "Biologie", "Ecole de commerce", "Chimie", "Informatique", "Economie",
        "Education", "Droit", "Ecole d'infirmière", "Ecole d'ingénieur", "Langues étrangères", "Géographie",
        "Gestion / Management", "Histoire", "Lettres", "Mathématiques", "Médecine", "Musique", "Pharmacie",
        "Philosophie", "Physique", "Sciences politiques", "Psychologie", "Sociologie", "Sport",
        "-- Pas dans la liste --"
    ]
    return [(i, e) for i, e in enumerate(items)]


class C(BaseConstants):
    NAME_IN_URL = 'apd'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 1


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    gender = models.StringField(label="Sexe", choices=["Féminin", "Masculin"], widget=widgets.RadioSelectHorizontal)
    year_of_birth = models.IntegerField(
        label="Année de naissance",
        choices=range(date.today().year - 15, date.today().year - 101, -1))
    nationality = models.StringField(label="Nationalité", choices=countries_names)
    marital_status = models.StringField(label="Statut marital",
                                        choices=["Célibataire", "Pacsé(e)", "Marié(e)", "Divorcé(e)", "Veuf(ve)"],
                                        widget=widgets.RadioSelectHorizontal)
    brotherhood = models.IntegerField(label="Combien avez-vous de frères et soeurs ?", choices=range(16))
    brotherhood_rank = models.IntegerField(label="Si vous avez des frères et soeurs, quel est votre rang parmi eux ?",
                                           choices=range(1, 16), blank=True)
    job = models.StringField(label="Avez-vous un travail ?",
                             choices=["Non", "Oui, à temps partiel", "Oui, à temps plein"])
    socioprofessional_group = models.IntegerField(
        label="Catégorie socio-professionnelle",
        choices=[(i, e) for i, e in enumerate(
            ['Etudiant', 'Agriculteurs exploitants',
             'Artisans, commerçants et chefs d’entreprise', 'Cadres et professions intellectuelles supérieures',
             'Professions Intermédiaires', 'Employés', 'Ouvriers', 'Retraités',
             'Autres personnes sans activité professionnelle'])], widget=widgets.RadioSelect)
    diplome = models.IntegerField(
        label="Diplôme le plus élevé obtenu",
        choices=[(i, e) for i, e in enumerate(
            ['Pas de diplôme', 'CEP / Brevet des collèges', 'BEP / CAP', 'Baccalauréat', 'Bac +1', 'Bac +2', 'Bac +3',
             'Bac +4', 'Bac +5', 'Bac +8'])])
    discipline = models.IntegerField(
        label="Discipline étudiée", choices=disciplines())

    sante_financiere_abs = models.StringField(
        label="Comment vous sentez-vous en termes de santé financière ?",
        choices=["Vraiment en sécurité", "En sécurité", "Pas en sécurité", "Vraiment pas en sécurité",
                 "Ne sais pas / Ne souhaite pas répondre"]
    )

    # PAGE SANTÉ FINANCIERE ---------------------------------------------------
    sante_financiere_rel_status = models.StringField(
        label="Par rapport aux personnes de votre catégorie socio-professionnelle, comment vous sentez-vous en termes "
              "de santé financière ?",
        choices=["Vraiment en sécurité", "En sécurité", "Pas en sécurité", "Vraiment pas en sécurité",
                 "Ne sais pas / Ne souhaite pas répondre"]
    )
    sante_financiere_rel_france = models.StringField(
        label="Par rapport à l'ensemble de la population française, comment vous sentez-vous en termes de "
              "santé financière ?",
        choices=["Vraiment en sécurité", "En sécurité", "Pas en sécurité", "Vraiment pas en sécurité",
                 "Ne sais pas / Ne souhaite pas répondre"]
    )
    sante_financiere_rel_monde = models.StringField(
        label="Par rapport à l'ensemble de la population mondiale, comment vous sentez-vous en termes de "
              "santé financière ?",
        choices=["Vraiment en sécurité", "En sécurité", "Pas en sécurité", "Vraiment pas en sécurité",
                 "Ne sais pas / Ne souhaite pas répondre"]
    )


# PAGES ================================================================================================================
class Demog(Page):
    form_model = "player"
    form_fields = ["gender", "year_of_birth", "nationality", "marital_status", "brotherhood", "brotherhood_rank",
                   "job", "socioprofessional_group", "diplome", "discipline", "sante_financiere_abs"]

    @staticmethod
    def js_vars(player: Player):
        return dict(fill_auto=player.session.config.get("fill_auto", False))


class SanteFinanciere(Page):
    form_model = "player"
    form_fields = ["sante_financiere_rel_status", "sante_financiere_rel_france", "sante_financiere_rel_monde"]

    @staticmethod
    def js_vars(player: Player):
        return dict(
            fill_auto=player.session.config.get("fill_auto", False)
        )


page_sequence = [Demog, SanteFinanciere]
