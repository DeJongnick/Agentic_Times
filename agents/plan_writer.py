"""
author: DeJongnick
name: plan_writer.py
date: 11/10/2025 (creation)
"""

import os
from typing import Optional, Literal
from dotenv import load_dotenv

from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage
from azure.core.credentials import AzureKeyCredential

try:
    from langchain_openai import ChatOpenAI
    from langchain_core.messages import SystemMessage as LCSystemMessage, HumanMessage
    _HAS_LANGCHAIN = True
except ImportError:
    _HAS_LANGCHAIN = False

class PlanWriter:
    """
    Generate a detailed press article outline from a user request and (optional) context articles.
    Supports Azure (Github/azure api) or OpenAI (langchain); automatic fallback if allowed.
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
        # Load environment for API keys
        load_dotenv(dotenv_path="/Users/perso/Documents/Agents/Agentic_Times/.venv/.env")
        self.model = model
        self.provider = provider if provider != "auto" else self._detect_provider()
        self.allow_fallback = allow_fallback
        self.base_system_prompt = system_prompt or (
            "You are an assistant that writes exhaustive and structured plans for press articles, "
            "including titles, subtitles, and relevant sources."
        )
        # Initialize LLM client
        try:
            if self.provider == "azure":
                self._init_azure(api_key, endpoint)
            elif self.provider == "openai":
                self._init_openai(api_key)
            else:
                raise ValueError(f"Unknown provider: {self.provider}")
        except Exception as e:
            # Automatic fallback to the alternative provider if initialization failed
            if allow_fallback and provider != "auto":
                alt = "openai" if self.provider == "azure" else "azure"
                try:
                    if alt == "azure":
                        self._init_azure(None, endpoint)
                    else:
                        self._init_openai(None)
                    self.provider = alt
                except Exception as e2:
                    raise ValueError(f"Failed with {self.provider} and {alt}: {e} / {e2}")
            else:
                raise

    def _detect_provider(self) -> str:
        """Detect available provider via environment variables."""
        if os.environ.get("GITHUB_APIKEY"):
            return "azure"
        if os.environ.get("OPENAI_APIKEY"):
            return "openai"
        raise ValueError("No API key found (GITHUB_APIKEY or OPENAI_APIKEY)")

    def _init_azure(self, api_key: Optional[str], endpoint: Optional[str]):
        """Initialize Azure inference client."""
        key = api_key or os.environ.get("GITHUB_APIKEY")
        if not key:
            raise ValueError("Missing Azure key ('GITHUB_APIKEY').")
        self.llm_client = ChatCompletionsClient(
            endpoint=endpoint or os.environ.get("AZURE_ENDPOINT", "https://models.github.ai/inference"),
            credential=AzureKeyCredential(key)
        )

    def _init_openai(self, api_key: Optional[str]):
        """Initialize OpenAI LangChain client."""
        if not _HAS_LANGCHAIN:
            raise ImportError("langchain_openai is not installed.")
        key = api_key or os.environ.get("OPENAI_APIKEY")
        if not key:
            raise ValueError("Missing OpenAI key ('OPENAI_APIKEY').")
        self.llm_client = ChatOpenAI(model=self.model, openai_api_key=key)

    def _articles_context(self, articles: Optional[list]) -> str:
        """Format context articles for the system prompt."""
        if not articles:
            return ""
        context = ["Articles for inspiration:"]
        for art in articles:
            for src, content in art.items():
                # Truncate if content is too long
                preview = content[:2000] + "..." if len(content) > 2000 else content
                context.append(f"\n--- Source: {src} ---\n{preview}\n")
        return "\n".join(context)

    def format(self, user_request: str, articles: Optional[list] = None) -> str:
        """
        Build a detailed outline for a press article based on the user request and, optionally, context articles.
        """
        system_prompt = self.base_system_prompt
        if articles:
            system_prompt += "\n\n" + self._articles_context(articles)
        # Build user message with or without articles context
        if articles:
            user_message = (
                f"Based on the request below and the articles in the system context, "
                f"write a complete outline for the article.\n\n"
                f"User request: {user_request}\n\n"
                f"The outline should include:\n"
                f"- An engaging title\n"
                f"- Clear subtitles/sections\n"
                f"- References to context articles\n"
                f"- A structured plan"
            )
        else:
            user_message = (
                f"Write a complete outline for the following article request:\n\n"
                f"{user_request}\n\n"
                f"The outline should include:\n"
                f"- An engaging title\n"
                f"- Clear subtitles/sections\n"
                f"- A structured plan"
            )
        # LLM call depending on provider
        if self.provider == "azure":
            resp = self.llm_client.complete(
                messages=[SystemMessage(system_prompt), UserMessage(user_message)],
                model=self.model
            )
            return resp.choices[0].message.content.strip()
        elif self.provider == "openai":
            resp = self.llm_client.invoke([
                LCSystemMessage(content=system_prompt),
                HumanMessage(content=user_message)
            ])
            return resp.content.strip()
        raise ValueError(f"Unknown provider: {self.provider}")