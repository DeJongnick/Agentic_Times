import sys
from pathlib import Path

project_root = Path("/Users/perso/Documents/Agents/Agentic_Times")
sys.path.insert(0, str(project_root))

from agents.analyser_collector import UserRequestFormatter, AnalyserCollector
from agents.vector_db import VectorDBClient
from agents.plan_writer import PlanWriter

def get_context(user_request):
    """
    Takes a user_request and returns (context, plan).
    """
    formatter = UserRequestFormatter(
        provider="openai",
        model="gpt-4o-mini",
        allow_fallback=True
    )

    ROOT = project_root
    EMBEDDINGS_PATH = ROOT / "data" / "vectors_base" / "embeddings.npy"
    METADATA_PATH = ROOT / "data" / "vectors_base" / "metadata.jsonl"
    RAW_DIR = ROOT / "data" / "raw"

    vector_db_client = VectorDBClient(
        embeddings_path=str(EMBEDDINGS_PATH),
        metadata_path=str(METADATA_PATH),
        raw_dir=str(RAW_DIR) if RAW_DIR.exists() else None
    )

    analyser_collector = AnalyserCollector(
        vector_db_client=vector_db_client,
        top_k=6,
        similarity_threshold=0.3,
        request_formatter=formatter
    )

    context = analyser_collector.corpus_context(user_request)

    plan_writer = PlanWriter(provider="openai", model="gpt-4o-mini")

    plan = plan_writer.format(
        user_request=user_request,
        articles=context
    )

    return context, plan