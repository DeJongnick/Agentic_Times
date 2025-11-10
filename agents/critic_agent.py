# input draft
# output draft + comments + note 

class CriticAgent:
    def __init__(self, model=None):
        self.model = model  # un éventuel modèle pour l'évaluation

    def review_draft(self, draft):
        """
        Analyse le draft et génère des commentaires.
        Args:
            draft (str): Le brouillon à analyser.
        Returns:
            dict: Dictionnaire contenant le draft, les commentaires et une note.
        """
        comments = self.generate_comments(draft)
        note = self.evaluate_draft(draft)
        return {
            "draft": draft,
            "comments": comments,
            "note": note
        }

    def generate_comments(self, draft):
        """
        Génère des commentaires sur le draft.
        Args:
            draft (str): Le brouillon à commenter.
        Returns:
            str: Commentaires sur le draft.
        """
        # À implémenter : logiques d'analyse
        pass

    def evaluate_draft(self, draft):
        """
        Génère une note pour le draft.
        Args:
            draft (str): Le brouillon à noter.
        Returns:
            float: Note du draft.
        """
        # À implémenter : logiques d'évaluation
        pass
