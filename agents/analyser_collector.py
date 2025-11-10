# interroge la base vectorielle pour trouver les articles pertinents et les enregistres comme contexte
# input user_request
# output articles contexte 

class AnalyserCollector:
    def __init__(self, vector_db_client):
        self.vector_db_client = vector_db_client

    def find_relevant_articles(self, user_request):
        """
        Interroge la base vectorielle pour trouver les articles pertinents.
        Args:
            user_request (str): La requête de l'utilisateur.
        Returns:
            list: Liste d'articles pertinents.
        """
        # À implémenter
        pass

    def save_context(self, articles):
        """
        Enregistre les articles comme contexte.
        Args:
            articles (list): Liste d'articles à enregistrer.
        """
        # À implémenter
        pass

    def process(self, user_request):
        """
        Processus complet : trouve les articles pertinents et les enregistre.
        Args:
            user_request (str): La requête de l'utilisateur.
        Returns:
            list: Liste d'articles de contexte.
        """
        articles = self.find_relevant_articles(user_request)
        self.save_context(articles)
        return articles
