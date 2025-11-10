"""
author: DeJongnick
name: analyser_collector.py
date: 11/10/2025 (creation)
"""

import os

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

        results = self.vector_db_client.search(
            query=user_request,
            top_k=self.top_k,
            threshold=self.similarity_threshold
        )

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

        for source, article in articles_dict.items():
            scores = [chunk['score'] for chunk in article['chunks']]
            article['avg_score'] = sum(scores) / len(scores) if scores else 0.0

        articles = sorted(articles_dict.values(), key=lambda x: x['max_score'], reverse=True)

        return articles

    def save_content(self, articles):
        """
        Saves the content of the articles as context.
        Args:
            articles (list): List of articles to save.
        Returns:
            list: List of HTML contents of the existing articles.
        """
        sources = [article['source'] for article in articles]
        content = []
        raw_path = "data/raw"

        for source in sources:
            file_path = os.path.join(raw_path, source)
            if os.path.exists(file_path):
                with open(file_path, "r", encoding="utf-8") as f:
                    text = f.read()
                content.append(text)

        return content

    def corpus_context(self, user_request):
        """
        Returns a list of dictionaries [{article_title: content}]
        for each relevant article found via find_relevant_articles and save_content.
        """

        articles = self.find_relevant_articles(user_request)

        sources = [article['source'] for article in articles]
        contents = self.save_content(articles)

        results = []
        for source, content in zip(sources, contents):
            results.append({source: content})
        return results
