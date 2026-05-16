"""
Markdown -> LaTeX converter for the academic preprints.

Handles the markdown subset used in paper.md: headers, bold/italic,
inline code, tables, ordered/unordered lists, links, inline math,
block quotes, horizontal rules, and the title/author header block at
the top of each paper.

Output is a standalone .tex file using the article class with hyperref,
booktabs, and standard packages. The output is intended for arxiv /
PsyArXiv submission with minor manual review.

Usage:
    python md_to_latex.py input.md output.tex
"""

from __future__ import annotations

import re
import sys
from typing import List


PREAMBLE = r"""\documentclass[11pt]{article}
\usepackage[margin=1in]{geometry}
\usepackage{microtype}
\usepackage{hyperref}
\usepackage{xcolor}
\usepackage{booktabs}
\usepackage{array}
\usepackage{tabularx}
\usepackage{amsmath}
\usepackage{verbatim}
\usepackage{titlesec}
\usepackage{parskip}
\usepackage{enumitem}
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}

\hypersetup{
  colorlinks=true,
  linkcolor=black,
  urlcolor=blue,
  citecolor=blue,
}

\titleformat*{\section}{\large\bfseries}
\titleformat*{\subsection}{\normalsize\bfseries}
\titleformat*{\subsubsection}{\normalsize\itshape}

\setlength{\parindent}{0pt}
\setlength{\parskip}{0.6em}

"""


# --------------------------------------------------------------------------
# Inline conversion
# --------------------------------------------------------------------------

# Order matters: process code spans first so we don't mangle their contents.

INLINE_CODE_RE = re.compile(r"`([^`\n]+)`")
BOLD_RE = re.compile(r"\*\*([^*\n]+)\*\*")
ITALIC_RE = re.compile(r"(?<!\*)\*([^*\n]+)\*(?!\*)")
EMPH_UNDERSCORE_RE = re.compile(r"(?<!\w)_([^_\n]+)_(?!\w)")
LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
INLINE_MATH_RE = re.compile(r"\$([^$\n]+)\$")
EM_DASH_RE = re.compile(r"---|—")
EN_DASH_RE = re.compile(r"--|–")
ELLIPSIS_RE = re.compile(r"\.{3}|…")


def escape_latex_text(text: str) -> str:
    """Escape LaTeX special characters in plain text segments."""
    # Order matters
    text = text.replace("\\", r"\textbackslash{}")
    text = text.replace("&", r"\&")
    text = text.replace("%", r"\%")
    text = text.replace("#", r"\#")
    text = text.replace("_", r"\_")
    text = text.replace("{", r"\{")
    text = text.replace("}", r"\}")
    text = text.replace("$", r"\$")
    text = text.replace("~", r"\textasciitilde{}")
    text = text.replace("^", r"\textasciicircum{}")
    text = text.replace("<", r"\textless{}")
    text = text.replace(">", r"\textgreater{}")
    text = text.replace('"', "''")
    return text


def convert_inline(line: str) -> str:
    """Convert markdown inline formatting to LaTeX, preserving code/math."""
    # Extract placeholders for things we don't want to escape
    placeholders: List[str] = []

    def stash(match, wrap):
        placeholders.append(wrap)
        return f"\x00{len(placeholders) - 1}\x00"

    # 1. Inline code (don't escape contents)
    line = INLINE_CODE_RE.sub(
        lambda m: stash(m, "\\texttt{" + m.group(1).replace("\\", r"\textbackslash{}").replace("_", r"\_").replace("#", r"\#").replace("&", r"\&").replace("%", r"\%").replace("$", r"\$") + "}"),
        line,
    )

    # 2. Inline math (preserve literally inside $...$)
    line = INLINE_MATH_RE.sub(lambda m: stash(m, "$" + m.group(1) + "$"), line)

    # 3. Links [text](url)
    line = LINK_RE.sub(
        lambda m: stash(m, "\\href{" + m.group(2) + "}{" + escape_latex_text(m.group(1)) + "}"),
        line,
    )

    # Now escape remaining special chars
    line = escape_latex_text(line)

    # Bold/italic (these use ** and * which survived escaping)
    line = BOLD_RE.sub(r"\\textbf{\1}", line)
    line = ITALIC_RE.sub(r"\\emph{\1}", line)
    line = EMPH_UNDERSCORE_RE.sub(r"\\emph{\1}", line)

    # Em-dashes and en-dashes
    line = EM_DASH_RE.sub("---", line)
    line = EN_DASH_RE.sub("--", line)
    line = ELLIPSIS_RE.sub(r"\\ldots{}", line)

    # Restore placeholders
    def restore(m):
        idx = int(m.group(1))
        return placeholders[idx]

    line = re.sub(r"\x00(\d+)\x00", restore, line)
    return line


