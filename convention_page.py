"""Renders the Markdown documents in static/ as HTML (/documentation and /confidentialite).

A small converter for the Markdown these documents use (headings, tables, quotes, lists,
code, bold/italic, links), so the .md file stays the single source. Numbered headings get
stable anchors ("## 6. Balises" -> #regle-6, "### 8.5 ..." -> #regle-8-5) that the editor
links to, and "règle 8.5" / "voir 8.4" in the text become links.
"""
from __future__ import annotations

import html
import re
from pathlib import Path

SOURCE = Path(__file__).parent / "static" / "convention-transcription-prova-mg.md"
PRIVACY = Path(__file__).parent / "static" / "politique-confidentialite.md"
_cache: dict = {}

HEADING_RE = re.compile(r"^(#{1,4})\s+(.*)$")
NUMBERED_RE = re.compile(r"^(\d+(?:\.\d+)*)\.?\s+(.*)$")
RULE_REF_RE = re.compile(r"\b((?:règles?|voir)\s+)(\d+(?:\.\d+)?)\b")


def _slug(text: str) -> str:
    s = re.sub(r"[^\w\s-]", "", text.lower(), flags=re.U)
    return re.sub(r"[\s_]+", "-", s).strip("-") or "section"


def _inline(text: str) -> str:
    codes: list[str] = []

    def keep(m):
        codes.append(f"<code>{html.escape(m.group(1))}</code>")
        return f"\x00{len(codes) - 1}\x00"

    text = re.sub(r"`([^`]+)`", keep, text)
    text = html.escape(text, quote=False)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<em>\1</em>", text)
    text = re.sub(r"\[([^\]]+)\]\((https?://[^)\s]+)\)", r'<a href="\2" target="_blank" rel="noopener">\1</a>', text)
    text = re.sub(r"\[([^\]]+)\]\((/[^)\s]*)\)", r'<a href="\2">\1</a>', text)
    return re.sub(r"\x00(\d+)\x00", lambda m: codes[int(m.group(1))], text)


def _cells(line: str) -> list[str]:
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    # Split on | outside `code`.
    out, cur, in_code = [], "", False
    for ch in line:
        if ch == "`":
            in_code = not in_code
        if ch == "|" and not in_code:
            out.append(cur.strip())
            cur = ""
        else:
            cur += ch
    out.append(cur.strip())
    return out


def render(source: Path = SOURCE, prefix: str = "regle-") -> dict:
    """{"title", "version", "toc": [{id, label, children}], "html"} (cached on the file's mtime).
    `prefix` starts the anchors of numbered headings."""
    mtime = source.stat().st_mtime
    if source in _cache and _cache[source]["mtime"] == mtime:
        return _cache[source]["page"]
    lines = source.read_text("utf-8").splitlines()
    out: list[str] = []
    toc: list[dict] = []
    ids: set[str] = set()
    title, version = "Convention", ""
    i, skip_section = 0, False

    def unique(base: str) -> str:
        cid, n = base, 2
        while cid in ids:
            cid, n = f"{base}-{n}", n + 1
        ids.add(cid)
        return cid

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        m = HEADING_RE.match(stripped)
        if m:
            level, text = len(m.group(1)), m.group(2).strip()
            if level == 1:
                title = text
                i += 1
                continue
            if level == 2:
                # The Markdown table of contents is replaced by the navigation.
                skip_section = text.lower() == "sommaire"
                if skip_section:
                    i += 1
                    continue
            elif skip_section:
                i += 1
                continue
            num = NUMBERED_RE.match(text)
            cid = unique(prefix + num.group(1).replace(".", "-") if num else _slug(text))
            label = text
            if level == 2:
                toc.append({"id": cid, "label": label, "children": []})
            elif level == 3 and toc:
                toc[-1]["children"].append({"id": cid, "label": label})
            out.append(f'<h{level} id="{cid}"><a class="anchor" href="#{cid}" aria-label="Lien vers cette section">#</a>'
                       f"{_inline(text)}</h{level}>")
            i += 1
            continue
        if skip_section:
            if stripped == "---":
                skip_section = False
            i += 1
            continue
        if not stripped:
            i += 1
            continue
        if stripped == "---":
            out.append("<hr>")
            i += 1
            continue
        if stripped.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append(_cells(lines[i]))
                i += 1
            head, body = rows[0], [r for r in rows[1:] if not all(re.fullmatch(r":?-+:?", c) for c in r)]
            out.append('<div class="table-wrap"><table><thead><tr>' + "".join(f"<th>{_inline(c)}</th>" for c in head)
                       + "</tr></thead><tbody>" + "".join("<tr>" + "".join(f"<td>{_inline(c)}</td>" for c in r) + "</tr>"
                                                          for r in body) + "</tbody></table></div>")
            continue
        if stripped.startswith(">"):
            quote = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                quote.append(lines[i].strip()[1:].strip())
                i += 1
            out.append(f"<blockquote><p>{_inline(' '.join(quote))}</p></blockquote>")
            continue
        if re.match(r"^(-|\d+\.)\s+", stripped):
            ordered = bool(re.match(r"^\d+\.", stripped))
            items: list[str] = []
            while i < len(lines):
                cur = lines[i]
                mi = re.match(r"^(-|\d+\.)\s+(.*)$", cur.strip())
                if mi and not cur.startswith("  "):
                    items.append(mi.group(2))
                elif cur.startswith("  ") and cur.strip() and items:
                    # Indented line: continuation of the previous item.
                    items[-1] += "\n" + cur.strip()
                else:
                    break
                i += 1
            tag = "ol" if ordered else "ul"
            out.append(f"<{tag}>" + "".join(
                "<li>" + "<br>".join(_inline(part.lstrip("- ")) for part in item.split("\n")) + "</li>"
                for item in items) + f"</{tag}>")
            continue
        para = []
        while i < len(lines) and lines[i].strip() and not HEADING_RE.match(lines[i].strip()) \
                and not lines[i].strip().startswith(("|", ">", "---")) and not re.match(r"^(-|\d+\.)\s+", lines[i].strip()):
            para.append(lines[i].strip())
            i += 1
        text = " ".join(para)
        vm = re.search(r"v\d+\.\d+", text)
        marker = re.search(r"\b(?:CONVENTION|DOC)_VERSION ", text)
        if not version and marker and vm:
            version = vm.group(0)
            text = text.replace(marker.group(0), "")
        out.append(f"<p>{_inline(text)}</p>")

    body = "\n".join(out)

    def link(m):
        anchor = prefix + m.group(2).replace(".", "-")
        return f'{m.group(1)}<a href="#{anchor}">{m.group(2)}</a>' if anchor in ids else m.group(0)

    # Only outside tags and code: split the HTML on tags and touch text nodes only.
    parts = re.split(r"(<[^>]+>)", body)
    in_code = False
    for n, part in enumerate(parts):
        if part.startswith("<"):
            in_code = part.startswith("<code") or (in_code and not part.startswith("</code"))
            continue
        if not in_code:
            parts[n] = RULE_REF_RE.sub(link, part)
    page = {"title": title, "version": version, "toc": toc, "html": "".join(parts)}
    _cache[source] = {"mtime": mtime, "page": page}
    return page
