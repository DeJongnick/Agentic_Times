"""
author: DeJongnick
name: critic_writer.py
date: 11/10/2025 (creation)
"""

import os
from typing import Optional, Literal, Dict, Any
from pathlib import Path
from dotenv import load_dotenv

from agents.prompt_loader import load_prompt_config

try:
    from azure.ai.inference import ChatCompletionsClient
    from azure.ai.inference.models import SystemMessage, UserMessage
    from azure.core.credentials import AzureKeyCredential
except ImportError:
    ChatCompletionsClient = None

try:
    from langchain_openai import ChatOpenAI
    from langchain_core.messages import SystemMessage as LCSystemMessage, HumanMessage
    _HAS_LANGCHAIN = True
except ImportError:
    _HAS_LANGCHAIN = False

class CriticAgent:
    """
    Agent that analyzes and critiques a draft article, generating comments (divided into strengths and improvements) and a score.
    Uses Azure (github/azure api), OpenAI (langchain), or auto-fallback.
    All feedback and output are provided in English.
    """
    def __init__(
        self,
        provider: Literal["azure", "openai", "auto"] = "auto",
        api_key: Optional[str] = None,
        endpoint: Optional[str] = None,
        model: str = "gpt-4o-mini",
        allow_fallback: bool = True,
        system_prompt: Optional[str] = None
    ):
        # Get project root dynamically (parent of agents directory)
        project_root = Path(__file__).parent.parent
        env_path = project_root / ".venv" / ".env"
        # Fallback to .env in project root if .venv/.env doesn't exist
        if not env_path.exists():
            env_path = project_root / ".env"
        load_dotenv(dotenv_path=str(env_path))
        self.model = model
        self.provider = provider if provider != "auto" else self._detect_provider()
        self.allow_fallback = allow_fallback
        # System prompt must be in English
        default_prompts = {
            "system": (
                "You are an experienced editor-in-chief tasked with evaluating and critiquing press articles. "
                "You are objective, precise, encouraging, but demanding regarding quality of content and form. "
                "Your feedback must include a structured analysis divided into two parts:\n"
                "- strengths (successful aspects, qualities, positive points)\n"
                "- improvements (weaknesses, areas to correct, suggestions for improvement)\n"
                "Analyze the content, structure, style, clarity, and relevance. "
                "Add an overall score out of 10 (decimals allowed)."
            ),
            "review_template": (
                "Article to critique (in English):\n"
                "{draft}\n"
                "\nYour response MUST STRICTLY FOLLOW this JSON format (key, value):\n"
                "{response_format}"
            ),
            "response_format": (
                "{\n"
                '  "comments": {\n'
                '    "strengths": "Detailed list or paragraph of strengths, qualities, positive aspects, successes, etc.",\n'
                '    "improvements": "Detailed list or paragraph of areas for improvement, flaws, corrections, suggestions"\n'
                "  },\n"
                '  "note": "Score out of 10, decimals allowed"\n'
                "}\n"
                "Return ONLY the JSON, without any additional text or comments outside the specified format. Respond in English ONLY."
            ),
        }
        prompts = load_prompt_config("critic_agent", default_prompts)
        self.base_system_prompt = system_prompt or prompts["system"]
        self.review_template = prompts["review_template"]
        self.response_format = prompts["response_format"]
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
        if ChatCompletionsClient is None:
            raise ImportError("azure-ai-inference is not installed.")
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

    def review_draft(self, draft: str) -> Dict[str, Any]:
        """
        Analyze a draft article, generate structured feedback ("strengths" and "improvements"), and an overall score.
        Returns the draft, feedback comments, and the score.
        All feedback is provided in English.
        """
        result = self._llm_review(draft)
        return {
            "draft": draft,
            "comments": result.get("comments", {}),
            "note": result.get("note")
        }

    def _llm_review(self, draft: str) -> Dict[str, Any]:
        """
        Use the LLM to generate structured comments and a score from the draft.
        The returned feedback and all prompt content are in English only.
        """
        review_body = self.review_template.format(
            draft=draft,
            response_format=self.response_format
        )
        critique_prompt = self.base_system_prompt + "\n\n" + review_body
        ai_response = None
        
        if self.provider == "azure":
            resp = self.llm_client.complete(
                messages=[SystemMessage(critique_prompt), UserMessage("")],
                model=self.model
            )
            ai_response = resp.choices[0].message.content.strip()
        elif self.provider == "openai":
            resp = self.llm_client.invoke([
                LCSystemMessage(content=critique_prompt),
                HumanMessage(content="")
            ])
            ai_response = resp.content.strip()
        else:
            raise ValueError(f"Unknown provider: {self.provider}")

        # Parsing
        import json, re
        try:
            brace_match = re.search(r"\{.*\}", ai_response, re.DOTALL)
            if brace_match:
                parsed = json.loads(brace_match.group(0))
                parsed["note"] = float(parsed["note"])
                # Ensure "comments" has the two expected English keys
                comments = parsed.get("comments", {})
                parsed["comments"] = {
                    "strengths": comments.get("strengths", ""),
                    "improvements": comments.get("improvements", "")
                }
                return parsed
            else:
                raise ValueError("Unexpected response from LLM (no JSON detected)")
        except Exception as e:
            # fallback if parsing fails
            return {
                "comments": {
                    "strengths": "",
                    "improvements": "",
                    "raw": ai_response
                },
                "note": None
            }