# --------------------------------------------------------------------------
# Block-level conversion
# --------------------------------------------------------------------------

HEADER_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*$")
LIST_UNORDERED_RE = re.compile(r"^[-*+]\s+(.*)$")
LIST_ORDERED_RE = re.compile(r"^\d+\.\s+(.*)$")
HRULE_RE = re.compile(r"^---+\s*$")
BLOCKQUOTE_RE = re.compile(r"^>\s?(.*)$")
TABLE_ROW_RE = re.compile(r"^\|(.+)\|\s*$")
TABLE_DIV_RE = re.compile(r"^\|(\s*:?-+:?\s*\|)+\s*$")
CODE_FENCE_RE = re.compile(r"^```(\w*)\s*$")


def parse_blocks(text: str) -> List[dict]:
    """Parse markdown into a list of block dicts."""
    lines = text.replace("\r\n", "\n").split("\n")
    blocks: List[dict] = []
    i = 0
    while i < len(lines):
        line = lines[i]

        # Code fences
        m = CODE_FENCE_RE.match(line)
        if m:
            i += 1
            buf = []
            while i < len(lines) and not CODE_FENCE_RE.match(lines[i]):
                buf.append(lines[i])
                i += 1
            i += 1  # skip closing fence
            blocks.append({"type": "code", "content": "\n".join(buf)})
            continue

        # Headers
        m = HEADER_RE.match(line)
        if m:
            level = len(m.group(1))
            blocks.append({"type": "header", "level": level, "content": m.group(2)})
            i += 1
            continue

        # Horizontal rule
        if HRULE_RE.match(line):
            blocks.append({"type": "hrule"})
            i += 1
            continue

        # Tables
        if TABLE_ROW_RE.match(line) and i + 1 < len(lines) and TABLE_DIV_RE.match(lines[i + 1]):
            header_cells = [c.strip() for c in line.strip().strip("|").split("|")]
            i += 2  # skip header + divider
            rows = []
            while i < len(lines) and TABLE_ROW_RE.match(lines[i]):
                row_cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                rows.append(row_cells)
                i += 1
            blocks.append({"type": "table", "header": header_cells, "rows": rows})
            continue

        # Block quote
        if BLOCKQUOTE_RE.match(line):
            buf = []
            while i < len(lines) and BLOCKQUOTE_RE.match(lines[i]):
                buf.append(BLOCKQUOTE_RE.match(lines[i]).group(1))
                i += 1
            blocks.append({"type": "blockquote", "content": "\n".join(buf)})
            continue

        # Unordered list
        if LIST_UNORDERED_RE.match(line):
            items = []
            while i < len(lines) and LIST_UNORDERED_RE.match(lines[i]):
                items.append(LIST_UNORDERED_RE.match(lines[i]).group(1))
                i += 1
            blocks.append({"type": "ulist", "items": items})
            continue

        # Ordered list
        if LIST_ORDERED_RE.match(line):
            items = []
            while i < len(lines) and LIST_ORDERED_RE.match(lines[i]):
                items.append(LIST_ORDERED_RE.match(lines[i]).group(1))
                i += 1
            blocks.append({"type": "olist", "items": items})
            continue

        # Blank line: paragraph break
        if line.strip() == "":
            i += 1
            continue

        # Paragraph (consume until blank line, header, table, list, hrule)
        buf = [line]
        i += 1
        while i < len(lines):
            nxt = lines[i]
            if (nxt.strip() == "" or HEADER_RE.match(nxt) or HRULE_RE.match(nxt)
                    or LIST_UNORDERED_RE.match(nxt) or LIST_ORDERED_RE.match(nxt)
                    or BLOCKQUOTE_RE.match(nxt) or CODE_FENCE_RE.match(nxt)
                    or TABLE_ROW_RE.match(nxt)):
                break
            buf.append(nxt)
            i += 1
        blocks.append({"type": "paragraph", "content": " ".join(buf)})

    return blocks


