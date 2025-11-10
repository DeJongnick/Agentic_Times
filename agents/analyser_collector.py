# interroge la base vectorielle pour trouver les articles pertinents et les enregistres comme contexte
# input user_request
# output articles contexte 

class AnalyserCollector:
    def __init__(self, vector_db_client, top_k: int = 10, similarity_threshold: float = 0.3):
        """
        Initialize the analyser-collector.
        
        Args:
            vector_db_client: The vector database client
            top_k: Number of relevant articles to return
            similarity_threshold: Minimum similarity threshold (0.0 to 1.0)
        """
        self.vector_db_client = vector_db_client
        self.top_k = top_k
        self.similarity_threshold = similarity_threshold

    def find_relevant_articles(self, user_request):
        """
        Queries the vector database to find relevant articles.
        Args:
            user_request (str): The user's input query.
        Returns:
            list: List of relevant articles with their scores and metadata.
        """
        if self.vector_db_client is None:
            raise ValueError("VectorDBClient must be initialized")
        
        # Search in the vector database
        results = self.vector_db_client.search(
            query=user_request,
            top_k=self.top_k,
            threshold=self.similarity_threshold
        )
        
        # Group by article source (an article can have several relevant chunks)
        articles_dict = {}
        for result in results:
            source = result['source']
            if source not in articles_dict:
                articles_dict[source] = {
                    'source': source,
                    'chunks': [],
                    'max_score': result['score'],
                    'avg_score': 0.0
                }
            articles_dict[source]['chunks'].append(result)
            articles_dict[source]['max_score'] = max(articles_dict[source]['max_score'], result['score'])
        
        # Compute the average score for each article
        for source, article in articles_dict.items():
            scores = [chunk['score'] for chunk in article['chunks']]
            article['avg_score'] = sum(scores) / len(scores) if scores else 0.0
        
        # Sort by descending max score
        articles = sorted(articles_dict.values(), key=lambda x: x['max_score'], reverse=True)
        
        return articles

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
