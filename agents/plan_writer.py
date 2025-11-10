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
    def __init__(self, model=None):
        """
        Initialise le PlanWriter avec un modèle LangChain (ex: ChatOpenAI) pour la génération de plan.
        Args:
            model: Un modèle LangChain (comme ChatOpenAI).
        """
        self.model = model  # Doit être une instance LangChain, ex: ChatOpenAI

    def write_plan(self, user_request, corpus_context):
        """
        Génère un plan détaillé à partir de la requête utilisateur ET du contexte corpus.
        Args:
            user_request (str): La demande de l'utilisateur.
            corpus_context (list|dict): Le contexte corpus (ex: articles, extraits pertinents, etc.).
        Returns:
            str: Le plan détaillé généré.
        """
        # À implémenter : logiques de génération de plan à partir de user_request + corpus_context
        # Idéalement, la génération exploite le modèle si fourni.
        pass