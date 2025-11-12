import re
import sys
from pathlib import Path

project_root = Path("/Users/perso/Documents/Agents/Agentic_Times")
sys.path.insert(0, str(project_root))

from agents.vector_db import VectorDBClient
from agents.analyser_collector import UserRequestFormatter, AnalyserCollector
from agents.plan_writer import PlanWriter
from agents.draft_writer import DraftWriter
from agents.critic_agent import CriticAgent
from agents.final_drafter import FinalDrafter


def exe(
    user_request: str,
    note_threshold: float = 8.0,
    max_iter: int = 5,
) -> Path:

    """
    Runs the full pipeline (analysis, plan, draft, critique) to produce a final
    HTML article styled like The Guardian. The resulting file is saved under
    `outputs/` with the article title as filename and the function returns the path.
    """
    formatter = UserRequestFormatter(
        provider="openai",
        model="gpt-4o-mini",
        allow_fallback=True
    )

    ROOT = project_root
    embeddings_path = ROOT / "data" / "vectors_base" / "embeddings.npy"
    metadata_path = ROOT / "data" / "vectors_base" / "metadata.jsonl"
    raw_dir = ROOT / "data" / "raw"

    vector_db_client = VectorDBClient(
        embeddings_path=str(embeddings_path),
        metadata_path=str(metadata_path),
        raw_dir=str(raw_dir) if raw_dir.exists() else None
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
    critic = CriticAgent(provider="openai")

    draft = writer.write_draft(user_request, plan, articles_context=context)
    review = critic.review_draft(draft)
    score = review.get("note", 0) if review.get("note") is not None else 0
    comments = review.get("comments", {})

    iterations = 1
    while score < note_threshold and iterations < max_iter:
        iterations += 1
        feedback = (
            "Strengths:\n" + str(comments.get("strengths", "")) + "\n\n"
            "Areas for improvement:\n" + str(comments.get("improvements", ""))
        )
        draft = writer.write_draft(
            user_request=user_request,
            plan=plan,
            articles_context=context,
            comments=feedback
        )
        review = critic.review_draft(draft)
        score = review.get("note", 0) if review.get("note") is not None else 0
        comments = review.get("comments", {})

    title_match = re.search(r"\[title\]\s*(.+)", draft or "")
    title = (title_match.group(1).strip() if title_match else "article") or "article"
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-") or "article"

    final_drafter = FinalDrafter()
    final_html = final_drafter.finalize_draft(
        draft,
        comments=comments,
        note=score,
    )

    output_dir = project_root / "outputs"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{slug}.html"
    output_path.write_text(final_html, encoding="utf-8")

    return output_path