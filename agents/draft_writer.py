# input user_request + plan détaillé + articles contexte
# output draft

class DraftWriter:
    def __init__(self, model=None):
        self.model = model  # éventuel modèle de génération de texte

    def write_draft(self, user_request, plan, articles_context):
        """
        Génère un draft à partir de la requête utilisateur, du plan détaillé et des articles de contexte.
        Args:
            user_request (str): La demande de l'utilisateur.
            plan (str): Le plan détaillé à suivre.
            articles_context (list): Liste d'articles de contexte.
        Returns:
            str: Le draft généré.
        """
        # À implémenter : logiques de génération
        pass
