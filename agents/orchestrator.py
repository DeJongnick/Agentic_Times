import re
import sys
from datetime import datetime
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
    authors: list[str] | None = 'Nicolas Le Jeune',
    note_threshold: float = 8.0,
    max_iter: int = 5,
) -> Path:

    """
    Runs the full pipeline (analysis, plan, draft, critique) to produce a final
    HTML article styled like The Guardian. The resulting file is saved under
    `outputs/` with the article title as filename and the function returns the path.

    Args:
        user_request: The end-user's prompt describing the desired article.
        authors: Optional list of author names to display in the final article.
        note_threshold: Minimum acceptable critic score before stopping iterations.
        max_iter: Maximum number of draft/critique refinement loops.
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

    combined_feedback: str | None = None
    draft = ""
    review: dict[str, object] = {}
    score = 0.0
    comments: dict[str, str] = {}

    human_satisfied = False

    for iteration in range(1, max_iter + 1):
        draft = writer.write_draft(
            user_request=user_request,
            plan=plan,
            articles_context=context,
            comments=combined_feedback,
        )
        review = critic.review_draft(draft)
        score = review.get("note", 0) if review.get("note") is not None else 0
        comments = review.get("comments", {})

        feedback_from_critic = (
            "Strengths:\n" + str(comments.get("strengths", "")) + "\n\n"
            "Areas for improvement:\n" + str(comments.get("improvements", ""))
        )

        print(f"\n--- Iteration {iteration} ---")
        print(f"Critic note: {score} / 10 (threshold: {note_threshold})")
        print("\nCurrent article draft:\n")
        print(draft)

        while True:
            user_answer = input("Satisfied? (y/n): ").strip().lower()
            if user_answer in {"y", "yes", "n", "no"}:
                human_satisfied = user_answer in {"y", "yes"}
                break
            print("Please answer with 'y' or 'n'.")

        if human_satisfied:
            break

        user_feedback = input(
            "Please provide your feedback for improvements (leave empty to rely on critic comments):\n"
        ).strip()

        combined_feedback = feedback_from_critic
        if user_feedback:
            combined_feedback += "\n\nUser feedback:\n" + user_feedback

        if iteration >= max_iter:
            print("Maximum number of iterations reached.")
        elif score >= note_threshold:
            print("Critic note meets the threshold, but will refine based on your feedback.")

    title_match = re.search(r"\[title\]\s*(.+)", draft or "")
    title = (title_match.group(1).strip() if title_match else "article") or "article"
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-") or "article"

    final_drafter = FinalDrafter()
    final_html = final_drafter.finalize_draft(
        draft,
        comments=comments,
        note=score,
        date=datetime.now().strftime("%Y-%m-%d"),
        authors=authors,
    )

    output_dir = project_root / "outputs"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{slug}.html"
    output_path.write_text(final_html, encoding="utf-8")

    return output_path