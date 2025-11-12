"""
author: DeJongnick
name: analyser_collector.py
date: 11/10/2025 (creation)
"""

import os
from typing import Optional, Literal

from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage
from azure.core.credentials import AzureKeyCredential

from dotenv import load_dotenv

from agents.prompt_loader import load_prompt

LANGCHAIN_AVAILABLE = False
try:
    from langchain_openai import ChatOpenAI
    from langchain_core.messages import SystemMessage as LangChainSystemMessage, HumanMessage
    LANGCHAIN_AVAILABLE = True
except ImportError:
    pass


class UserRequestFormatter:
    """
    Formats a user request (Azure or OpenAI/langchain),
    extracts themes/keywords for semantic search.
    Handles automatic fallback based on API keys.
    """
    def __init__(
        self, 
        provider: Literal["azure", "openai", "auto"] = "auto",
        api_key: Optional[str] = None,
        endpoint: Optional[str] = None,
        model: str = "gpt-4o-mini",
        system_prompt: Optional[str] = None,
        allow_fallback: bool = True
    ):
        load_dotenv(dotenv_path="/Users/perso/Documents/Agents/Agentic_Times/.venv/.env")
        self.model = model
        self.allow_fallback = allow_fallback
        default_prompt = (
            "You are a helpful assistant specialized in extracting themes and topics from user requests. "
            "Give exhaustive but concise keywords, topics, and themes optimized for semantic vector search."
        )
        self.system_prompt = system_prompt or load_prompt("user_request_formatter", default_prompt, section="system")

        prov = provider if provider != "auto" else self._auto_provider()
        # Initialize provider, fallback if needed
        try:
            if prov == "azure":
                self._init_azure(api_key, endpoint)
            elif prov == "openai":
                self._init_openai(api_key)
            else:
                raise ValueError(f"Unknown provider: {prov}")
            self.provider = prov
        except (ValueError, ImportError) as e:
            if allow_fallback and provider != "auto":
                fallback = "openai" if prov == "azure" else "azure"
                print(f"Warning: initializing {prov} failed ({e}), falling back to {fallback}")
                try:
                    if fallback == "azure":
                        self._init_azure(None, endpoint)
                    else:
                        self._init_openai(None)
                    self.provider = fallback
                except Exception as fb_err:
                    raise ValueError(
                        f"Both providers failed. Azure: {e}, OpenAI: {fb_err}. "
                        "Check your API keys (GITHUB_APIKEY/OPENAI_APIKEY)."
                    ) from fb_err
            else:
                raise

    def _auto_provider(self) -> str:
        """Detects the available provider (Azure if possible, otherwise OpenAI)."""
        if os.environ.get("GITHUB_APIKEY"):
            return "azure"
        if os.environ.get("OPENAI_APIKEY"):
            return "openai"
        raise ValueError("No API key found (GITHUB_APIKEY or OPENAI_APIKEY).")

    def _init_azure(self, api_key: Optional[str], endpoint: Optional[str]):
        self.api_key = api_key or os.environ.get("GITHUB_APIKEY")
        if not self.api_key:
            raise ValueError("Azure key missing ('GITHUB_APIKEY')")
        self.llm_client = ChatCompletionsClient(
            endpoint=endpoint or os.environ.get("AZURE_ENDPOINT", "https://models.github.ai/inference"),
            credential=AzureKeyCredential(self.api_key)
        )

    def _init_openai(self, api_key: Optional[str]):
        if not LANGCHAIN_AVAILABLE:
            raise ImportError("langchain_openai is not installed.")
        self.api_key = api_key or os.environ.get("OPENAI_APIKEY")
        if not self.api_key:
            raise ValueError("OpenAI key missing ('OPENAI_APIKEY')")
        self.llm_client = ChatOpenAI(model=self.model, openai_api_key=self.api_key)

    def format(self, user_request: str) -> str:
        """Returns formatted request (themes/keywords) according to provider."""
        if self.provider == "azure":
            resp = self.llm_client.complete(
                messages=[SystemMessage(self.system_prompt), UserMessage(user_request)],
                model=self.model
            )
            return resp.choices[0].message.content.strip()
        elif self.provider == "openai":
            messages = [
                LangChainSystemMessage(content=self.system_prompt),
                HumanMessage(content=user_request)
            ]
            resp = self.llm_client.invoke(messages)
            return resp.content.strip()
        else:
            raise ValueError(f"Unknown provider: {self.provider}")


class AnalyserCollector:
    def __init__(
        self, 
        vector_db_client, 
        top_k: int = 10, 
        similarity_threshold: float = 0.3,
        request_formatter: Optional[UserRequestFormatter] = None
    ):
        """
        Initialize the analyser-collector.

        Args:
            vector_db_client: The vector database client
            top_k: Number of relevant articles to return
            similarity_threshold: Minimum similarity threshold (0.0 to 1.0)
            request_formatter: Optional UserRequestFormatter to format user requests before search
        """
        self.vector_db_client = vector_db_client
        self.top_k = top_k
        self.similarity_threshold = similarity_threshold
        self.request_formatter = request_formatter

    def find_relevant_articles(self, query):
        """
        Queries the vector database to find relevant articles.
        Args:
            query (str): The user's input query (will be formatted if formatter is set).
        Returns:
            list: List of relevant articles with their scores and metadata.
        """
        if self.vector_db_client is None:
            raise ValueError("VectorDBClient must be initialized")
        
        # Format the query if a formatter is provided
        if self.request_formatter is not None:
            query = self.request_formatter.format(query)

        results = self.vector_db_client.search(
            query=query,
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

    def corpus_context(self, query):
        """
        Returns a list of dictionaries [{article_title: content}]
        for each relevant article found via find_relevant_articles and save_content.
        """
        articles = self.find_relevant_articles(query)

        sources = [article['source'] for article in articles]
        contents = self.save_content(articles)

        results = []
        for source, content in zip(sources, contents):
            results.append({source: content})
        return results
