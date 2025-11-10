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

LANGCHAIN_AVAILABLE = False
try:
    from langchain_openai import ChatOpenAI
    from langchain_core.messages import SystemMessage as LangChainSystemMessage, HumanMessage
    LANGCHAIN_AVAILABLE = True
except ImportError:
    pass


class PlanWriter:
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
        self.base_system_prompt = system_prompt or (
            "You are a helpful assistant specialized in create details plan for press articles. "
            "Give exhaustive plan with title, subtitles, sources etc."
        )

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

    def _format_articles_context(self, articles: list) -> str:
        """
        Format the articles context for the system prompt.
        Args:
            articles: List of dictionaries from analyser_collector.corpus_context()
                     Format: [{source: content}, ...]
        Returns:
            Formatted string with articles context
        """
        if not articles:
            return ""
        
        context_parts = ["Be inspired by these relevant articles:\n"]
        for article_dict in articles:
            for source, content in article_dict.items():
                # Truncate content if too long (e.g., first 2000 chars)
                content_preview = content[:2000] + "..." if len(content) > 2000 else content
                context_parts.append(f"\n--- Source: {source} ---\n{content_preview}\n")
        
        return "\n".join(context_parts)

    def format(self, user_request: str, articles: Optional[list] = None) -> str:
        """
        Creates a detailed plan based on user request and relevant articles.
        Args:
            user_request: The user's request for the article
            articles: Optional list of articles from analyser_collector.corpus_context()
                     Format: [{source: content}, ...]
        Returns:
            A detailed plan for the article
        """
        # Build system prompt with articles context if provided
        system_prompt = self.base_system_prompt
        if articles:
            articles_context = self._format_articles_context(articles)
            system_prompt = f"{self.base_system_prompt}\n\n{articles_context}"
        
        # Build user message that explicitly references the request and articles
        if articles:
            user_message = (
                f"Based on the user's request below and the relevant articles provided in the system context, "
                f"create a comprehensive plan for the article.\n\n"
                f"User request: {user_request}\n\n"
                f"The plan should include:\n"
                f"- A compelling title\n"
                f"- Clear subtitles and sections\n"
                f"- References to the relevant articles provided\n"
                f"- A structured outline that addresses the user's request"
            )
        else:
            user_message = (
                f"Create a comprehensive plan for the following article request:\n\n"
                f"{user_request}\n\n"
                f"The plan should include:\n"
                f"- A compelling title\n"
                f"- Clear subtitles and sections\n"
                f"- A structured outline"
            )
        
        if self.provider == "azure":
            resp = self.llm_client.complete(
                messages=[SystemMessage(system_prompt), UserMessage(user_message)],
                model=self.model
            )
            return resp.choices[0].message.content.strip()
        elif self.provider == "openai":
            messages = [
                LangChainSystemMessage(content=system_prompt),
                HumanMessage(content=user_message)
            ]
            resp = self.llm_client.invoke(messages)
            return resp.content.strip()
        else:
            raise ValueError(f"Unknown provider: {self.provider}")