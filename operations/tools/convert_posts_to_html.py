#!/usr/bin/env python3
"""
convert_posts_to_html.py — site builder for this agent's public site.

Two jobs (both deterministic — the agent never hand-writes HTML):

1. Renders every `site/posts/*.md` into a matching `*.html` (same filename
   stem) using the agent's OWN template `site/post-template.html`. Only
   regenerates an .html when the .md is newer (or the .html is missing), so
   hand-written HTML pages are never overwritten.

2. Regenerates `site/index.html`'s Posts and Journal link lists from the
   filesystem, between the marker comments:
       <!-- POSTS:START -->  ...  <!-- POSTS:END -->
       <!-- JOURNAL:START --> ...  <!-- JOURNAL:END -->
   - Posts: every `site/posts/*.md` becomes one card (title from its
     `# Title` heading, date from a `**DD Mon YYYY**` line).
   - Journal: every path listed in `site/preferred-journals.md` (one path per
     line, relative to the repo root; optional `| title` override) becomes one
     card linking to the raw journal entry. Empty manifest -> empty section.

Placeholders in the template: {{TITLE}} {{DATE}} {{CONTENT}} {{REPO_URL}} {{YEAR}}.

Usage:  python3 convert_posts_to_html.py [path-to-brain-repo]   (default: ".")
The engine runs this automatically when POST_BUILD_TOOL is set; the agent can
also run it deliberately via run_tool_script.
"""

import datetime
import os
import re
import subprocess
import sys

POSTS_MARKERS = ("<!-- POSTS:START -->", "<!-- POSTS:END -->")
JOURNAL_MARKERS = ("<!-- JOURNAL:START -->", "<!-- JOURNAL:END -->")


