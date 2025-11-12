import sys
from pathlib import Path

project_root = Path("/Users/perso/Documents/Agents/Agentic_Times")
sys.path.insert(0, str(project_root))

from agents.vector_db import VectorDBClient
from agents.analyser_collector import UserRequestFormatter, AnalyserCollector
from agents.plan_writer import PlanWriter
from agents.draft_writer import DraftWriter
from agents.critic_agent import CriticAgent

def exe(user_request):
    """
    Takes a user_request and returns the generated draft article.
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

    writer = DraftWriter(provider="openai")
    draft = writer.write_draft(user_request, plan, articles_context=context)

    return draft

def evaluate(article: str):
    """
    Evaluate the given article using the CriticAgent.
    Prints the feedback comments and score.
    """
    from agents.critic_agent import CriticAgent

    agent = CriticAgent(
        provider="openai")

    result = agent.review_draft(article)
    print("Comments:\n", result["comments"])
    print("Score out of 10:", result["note"])

def iterative_draft_improve(user_request, 
                            note_threshold=8.0, 
                            max_iter=5):
    """
    Takes the user_request, generates an initial draft (via exe),
    then iteratively evaluates and rewrites the draft with feedback if
    the score is below the threshold, up to a maximum number of iterations.
    Returns a dictionary with the number of iterations, the final result,
    the final score, comments, plan, and context.
    """
    writer = DraftWriter(provider="openai")
    critic = CriticAgent(provider="openai")

    # Rebuild the entire process to have context and plan
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

    draft = writer.write_draft(user_request, plan, articles_context=context)
    result = critic.review_draft(draft)
    score = result.get("note", 0) if result.get("note") is not None else 0
    comments = result.get("comments", {})

    i = 1
    while score < note_threshold and i < max_iter:
        # Use critic feedback to improve the article
        i += 1
        feedback = (
            "Strengths:\n" + str(comments.get("strengths", "")) + "\n\n" +
            "Areas for improvement:\n" + str(comments.get("improvements", ""))
        )
        draft = writer.write_draft(
            user_request=user_request,
            plan=plan,
            articles_context=context,
            comments=feedback
        )
        result = critic.review_draft(draft)
        score = result.get("note", 0) if result.get("note") is not None else 0
        comments = result.get("comments", {})

    return {
        "iterations": i,
        "final_draft": draft,
        "final_score": score,
        "comments": comments,
        "plan": plan,
        "context": context
    }