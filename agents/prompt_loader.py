from pathlib import Path
import re
from typing import Dict, Optional

PROJECT_ROOT = Path("/Users/perso/Documents/Agents/Agentic_Times")
PROMPTS_DIR = PROJECT_ROOT / "prompts"

_SECTION_PATTERN = re.compile(r"^\[\[(?P<section>[A-Za-z0-9_\-]+)\]\]\s*$")


def _parse_prompt_sections(text: str) -> Dict[str, str]:
    """
    Parse a prompt file into sections. Sections are declared with `[[section_name]]`.
    Lines before the first section belong to the `default` section.
    """
    sections: Dict[str, list[str]] = {}
    default_lines: list[str] = []
    current_section: Optional[str] = None

    for raw_line in text.splitlines():
        line = raw_line.rstrip("\n")
        match = _SECTION_PATTERN.match(line.strip())
        if match:
            current_section = match.group("section").strip().lower()
            sections.setdefault(current_section, [])
            continue
        if current_section is None:
            default_lines.append(raw_line)
        else:
            sections[current_section].append(raw_line)

    results: Dict[str, str] = {}
    if sections:
        for name, lines in sections.items():
            content = "\n".join(lines).strip()
            if content:
                results[name] = content
    joined_default = "\n".join(default_lines).strip()
    if joined_default:
        results["default"] = joined_default
    if not results and text.strip():
        results["default"] = text.strip()
    return results


def _load_prompt_file(prompt_name: str) -> Dict[str, str]:
    prompt_path = PROMPTS_DIR / f"{prompt_name}.txt"
    if not prompt_path.exists():
        return {}
    try:
        content = prompt_path.read_text(encoding="utf-8")
    except OSError:
        return {}
    return _parse_prompt_sections(content)


def load_prompt(prompt_name: str, default: str, section: str = "default") -> str:
    """
    Load a specific prompt section for the given agent.

    Args:
        prompt_name: Base filename (without extension) that identifies the prompt.
        default: Fallback prompt text if no custom prompt file or section is found.
        section: Name of the section to retrieve (case-insensitive). Defaults to 'default'.

    Returns:
        The custom prompt content if available, otherwise the provided default.
    """
    sections = _load_prompt_file(prompt_name)
    if not sections:
        return default
    section_key = section.lower()
    if section_key in sections:
        return sections[section_key]
    if section_key != "default" and "default" in sections:
        return sections["default"]
    return default


def load_prompt_config(prompt_name: str, defaults: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    """
    Load a mapping of prompt sections for an agent, applying the provided defaults
    when no custom value is supplied.
    """
    sections = dict(defaults or {})
    custom_sections = _load_prompt_file(prompt_name)
    if custom_sections:
        sections.update(custom_sections)
    return sections