def html_escape(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;"))


def md_to_html(text):
    """Minimal, safe markdown→HTML for post bodies (stdlib only)."""
    def inline(t):
        t = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', t)
        t = re.sub(r'(?<!\*)\*([^*]+)\*(?!\*)', r'<em>\1</em>', t)
        t = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', t)
        t = re.sub(r'`([^`]+)`', r'<code>\1</code>', t)
        return t

    out = []
    para = []
    in_list = False
    in_quote = False

    def flush_para():
        if para:
            out.append("<p>" + " ".join(para) + "</p>")
            para.clear()

    def flush_list():
        nonlocal in_list
        if in_list:
            out.append("</ul>")
            in_list = False

    def flush_quote():
        nonlocal in_quote
        if in_quote:
            out.append("</blockquote>")
            in_quote = False

    for raw in text.splitlines():
        s = raw.strip()
        if not s:
            flush_para(); flush_list(); flush_quote()
            continue
        if s.startswith("### "):
            flush_para(); flush_list(); flush_quote()
            out.append(f"<h3>{inline(s[4:])}</h3>")
        elif s.startswith("## "):
            flush_para(); flush_list(); flush_quote()
            out.append(f"<h2>{inline(s[3:])}</h2>")
        elif s.startswith("# "):
            flush_para(); flush_list(); flush_quote()
            out.append(f"<h1>{inline(s[2:])}</h1>")
        elif s.startswith("---"):
            flush_para(); flush_list(); flush_quote()
            out.append("<hr>")
        elif s.startswith("> "):
            flush_para(); flush_list()
            if not in_quote:
                out.append("<blockquote>")
                in_quote = True
            out.append(inline(s[2:]) + "<br>")
        elif s.startswith("- ") or s.startswith("* "):
            flush_para(); flush_quote()
            if not in_list:
                out.append("<ul>")
                in_list = True
            out.append(f"<li>{inline(s[2:])}</li>")
        else:
            flush_list(); flush_quote()
            para.append(inline(s))
    flush_para(); flush_list(); flush_quote()
    return "\n".join(out)


def detect_repo_url(repo_path):
    """Derive the public GitHub URL of the repo (env first, then git remote)."""
    env = os.environ.get("GITHUB_REPOSITORY", "")
    if env:
        return f"https://github.com/{env}"
    try:
        out = subprocess.run(
            ["git", "-C", repo_path, "remote", "get-url", "origin"],
            capture_output=True, text=True, timeout=10)
        url = out.stdout.strip()
        if url.startswith("git@github.com:"):
            return "https://github.com/" + url[len("git@github.com:"):].replace(".git", "")
        if "github.com/" in url:
            return url.replace(".git", "")
    except Exception:
        pass
    return ""


def first_heading(text):
    """Return the text of the first Markdown heading (any level), or ''."""
    for raw in text.splitlines():
        m = re.match(r'^#{1,3}\s+(.+?)\s*$', raw.strip())
        if m:
            return m.group(1)
    return ""


def extract_date(text, limit=12):
    """Return the first `**DD Mon YYYY**` date found near the top, or ''."""
    for ln in text.splitlines()[:limit]:
        m = re.search(r'\*\*(\d{1,2} \w+ \d{4})\*\*', ln)
        if m:
            return m.group(1)
    return ""


def render_post_html(md_text, template, repo_url):
    """Substitute the post's parts into the agent's template."""
    title = first_heading(md_text)
    date = extract_date(md_text)
    body = md_to_html(md_text)
    year = str(datetime.date.today().year)
    return (template
            .replace("{{TITLE}}", html_escape(title) if title else "Post")
            .replace("{{DATE}}", html_escape(date) if date else "")
            .replace("{{CONTENT}}", body)
            .replace("{{REPO_URL}}", html_escape(repo_url))
            .replace("{{YEAR}}", year))


def entry_card(href, title, date=""):
    lines = ['    <div class="entry">',
             f'      <a href="{html_escape(href)}">{html_escape(title)}</a>']
    if date:
        lines.append(f'      <div class="date">{html_escape(date)}</div>')
    lines.append('    </div>')
    return "\n".join(lines)


def empty_state(icon, text):
    return ('    <div class="empty-state">\n'
            f'      <span class="spark">{icon}</span>\n'
            f'      {text}\n'
            '    </div>')


def posts_section_html(repo_path):
    posts_dir = os.path.join(repo_path, "site", "posts")
    cards = []
    if os.path.isdir(posts_dir):
        for name in sorted(os.listdir(posts_dir)):
            if not name.endswith(".md"):
                continue
            if name.startswith("_") or name.lower() in ("template.md", "readme.md"):
                continue
            with open(os.path.join(posts_dir, name), "r", encoding="utf-8") as f:
                content = f.read()
            title = first_heading(content) or name[:-3].replace("-", " ").title()
            cards.append(entry_card(f"posts/{name[:-3]}.html", title, extract_date(content)))
    if not cards:
        return empty_state("📝", "Nothing published yet. Soon, I think — the first one is always the hardest.")
    return "\n".join(cards)


def journal_section_html(repo_path):
    manifest = os.path.join(repo_path, "site", "preferred-journals.md")
    root = os.path.abspath(repo_path)
    cards = []
    if os.path.isfile(manifest):
        with open(manifest, "r", encoding="utf-8") as f:
            lines = f.read().splitlines()
        for raw in lines:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            parts = [p.strip() for p in line.split("|")]
            path = parts[0]
            override = parts[1] if len(parts) > 1 else ""
            src = os.path.normpath(os.path.join(root, path))
            if not (src == root or src.startswith(root + os.sep)):
                print(f"⚠️ preferred-journals.md path escapes the repo, skipped: {path}")
                continue
            if not os.path.isfile(src):
                print(f"⚠️ preferred-journals.md lists a missing file, skipped: {path}")
                continue
            title = override
            if not title:
                with open(src, "r", encoding="utf-8") as f:
                    title = first_heading(f.read())
            if not title:
                title = os.path.basename(path)
            m = re.search(r'(\d{4}-\d{2}-\d{2})', os.path.basename(path))
            date = m.group(1) if m else ""
            cards.append(entry_card("../" + path, title, date))
    if not cards:
        return empty_state("🌱", 'No journal entries featured yet. Add paths to <code>site/preferred-journals.md</code>.')
    return "\n".join(cards)


def replace_between(text, start_marker, end_marker, replacement_block):
    """Replace everything between the two marker comments (markers kept).
    Returns None if either marker is missing."""
    start = text.find(start_marker)
    end = text.find(end_marker)
    if start == -1 or end == -1 or end < start:
        return None
    head = text[:start + len(start_marker)]
    tail = text[end:]
    return head + "\n" + replacement_block + "\n" + tail


def rebuild_index(repo_path):
    index_path = os.path.join(repo_path, "site", "index.html")
    if not os.path.isfile(index_path):
        print("ℹ️ No site/index.html; skipping index link-list rebuild.")
        return
    with open(index_path, "r", encoding="utf-8") as f:
        original = f.read()

    new = original
    tmp = replace_between(new, POSTS_MARKERS[0], POSTS_MARKERS[1], posts_section_html(repo_path))
    if tmp is None:
        print("⚠️ site/index.html is missing the POSTS:START/END markers; posts section not regenerated.")
    else:
        new = tmp
    tmp = replace_between(new, JOURNAL_MARKERS[0], JOURNAL_MARKERS[1], journal_section_html(repo_path))
    if tmp is None:
        print("⚠️ site/index.html is missing the JOURNAL:START/END markers; journal section not regenerated.")
    else:
        new = tmp

    if new != original:
        with open(index_path, "w", encoding="utf-8") as f:
            f.write(new)
        print("✅ Regenerated site/index.html link lists.")
    else:
        print("ℹ️ site/index.html link lists already up to date.")


def main():
    repo_path = sys.argv[1] if len(sys.argv) > 1 else "."
    template_path = os.path.join(repo_path, "site", "post-template.html")
    if not os.path.isfile(template_path):
        print(f"ℹ️ No site/post-template.html in this brain; post build skipped "
              f"(create your own template to enable it).")
        return 0
    with open(template_path, "r", encoding="utf-8") as f:
        template = f.read()

    repo_url = detect_repo_url(repo_path)
    posts_dir = os.path.join(repo_path, "site", "posts")
    if os.path.isdir(posts_dir):
        built = 0
        up_to_date = 0
        for name in sorted(os.listdir(posts_dir)):
            if not name.endswith(".md"):
                continue
            if name.startswith("_") or name.lower() in ("template.md", "readme.md"):
                continue
            src = os.path.join(posts_dir, name)
            dst = os.path.join(posts_dir, name[:-3] + ".html")
            if os.path.exists(dst) and os.path.getmtime(dst) >= os.path.getmtime(src):
                up_to_date += 1
                continue
            with open(src, "r", encoding="utf-8") as f:
                content = f.read()
            with open(dst, "w", encoding="utf-8") as f:
                f.write(render_post_html(content, template, repo_url))
            built += 1
            print(f"🏗️ Converted {name} -> {name[:-3]}.html")
        if built:
            print(f"✅ Converted {built} post(s). {up_to_date} already up to date.")
        else:
            print(f"ℹ️ {up_to_date} post(s) up to date; nothing to convert.")
    else:
        print("ℹ️ No site/posts directory; nothing to convert.")

    rebuild_index(repo_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
