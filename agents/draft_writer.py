"""
author: DeJongnick
name: draft_writer.py
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

class DraftWriter:
    """
    Generate a complete draft article from a user request, plan, context articles, and optional comments.
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
        load_dotenv(dotenv_path="/Users/perso/Documents/Agents/Agentic_Times/.venv/.env")
        self.model = model
        self.provider = provider if provider != "auto" else self._detect_provider()
        self.allow_fallback = allow_fallback
        self.base_system_prompt = system_prompt or (
            "You are an expert journalist and writer specialized in creating high-quality press articles. "
            "Your articles are well-structured, engaging, and follow professional journalistic standards. "
            "You write clear, informative content with proper formatting, including titles, subtitles, "
            "paragraphs, and appropriate emphasis where needed. "
            "It is essential that all information and data published in the article cite their sources. "
            "You must clearly indicate the origin/source of any referenced or paraphrased idea, notably by citing the articles provided in context (with source/filename if available)."
        )
        try:
            if self.provider == "azure":
                self._init_azure(api_key, endpoint)
            elif self.provider == "openai":
                self._init_openai(api_key)
            else:
                raise ValueError(f"Unknown provider: {self.provider}")
        except Exception as e:
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
        if os.environ.get("GITHUB_APIKEY"):
            return "azure"
        if os.environ.get("OPENAI_APIKEY"):
            return "openai"
        raise ValueError("No API key found (GITHUB_APIKEY or OPENAI_APIKEY)")

    def _init_azure(self, api_key: Optional[str], endpoint: Optional[str]):
        key = api_key or os.environ.get("GITHUB_APIKEY")
        if not key:
            raise ValueError("Missing Azure key ('GITHUB_APIKEY').")
        self.llm_client = ChatCompletionsClient(
            endpoint=endpoint or os.environ.get("AZURE_ENDPOINT", "https://models.github.ai/inference"),
            credential=AzureKeyCredential(key)
        )

    def _init_openai(self, api_key: Optional[str]):
        if not _HAS_LANGCHAIN:
            raise ImportError("langchain_openai is not installed.")
        key = api_key or os.environ.get("OPENAI_APIKEY")
        if not key:
            raise ValueError("Missing OpenAI key ('OPENAI_APIKEY').")
        self.llm_client = ChatOpenAI(model=self.model, openai_api_key=key)

    def _articles_context(self, articles: Optional[list]) -> str:
        if not articles:
            return ""
        context = ["Reference articles for context and inspiration (please cite these sources if used in your writing):"]
        for art in articles:
            for src, content in art.items():
                preview = content[:2000] + "..." if len(content) > 2000 else content
                context.append(f"\n--- Source: {src} ---\n{preview}\n")
        return "\n".join(context)

    def _format_comments(self, comments: Optional[str]) -> str:
        if not comments:
            return ""
        return f"\n\nFeedback and comments to incorporate:\n{comments}\n"

    def write_draft(
        self,
        user_request: str,
        plan: str,
        articles_context: Optional[list] = None,
        comments: Optional[str] = None
    ) -> str:
        system_prompt = self.base_system_prompt
        if articles_context:
            system_prompt += "\n\n" + self._articles_context(articles_context)
        user_message_parts = [
            "Write a complete, well-formatted press article based on the following information:\n"
        ]
        user_message_parts.append(f"User request: {user_request}\n")
        user_message_parts.append(f"\nPlan to follow:\n{plan}\n")
        if comments:
            user_message_parts.append(self._format_comments(comments))
        user_message_parts.append(
            "\nThe article should:\n"
            "- Follow the plan structure closely\n"
            "- Be well-formatted with a clear title, subtitles, and paragraphs\n"
            "- Include engaging content that informs and captivates readers\n"
            "- Use appropriate journalistic style and tone\n"
            "- Incorporate information from context articles when relevant\n"
            "- Explicitly cite sources (especially articles provided in context) each time a fact, quote, or idea is used from them (e.g. at minimum by referencing the source filename such as [source: EXAMPLE.txt] in the text or footnotes)\n"
            "- Be complete and ready for publication\n"
        )
        if comments:
            user_message_parts.append(
                "- Incorporate the provided feedback and comments to improve the article\n"
            )
        user_message = "".join(user_message_parts)
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

