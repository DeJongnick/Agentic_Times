from __future__ import annotations

from html import escape
from typing import Any, Dict, Iterable, List, Optional, Union


class FinalDrafter:
    """
    Generate the final HTML article styled with a Guardian-inspired look & feel.
    The incoming draft is expected to use explicit tags:
      - [title] for the main headline
      - [subtitle] for section headings
      - [paragraph] for each paragraph-level block
    """

    def __init__(self, model: Optional[str] = None) -> None:
        self.model = model  # Placeholder for parity with other agents

    def finalize_draft(
        self,
        draft: str,
        comments: Optional[Union[str, Dict[str, Any]]] = None,
        note: Optional[float] = None,
    ) -> str:
        """
        Transform the tagged draft into a publish-ready HTML document.

        Args:
            draft: Raw draft content with [title], [subtitle], [paragraph] prefixes.
            comments: Optional critique or suggestions (unused in current implementation).
            note: Optional score from the critic agent (unused in current implementation).

        Returns:
            A complete HTML document string.
        """
        clean_lines = self._prepare_lines(draft)

        title_text: str = "Untitled Article"
        body_segments: List[str] = []

        for line in clean_lines:
            if line.startswith("[title]"):
                title_text = self._extract_content(line, "[title]")
                body_segments.append(self._render_title(title_text))
            elif line.startswith("[subtitle]"):
                subtitle_text = self._extract_content(line, "[subtitle]")
                body_segments.append(self._render_subtitle(subtitle_text))
            elif line.startswith("[paragraph]"):
                paragraph_text = self._extract_content(line, "[paragraph]")
                body_segments.append(self._render_paragraph(paragraph_text))
            else:
                body_segments.append(self._render_paragraph(line))

        if not any(segment.startswith("<h1") for segment in body_segments):
            # Fallback headline if none provided
            body_segments.insert(0, self._render_title(title_text))

        return self._wrap_html_document(title_text, body_segments)

    @staticmethod
    def _prepare_lines(draft: str) -> Iterable[str]:
        if not draft:
            return []
        return [line.strip() for line in draft.splitlines() if line.strip()]

    @staticmethod
    def _extract_content(line: str, tag: str) -> str:
        content = line[len(tag) :].strip()
        return content if content else tag

    @staticmethod
    def _render_title(text: str) -> str:
        return f'<h1 class="headline">{escape(text)}</h1>'

    @staticmethod
    def _render_subtitle(text: str) -> str:
        return f'<h2 class="standfirst">{escape(text)}</h2>'

    @staticmethod
    def _render_paragraph(text: str) -> str:
        return f'<p class="paragraph">{escape(text)}</p>'

    @staticmethod
    def _wrap_html_document(title: str, segments: List[str]) -> str:
        escaped_title = escape(title)
        body_html = "\n".join(segments)

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{escaped_title}</title>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Merriweather:wght@300;400;700&family=Roboto:wght@300;400;500&display=swap');

    body {{
      margin: 0;
      padding: 0;
      background-color: #f6f6f6;
      font-family: 'Roboto', Arial, Helvetica, sans-serif;
      color: #121212;
      line-height: 1.7;
    }}

    .article-container {{
      max-width: 760px;
      margin: 60px auto 80px auto;
      padding: 0 24px;
      background-color: #ffffff;
      box-shadow: 0 20px 40px rgba(0, 0, 0, 0.08);
      border-top: 6px solid #052962;
    }}

    .article-inner {{
      padding: 48px 36px 56px 36px;
    }}

    .headline {{
      font-family: 'Merriweather', 'Guardian Egyptian Headline', Georgia, serif;
      font-size: 42px;
      line-height: 1.1;
      margin: 0 0 24px 0;
      color: #121212;
    }}

    .standfirst {{
      font-family: 'Merriweather', 'Guardian Text Egyptian', Georgia, serif;
      font-size: 24px;
      line-height: 1.3;
      font-weight: 400;
      margin: 32px 0 16px 0;
      color: #5a5a5a;
    }}

    .paragraph {{
      font-size: 18px;
      margin: 0 0 20px 0;
      color: #2a2a2a;
    }}

    .paragraph:first-of-type {{
      margin-top: 12px;
    }}

    a {{
      color: #052962;
      text-decoration: none;
      border-bottom: 1px solid rgba(5, 41, 98, 0.4);
    }}

    a:hover {{
      border-bottom-color: #052962;
    }}
  </style>
</head>
<body>
  <div class="article-container">
    <div class="article-inner">
      {body_html}
    </div>
  </div>
</body>
</html>
"""

