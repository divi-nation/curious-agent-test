#!/usr/bin/env python3
"""
convert_posts_to_html.py — Rebuild HTML for every post in site/posts/.

Reads each site/posts/*.md in the brain repo, renders it to a matching *.html
(same filename stem) using the agent's OWN template site/post-template.html,
and writes it back. Only regenerates an .html when the .md is newer (or the
.html is missing), so hand-written HTML pages are never overwritten.

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


def render_post_html(md_text, template, repo_url):
    """Substitute the post's parts into the agent's template."""
    lines = md_text.splitlines()
    title = ""
    for ln in lines:
        if ln.startswith("# "):
            title = ln[2:].strip()
            break
    date = ""
    for ln in lines[:12]:
        m = re.search(r'\*\*(\d{1,2} \w+ \d{4})\*\*', ln)
        if m:
            date = m.group(1)
            break
    body = md_to_html("\n".join(lines))
    year = str(datetime.date.today().year)
    return (template
            .replace("{{TITLE}}", html_escape(title) if title else "Post")
            .replace("{{DATE}}", html_escape(date) if date else "")
            .replace("{{CONTENT}}", body)
            .replace("{{REPO_URL}}", html_escape(repo_url))
            .replace("{{YEAR}}", year))


def main():
    repo_path = sys.argv[1] if len(sys.argv) > 1 else "."
    template_path = os.path.join(repo_path, "site", "post-template.html")
    if not os.path.isfile(template_path):
        print(f"ℹ️ No site/post-template.html in this brain; post build skipped "
              f"(create your own template to enable it).")
        return 0
    with open(template_path, "r", encoding="utf-8") as f:
        template = f.read()

    posts_dir = os.path.join(repo_path, "site", "posts")
    if not os.path.isdir(posts_dir):
        print("ℹ️ No site/posts directory; nothing to do.")
        return 0
    repo_url = detect_repo_url(repo_path)
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
    return 0


if __name__ == "__main__":
    sys.exit(main())