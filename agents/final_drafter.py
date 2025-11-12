from __future__ import annotations

import re
from html import escape
from typing import Any, Dict, Iterable, List, Optional, Union
from datetime import datetime
from pathlib import Path


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
        date: Optional[str] = None,
        authors: Optional[Union[str, List[str]]] = None
    ) -> str:
        """
        Transform the tagged draft into a publish-ready HTML document.
        Args:
            draft: Raw draft content with [title], [subtitle], [paragraph] prefixes.
            comments: Optional critique or suggestions (unused in current implementation).
            note: Optional score from the critic agent (unused in current implementation).
            date: Optional publication date as string (e.g. "2024-06-10"); if None, today's date.
            authors: Optional author or list of authors; if None, defaults to "Unknown".
        Returns:
            A complete HTML document string.
        """
        clean_lines = self._prepare_lines(draft)

        title_text: str = "Untitled Article"
        header_segments: List[str] = []
        body_segments: List[str] = []
        title_inserted = False
        first_paragraph_rendered = False

        # Insert the title and collect other blocks
        for line in clean_lines:
            if line.startswith("[title]") and not title_inserted:
                title_text = self._extract_content(line, "[title]")
                header_segments.append(self._render_title(title_text))
                # Info block after the headline
                info_html = self._render_info_block(date, authors)
                header_segments.append(info_html)
                title_inserted = True
            elif line.startswith("[subtitle]"):
                subtitle_text = self._extract_content(line, "[subtitle]")
                body_segments.append(self._render_subtitle(subtitle_text))
                # Reset first paragraph flag after subtitle (new section)
                first_paragraph_rendered = False
            elif line.startswith("[paragraph]"):
                paragraph_text = self._extract_content(line, "[paragraph]")
                body_segments.append(self._render_paragraph(paragraph_text, is_first=not first_paragraph_rendered))
                first_paragraph_rendered = True
            else:
                body_segments.append(self._render_paragraph(line, is_first=not first_paragraph_rendered))
                first_paragraph_rendered = True

        if not any(segment.startswith("<h1") for segment in header_segments):
            # Fallback headline if none provided
            header_segments.insert(0, self._render_title(title_text))
            header_segments.insert(1, self._render_info_block(date, authors))

        return self._wrap_html_document(title_text, header_segments, body_segments)

    @staticmethod
    def _prepare_lines(draft: str) -> Iterable[str]:
        if not draft:
            return []
        return [line.strip() for line in draft.splitlines() if line.strip()]

    @staticmethod
    def _extract_content(line: str, tag: str) -> str:
        content = line[len(tag):].strip()
        return content if content else tag

    @staticmethod
    def _render_title(text: str) -> str:
        return f'<h1 class="headline">{escape(text)}</h1>'

    @staticmethod
    def _render_subtitle(text: str) -> str:
        return f'<h2 class="standfirst">{escape(text)}</h2>'

    @staticmethod
    def _process_citations(text: str) -> str:
        """
        Convert [source: filename.html] citations to simple hyperlinks.
        Replaces [source: filename.html] with just the article name as a clickable link.
        Also handles multiple citations: [source: file1.html] and [source: file2.html]
        """
        # Pattern to match [source: filename.html] - handles both single and multiple
        pattern = r'\[source:\s*([^\]]+)\]'
        
        def replace_citation(match):
            sources_text = match.group(1)
            # Split by 'and' or ',' to handle multiple sources
            sources = re.split(r'\s+and\s+|,\s*', sources_text)
            sources = [s.strip() for s in sources if s.strip()]
            
            citation_links = []
            for source in sources:
                # Clean the source filename
                source_clean = source.strip()
                # Create a relative path to the source file
                source_path = f"../data/raw/{source_clean}"
                # Extract readable name (remove .html and replace - with spaces, limit length)
                readable_name = source_clean.replace('.html', '').replace('-', ' ')
                # Capitalize first letter of each word, but keep it simple
                readable_name = ' '.join(word.capitalize() for word in readable_name.split())
                # Create simple link - just the readable name
                citation_links.append(f'<a href="{escape(source_path)}" class="source-citation">{escape(readable_name)}</a>')
            
            if len(citation_links) == 1:
                # Single source: just the link
                return citation_links[0]
            else:
                # Multiple citations: join with "and"
                citations_str = ', '.join(citation_links[:-1]) + f' and {citation_links[-1]}'
                return citations_str
        
        return re.sub(pattern, replace_citation, text)
    
    @staticmethod
    def _detect_pull_quote(text: str) -> tuple[str, Optional[str]]:
        """
        Detect if a paragraph contains a pull quote.
        Pull quotes are typically short, impactful quotes that can be extracted.
        Returns (remaining_text, pull_quote) or (text, None) if no pull quote.
        """
        # Pattern to detect quotes that might be pull quotes
        # Look for text in quotes that's between 20-150 characters
        quote_pattern = r'["""]([^"""]{20,150})["""]'
        matches = re.findall(quote_pattern, text)
        
        # If we find a good quote, extract it
        if matches:
            # Take the first substantial quote
            for quote in matches:
                if len(quote.strip()) >= 20:
                    # Remove the quote from the text and return both
                    # Replace the first occurrence of the quote
                    text_without_quote = text.replace(f'"{quote}"', '', 1)
                    text_without_quote = text_without_quote.replace(f'"{quote}"', '', 1)
                    return text_without_quote.strip(), quote.strip()
        
        return text, None
    
    @staticmethod
    def _render_pull_quote(quote: str) -> str:
        """Render a pull quote as a styled blockquote."""
        return f'<blockquote class="pull-quote">{escape(quote)}</blockquote>'
    
    @staticmethod
    def _render_paragraph(text: str, is_first: bool = False) -> str:
        # Check for pull quotes first (before processing citations)
        remaining_text, pull_quote = FinalDrafter._detect_pull_quote(text)
        
        # Process citations on remaining text (this returns HTML with links)
        processed_text = FinalDrafter._process_citations(remaining_text)
        
        # Now escape the text but preserve HTML links from citations
        # Split by HTML tags to preserve them
        parts = re.split(r'(<a[^>]*>.*?</a>)', processed_text)
        escaped_parts = []
        for part in parts:
            if part.startswith('<a') and part.endswith('</a>'):
                # This is already HTML link, don't escape
                escaped_parts.append(part)
            else:
                # Escape this part
                escaped_parts.append(escape(part))
        processed_text = ''.join(escaped_parts)
        
        # Build paragraph HTML
        if is_first:
            # Add drop cap for first paragraph
            # Find first non-HTML character (not part of a tag)
            first_char_match = re.search(r'^(<[^>]+>)*([^<\s&])', processed_text)
            if first_char_match:
                # Get everything before the first char and the first char itself
                before_char = first_char_match.group(1) if first_char_match.group(1) else ""
                first_char = first_char_match.group(2)
                # Get position after the match
                match_end = first_char_match.end()
                rest_text = processed_text[match_end:]
                paragraph_html = f'<p class="paragraph paragraph-first">{before_char}<span class="drop-cap">{escape(first_char)}</span>{rest_text}</p>'
            else:
                paragraph_html = f'<p class="paragraph paragraph-first">{processed_text}</p>'
        else:
            paragraph_html = f'<p class="paragraph">{processed_text}</p>'
        
        # Add pull quote if found
        if pull_quote:
            return paragraph_html + FinalDrafter._render_pull_quote(pull_quote)
        
        return paragraph_html

    @staticmethod
    def _render_info_block(date: Optional[str], authors: Optional[Union[str, List[str]]]) -> str:
        # Get date string (default: today, format for newspaper style)
        if not date:
            date_obj = datetime.now()
        else:
            try:
                date_obj = datetime.strptime(date, "%Y-%m-%d")
            except ValueError:
                date_obj = datetime.now()
        
        # Format date in newspaper style: "Monday, January 15, 2024"
        date_formatted = date_obj.strftime("%A, %B %d, %Y")
        date_text = escape(date_formatted)
        
        # Parse authors
        if authors is None or (isinstance(authors, str) and not authors.strip()):
            author_display = "Unknown"
            author_label = "Author"
        elif isinstance(authors, str):
            author_display = escape(authors)
            author_label = "Author"
        elif isinstance(authors, list):
            # Remove empty/blank authors
            authors_clean = [str(a).strip() for a in authors if str(a).strip()]
            if len(authors_clean) == 0:
                author_display = "Unknown"
                author_label = "Author"
            elif len(authors_clean) == 1:
                author_display = escape(authors_clean[0])
                author_label = "Author"
            else:
                author_display = ", ".join([escape(x) for x in authors_clean])
                author_label = "Authors"
        else:
            author_display = "Unknown"
            author_label = "Author"
        
        return f'<div class="article-meta"><span class="meta-date">{date_text}</span> <span class="meta-separator">|</span> <span class="meta-author">{author_label}: {author_display}</span></div>'

    @staticmethod
    def _wrap_html_document(title: str, header_segments: List[str], body_segments: List[str]) -> str:
        escaped_title = escape(title)
        header_html = "\n".join(header_segments)
        body_html = "\n".join(body_segments)

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{escaped_title}</title>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Merriweather:wght@300;400;700&family=Roboto:wght@300;400;500&display=swap');

    * {{
      box-sizing: border-box;
    }}

    body {{
      margin: 0;
      padding: 0;
      background-color: #f6f6f6;
      font-family: 'Roboto', Arial, Helvetica, sans-serif;
      color: #121212;
      line-height: 1.7;
    }}

    .article-container {{
      max-width: 1200px;
      margin: 40px auto;
      padding: 0;
      background-color: #ffffff;
      box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
      border-top: 6px solid #052962;
    }}

    .article-inner {{
      max-width: 1000px;
      margin: 0 auto;
      padding: 40px 50px 50px 50px;
      display: grid;
      grid-template-columns: 1fr;
      gap: 0;
    }}

    /* Header section - full width */
    .headline {{
      font-family: 'Merriweather', 'Guardian Egyptian Headline', Georgia, serif;
      font-size: 48px;
      line-height: 1.1;
      margin: 0 0 20px 0;
      color: #121212;
      font-weight: 700;
      grid-column: 1 / -1;
      border-bottom: 2px solid #e5e5e5;
      padding-bottom: 20px;
    }}

    .article-meta {{
      font-family: 'Roboto', Arial, Helvetica, sans-serif;
      font-size: 14px;
      color: #626262;
      margin-bottom: 30px;
      margin-top: 0;
      letter-spacing: 0.02em;
      text-transform: uppercase;
      grid-column: 1 / -1;
      border-bottom: 1px solid #e5e5e5;
      padding-bottom: 15px;
    }}

    .meta-date {{
      font-weight: 500;
    }}

    .meta-separator {{
      margin: 0 10px;
      color: #999;
    }}

    .meta-author {{
      font-weight: 400;
    }}

    /* Multi-column layout for body content - fixed 3 columns using CSS Grid */
    .article-body {{
      grid-column: 1 / -1;
      margin-top: 20px;
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      grid-auto-flow: row;
      gap: 30px;
      align-items: start;
    }}
    
    /* Paragraphs flow horizontally (row-wise) across columns */
    .article-body .paragraph {{
      margin-bottom: 16px;
      display: block;
      min-width: 0;
    }}
    
    /* Ensure paragraphs after subtitles start in first column */
    .standfirst + .paragraph {{
      grid-column: 1;
    }}

    .standfirst {{
      font-family: 'Merriweather', 'Guardian Text Egyptian', Georgia, serif;
      font-size: 22px;
      line-height: 1.4;
      font-weight: 400;
      margin: 40px 0 25px 0;
      color: #333;
      font-style: italic;
      border-left: 4px solid #052962;
      padding-left: 20px;
      grid-column: 1 / -1;
    }}

    .paragraph {{
      font-size: 17px;
      margin: 0 0 18px 0;
      color: #2a2a2a;
      text-align: justify;
      hyphens: auto;
      orphans: 2;
      widows: 2;
      break-inside: auto;
      page-break-inside: auto;
    }}

    .paragraph-first {{
      margin-top: 0;
    }}

    /* Drop cap styling */
    .drop-cap {{
      float: left;
      font-family: 'Merriweather', Georgia, serif;
      font-size: 80px;
      line-height: 60px;
      padding-top: 8px;
      padding-right: 8px;
      padding-left: 3px;
      color: #052962;
      font-weight: 700;
    }}

    /* Section dividers */
    .standfirst + .paragraph {{
      margin-top: 20px;
    }}

    /* References section */
    .references {{
      font-size: 13px;
      color: #666;
      margin-top: 40px;
      margin-bottom: 0;
      font-style: italic;
      line-height: 1.6;
      grid-column: 1 / -1;
      border-top: 1px solid #e5e5e5;
      padding-top: 20px;
    }}

    /* Links */
    a {{
      color: #052962;
      text-decoration: none;
      border-bottom: 1px solid rgba(5, 41, 98, 0.3);
      transition: border-bottom-color 0.2s;
    }}

    a:hover {{
      border-bottom-color: #052962;
    }}

    /* Source citations - British newspaper style */
    .source-citation {{
      color: #052962;
      font-weight: 500;
      border-bottom: 1px solid rgba(5, 41, 98, 0.4);
      text-decoration: none;
      font-style: normal;
    }}

    .source-citation:hover {{
      border-bottom-color: #052962;
      border-bottom-width: 2px;
    }}

    /* Pull quotes */
    .pull-quote {{
      font-family: 'Merriweather', Georgia, serif;
      font-size: 24px;
      line-height: 1.5;
      color: #052962;
      font-style: italic;
      font-weight: 400;
      margin: 30px 0;
      padding: 20px 30px;
      border-left: 4px solid #052962;
      border-right: 4px solid #052962;
      background-color: #f0f4f8;
      text-align: center;
      max-width: 80%;
      margin-left: auto;
      margin-right: auto;
      position: relative;
      grid-column: 1 / -1;
    }}

    .pull-quote::before {{
      content: '"';
      font-size: 60px;
      line-height: 0;
      position: absolute;
      left: 10px;
      top: 20px;
      color: #052962;
      opacity: 0.3;
      font-family: Georgia, serif;
    }}

    .pull-quote::after {{
      content: '"';
      font-size: 60px;
      line-height: 0;
      position: absolute;
      right: 10px;
      bottom: 10px;
      color: #052962;
      opacity: 0.3;
      font-family: Georgia, serif;
    }}

    /* Responsive design */
    @media (min-width: 1024px) {{
      .article-inner {{
        padding: 50px 80px 60px 80px;
      }}

      .article-body {{
        grid-template-columns: repeat(3, 1fr);
      }}

      .headline {{
        font-size: 56px;
      }}

      .standfirst {{
        font-size: 24px;
      }}

      .pull-quote {{
        font-size: 28px;
        padding: 30px 40px;
        max-width: 70%;
      }}
    }}

    @media (min-width: 768px) and (max-width: 1023px) {{
      .article-inner {{
        padding: 50px 60px 60px 60px;
      }}

      .article-body {{
        grid-template-columns: repeat(2, 1fr);
      }}

      .headline {{
        font-size: 52px;
      }}

      .pull-quote {{
        font-size: 26px;
        padding: 25px 35px;
      }}
    }}

    @media (max-width: 767px) {{
      .article-inner {{
        padding: 30px 25px 40px 25px;
      }}

      .article-body {{
        grid-template-columns: 1fr;
      }}

      .pull-quote {{
        font-size: 20px;
        padding: 15px 20px;
        max-width: 90%;
      }}
    }}

    /* Print styles */
    @media print {{
      .article-container {{
        box-shadow: none;
        border: none;
        max-width: 100%;
      }}

      .article-body {{
        grid-template-columns: repeat(2, 1fr);
      }}
    }}
  </style>
</head>
<body>
  <div class="article-container">
    <div class="article-inner">
      {header_html}
      <div class="article-body">
      {body_html}
      </div>
    </div>
  </div>
</body>
</html>
"""