def render_blocks(blocks: List[dict], title_info: dict) -> str:
    """Render parsed blocks as LaTeX."""
    out: List[str] = []
    in_abstract = False

    # Title block
    out.append(PREAMBLE)
    title = escape_latex_text(title_info.get("title", "Untitled"))
    out.append(r"\title{" + title + "}")

    author = title_info.get("author", "")
    if author:
        out.append(r"\author{" + escape_latex_text(author) + r"\\" + escape_latex_text(title_info.get("affiliation", "")) + "}")
    else:
        out.append(r"\author{}")

    out.append(r"\date{" + escape_latex_text(title_info.get("date", "")) + "}")
    out.append("")
    out.append(r"\begin{document}")
    out.append(r"\maketitle")
    out.append("")

    section_levels = {1: r"\section*", 2: r"\section", 3: r"\subsection",
                      4: r"\subsubsection", 5: r"\paragraph", 6: r"\subparagraph"}

    for blk in blocks:
        t = blk["type"]

        if t == "header":
            level = blk["level"]
            content = convert_inline(blk["content"])

            # Detect the Abstract section to wrap it in \begin{abstract}
            if blk["content"].strip().lower() == "abstract":
                out.append(r"\begin{abstract}")
                in_abstract = True
                continue

            # Close the abstract environment when the next H2 starts
            if in_abstract and level == 2:
                out.append(r"\end{abstract}")
                in_abstract = False

            cmd = section_levels.get(level, r"\section")
            # Strip leading "N. " or "N.N " section numbers from heading text
            text_for_section = re.sub(r"^\d+(\.\d+)*\.?\s+", "", blk["content"])
            text_for_section = convert_inline(text_for_section)
            out.append(cmd + "{" + text_for_section + "}")

        elif t == "paragraph":
            content = convert_inline(blk["content"])
            out.append(content)

        elif t == "code":
            out.append(r"\begin{verbatim}")
            out.append(blk["content"])
            out.append(r"\end{verbatim}")

        elif t == "hrule":
            out.append(r"\bigskip\hrule\bigskip")

        elif t == "blockquote":
            out.append(r"\begin{quote}")
            out.append(convert_inline(blk["content"]))
            out.append(r"\end{quote}")

        elif t == "ulist":
            out.append(r"\begin{itemize}[leftmargin=*]")
            for item in blk["items"]:
                out.append(r"  \item " + convert_inline(item))
            out.append(r"\end{itemize}")

        elif t == "olist":
            out.append(r"\begin{enumerate}[leftmargin=*]")
            for item in blk["items"]:
                out.append(r"  \item " + convert_inline(item))
            out.append(r"\end{enumerate}")

        elif t == "table":
            n_cols = len(blk["header"])
            col_spec = "l" * n_cols
            out.append(r"\begin{center}")
            out.append(r"\begin{tabular}{" + col_spec + "}")
            out.append(r"\toprule")
            out.append(" & ".join(r"\textbf{" + convert_inline(c) + "}" for c in blk["header"]) + r" \\")
            out.append(r"\midrule")
            for row in blk["rows"]:
                # pad row to match header length if needed
                while len(row) < n_cols:
                    row.append("")
                out.append(" & ".join(convert_inline(c) for c in row[:n_cols]) + r" \\")
            out.append(r"\bottomrule")
            out.append(r"\end{tabular}")
            out.append(r"\end{center}")

    if in_abstract:
        out.append(r"\end{abstract}")

    out.append(r"\end{document}")
    return "\n".join(out)


def extract_title_info(text: str) -> tuple[dict, str]:
    """Strip the title/author block from the top of the markdown.

    The papers have a leading structure:
        # Title

        (Optional subtitle line)

        Author Name
        Affiliation
        email

        *Draft preprint... etc.*

        ---

        ...rest of paper

    Returns the title_info dict plus the markdown body with the title
    block removed.
    """
    info = {"title": "", "author": "Heather Leffew, PhD",
            "affiliation": "Obelus Institute", "date": ""}
    lines = text.split("\n")
    body_start = 0

    # First H1 is the title
    for i, ln in enumerate(lines):
        m = HEADER_RE.match(ln)
        if m and len(m.group(1)) == 1:
            info["title"] = m.group(2).strip()
            body_start = i + 1
            break

    # Scan forward through the title block. Stop at the first "---" or
    # at the first "## " header. Anything in between is author/date metadata.
    j = body_start
    metadata_lines = []
    while j < len(lines):
        ln = lines[j].strip()
        if ln.startswith("## ") or HRULE_RE.match(ln):
            # Skip the --- if found
            if HRULE_RE.match(ln):
                j += 1
            break
        if ln:
            metadata_lines.append(ln)
        j += 1

    # Try to identify a date line in the metadata
    for ml in metadata_lines:
        if re.search(r"(?:January|February|March|April|May|June|July|August|September|October|November|December|preprint|Draft)", ml, re.I):
            info["date"] = re.sub(r"[*_]", "", ml).strip()
            break

    body = "\n".join(lines[j:])
    return info, body


def main():
    if len(sys.argv) != 3:
        print("Usage: python md_to_latex.py input.md output.tex")
        sys.exit(1)
    in_path = sys.argv[1]
    out_path = sys.argv[2]
    with open(in_path, encoding="utf-8") as f:
        md_text = f.read()
    title_info, body = extract_title_info(md_text)
    blocks = parse_blocks(body)
    latex = render_blocks(blocks, title_info)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(latex)
    print(f"Wrote {out_path}")
    print(f"  Title: {title_info['title'][:80]}")
    print(f"  Blocks: {len(blocks)}")


if __name__ == "__main__":
    main()
