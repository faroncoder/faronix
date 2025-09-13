#!/usr/bin/env python3
"""
Generate/Sync Django pages from the menu block inside core/context_processors.py.

Dynamic features:
- Auto-detects all groups/items in the block (no hard-coded lists).
- Creates templates/pages/<slug>.html, adds view functions and URL patterns.
- Idempotent; creates only missing pieces by default.

Sync options:
- --mode sync : also updates view titles when labels change.
- --sync-templates : updates template title block + H1 (conservative), and refreshes the // page:<slug> marker.
- --prune : (with --mode sync) remove urls/views for pages no longer present in the menu.

Usage examples:
  python3 tools/generate_pages.py
  python3 tools/generate_pages.py --mode sync --sync-templates
  python3 tools/generate_pages.py --mode sync --prune --sync-templates
  python3 tools/generate_pages.py --exclude-groups featured_pdfs,errors
"""

import argparse
import ast
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Set

MARK_BEGIN = "### SITE BEGIN"
MARK_END = "### SITE END"

DEFAULT_CONTEXT = "core/context_processors.py"
DEFAULT_VIEWS = "core/views_dynamic.py"
DEFAULT_URLS = "core/urls.py"
DEFAULT_TEMPLATES = "templates/pages"

TEMPLATE_HTML = """{# GPAGE META slug="__PAGE_SLUG__" title="__PAGE_TITLE__" #}
{% load static %}

{% block title %}{{ title }}{% endblock %}
{% block headcss %}{% endblock %}

{% block dynamic_content %}
    <div class="container py-4">
        <!-- GPAGE-H1 START -->{{ title }}
        <h1>Welcome to {{ title }}</h1>
        <!-- GPAGE-H1 END -->
        <p>This is the main content area for {{ title }}.</p>
    </div>
{% endblock %}

{% block extra_js %}
    <script>
       /*  document.addEventListener('DOMContentLoaded', function() {
            // page: __PAGE_SLUG__
        });
        
        */
    </script>
{% endblock %}
"""

VIEW_SNIPPET_IMPORT = "from django.views.decorators.http import require_http_methods\nfrom django.shortcuts import render\n"

VIEW_SNIPPET = """
@require_http_methods(["GET"])
def {page_slug}(request):
    context = {{'title': '{page_title}'}}
    return render(request, 'pages/{page_slug}.html', context=context)
"""


def ensure_view_import(views_py: Path):
    text = views_py.read_text(encoding="utf-8") if views_py.exists() else ""
    if VIEW_SNIPPET_IMPORT not in text:
        lines = text.splitlines(keepends=True)
        insert_at = 0
        if lines and lines[0].startswith("#!"):
            insert_at = 1
        if len(lines) > insert_at and lines[insert_at].strip().startswith('"""'):
            for i in range(insert_at + 1, len(lines)):
                if lines[i].strip().endswith('"""'):
                    insert_at = i + 1
                    break
        lines.insert(insert_at, VIEW_SNIPPET_IMPORT)
        views_py.write_text("".join(lines), encoding="utf-8")


URL_PATH_LINE_DIRECT = "    path('{page_slug}/', {page_slug}, name='{page_slug}'),"
# URL_PATH_LINE_VIEWSNS = "    path('{page_slug}/', views.{view_name}, name='{page_slug}'),"


def read_between_markers(text: str, start_mark: str, end_mark: str) -> str:
    on = False
    out = []
    for ln in text.splitlines():
        if start_mark in ln:
            on = True
            continue
        if end_mark in ln:
            break
        if on:
            out.append(ln)
    return "\n".join(out).strip()


def parse_menu_block(block: str) -> Dict:
    wrapped = "{\n" + block + "\n}"
    data = ast.literal_eval(wrapped)  # safe parser for Python literals
    menu = data.get("menu", {})
    if not isinstance(menu, dict):
        raise ValueError("'menu' is not a dict in the block")
    return menu


def slugify_label(label: str) -> str:
    s = label.lower()
    s = re.sub(r"&", " and ", s)
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s or "page"


def slug_from_urlname(url_name: str, fallback_label: str) -> str:
    # Prefer the tail after ":" (e.g., core:about-us -> about-us)
    part = url_name.split(":")[-1] if ":" in url_name else url_name
    part = part.strip()
    # Allow hyphens and underscores (e.g., error_400)
    if re.fullmatch(r"[a-z0-9]+(?:[-_][a-z0-9]+)*", part):
        return part
    return slugify_label(fallback_label)


def view_name_from_slug(slug: str) -> str:
    v = slug.replace("-", "_")
    if not re.match(r"^[A-Za-z_]", v):
        v = "page_" + v
    return v


def collect_pages(menu: Dict, exclude_groups: Set[str]) -> List[Tuple[str, str, str]]:
    """
    Return list of (slug, view_name, title). Deduplicate by slug (first wins).
    """
    seen = set()
    rows = []
    for group, items in menu.items():
        if exclude_groups and group in exclude_groups:
            continue
        if not isinstance(items, (list, tuple)):
            continue
        for it in items:
            label = it.get("label") or "Page"
            url_name = it.get("url_name") or label
            slug = slug_from_urlname(url_name, label)
            if slug in seen:
                continue
            seen.add(slug)
            rows.append((slug, view_name_from_slug(slug), label.strip()))
    return rows


def ensure_template_create(
    templates_dir: Path, page_slug: str, page_title: str
) -> bool:
    """Create template if missing. Returns True if created."""
    templates_dir.mkdir(parents=True, exist_ok=True)
    f = templates_dir / f"{page_slug}.html"
    if f.exists():
        return False
    content = TEMPLATE_HTML.replace("__PAGE_SLUG__", page_slug).replace(
        "__PAGE_TITLE__", page_title
    )
    f.write_text(content, encoding="utf-8")
    return True


def sync_template(path: Path, page_slug: str, page_title: str) -> bool:
    """
    Conservative template sync:
    - Update GPAGE META comment (if present) with slug/title.
    - Upgrade {% block title %}...{% endblock %} to {% firstof title site.title %} if not already.
    - Upgrade H1 (if within GPAGE-H1 markers) to Welcome to {% firstof title site.label %}.
      If markers absent, try to replace a classic line using site.label/title conservatively.
    - Refresh the JS comment: // page: <slug>
    Returns True if file changed.
    """
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8")
    orig = text

    # 1) Update GPAGE META
    if "{# GPAGE META" in text:
        text = re.sub(
            r'\{# GPAGE META slug="[^"]*" title="[^"]*"\s*#\}',
            f'{{# GPAGE META slug="{page_slug}" title="{page_title}" #}}',
            text,
        )
    else:
        # Optionally inject META at very top (keep user content intact)
        text = f'{{# GPAGE META slug="{page_slug}" title="{page_title}" #}}\n' + text

    # 2) Upgrade block title
    def repl_title_block(m):
        return "{% block title %}{% firstof title site.title %}{% endblock %}"

    text = re.sub(
        r"\{\%\s*block\s+title\s*\%\}[\s\S]*?\{\%\s*endblock\s*\%\}",
        repl_title_block,
        text,
        count=1,
    )

    # 3) Upgrade H1
    if "GPAGE-H1 START" in text and "GPAGE-H1 END" in text:
        text = re.sub(
            r"(<!-- GPAGE-H1 START -->)([\s\S]*?)(<!-- GPAGE-H1 END -->)",
            r"\1\n        <h1>Welcome to {% firstof title site.label %}</h1>\n        \3",
            text,
            count=1,
        )
    else:
        # Conservative fallback replacements (only if they match simple forms)
        text = re.sub(
            r"<h1>\s*Welcome to the\s*\{\{\s*site\.label\s*\}\}\s*</h1>",
            "<h1>Welcome to {% firstof title site.label %}</h1>",
            text,
        )
        text = re.sub(
            r"<h1>\s*Welcome to\s*\{\{\s*title\s*\}\}\s*</h1>",
            "<h1>Welcome to {% firstof title site.label %}</h1>",
            text,
        )

    # 4) Refresh JS comment marker
    text = re.sub(r"//\s*page:\s*[A-Za-z0-9\-_]+", f"// page: {page_slug}", text)

    changed = text != orig
    if changed:
        path.write_text(text, encoding="utf-8")
    return changed


def ensure_view(
    views_py: Path, view_name: str, page_title: str, page_slug: str, mode: str
) -> str:
    ensure_view_import(views_py)
    text = views_py.read_text(encoding="utf-8") if views_py.exists() else ""
    func_re = rf"(^def\s+{re.escape(view_name)}\s*\(request\):)([\s\S]*?)(?=^def\s|\Z)"
    m = re.search(func_re, text, flags=re.M)
    if not m:
        with views_py.open("a", encoding="utf-8") as w:
            w.write(
                VIEW_SNIPPET.format(
                    view_name=view_name,
                    page_title=page_title.replace("'", "\\'"),
                    page_slug=page_slug,
                )
            )
        return "added"

    if mode == "sync":
        start, end = m.span(2)
        body = m.group(2)
        safe_title = page_title.replace("'", "\\'")
        body_new = re.sub(
            r"context\s*=\s*\{\s*'title'\s*:\s*'[^']*'\s*\}",
            "context = {'title': '" + safe_title + "'}",
            body,
        )
        if body_new != body:
            new_text = text[:start] + body_new + text[end:]
            views_py.write_text(new_text, encoding="utf-8")
            return "updated"

    return "exists"


def urls_uses_views_namespace(text: str) -> bool:
    if re.search(r"^from\s+\.\s+import\s+views\s*$", text, re.M):
        return True
    if re.search(r"^import\s+core\.views\s+as\s+views\s*$", text, re.M):
        return True
    if re.search(r"^import\s+views\s*$", text, re.M):
        return True
    return False


def ensure_url_import_direct(text: str, view_name: str) -> str:
    if re.search(rf"^from\.views import .*?\b{re.escape(view_name)}\b", text, re.M):
        return text
    if re.search(r"^from\.views import ", text, re.M):

        def repl(m):
            line = m.group(0)
            if line.rstrip().endswith("import"):
                return f"{line} {view_name}"
            return f"{line}, {view_name}"

        return re.sub(r"^from\.views import [^\n]+", repl, text, count=1, flags=re.M)
    return f"from .views import {view_name}\n{text}"


def ensure_urlpattern(urls_py: Path, page_slug: str, view_name: str) -> str:
    text = urls_py.read_text(encoding="utf-8") if urls_py.exists() else ""
    if "from django.urls import path" not in text:
        text = f"from django.urls import path\n{text}"

    namespaced = urls_uses_views_namespace(text)
    if not namespaced:
        text = ensure_url_import_direct(text, view_name)

    if not re.search(r"^urlpatterns\s*=\s*\[", text, re.M):
        line = (URL_PATH_LINE_VIEWSNS if namespaced else URL_PATH_LINE_DIRECT).format(
            page_slug=page_slug, view_name=view_name
        )
        text += f"\nurlpatterns = [\n{line}\n]\n"
        urls_py.write_text(text, encoding="utf-8")
        return "added"

    pat = (
        rf"path\('{re.escape(page_slug)}/',\s*views\.{re.escape(page_slug)},\s*name='{re.escape(page_slug)}'\)"
        if namespaced
        else rf"path\('{re.escape(page_slug)}/',\s*{re.escape(page_slug)},\s*name='{re.escape(page_slug)}'\)"
    )
    if re.search(pat, text):
        urls_py.write_text(text, encoding="utf-8")
        return "exists"

    def add_before_closing(m):
        body = m.group(1)
        if body and body.strip() and not body.rstrip().endswith(","):
            body += ","
        line = (URL_PATH_LINE_VIEWSNS if namespaced else URL_PATH_LINE_DIRECT).format(
            page_slug=page_slug, view_name=view_name
        )
        body += "\n" + line
        return "urlpatterns = [" + body + "\n]\n"

    new_text, n = re.subn(
        r"urlpatterns\s*=\s*\[(.*?)\]\s*$", add_before_closing, text, flags=re.S
    )
    if n == 0:
        line = (URL_PATH_LINE_VIEWSNS if namespaced else URL_PATH_LINE_DIRECT).format(
            page_slug=page_slug, view_name=view_name
        )
        new_text = text + f"\nurlpatterns = [\n{line}\n]\n"

    urls_py.write_text(new_text, encoding="utf-8")
    return "added"


def find_existing_pages(urls_py: Path) -> Set[str]:
    if not urls_py.exists():
        return set()
    text = urls_py.read_text(encoding="utf-8")
    return set(re.findall(r"path\('([^']+)/',", text))


def prune_missing(urls_py: Path, views_py: Path, keep_slugs: Set[str]) -> List[str]:
    removed = []
    if urls_py.exists():
        text = urls_py.read_text(encoding="utf-8")

        def should_remove(m):
            slug = m.group(1)
            return slug not in keep_slugs

        new_text = re.sub(
            r"^\s*path\('([^']+)/',\s*[^)]+\),\s*$",
            lambda m: "" if should_remove(m) else m.group(0),
            text,
            flags=re.M,
        )
        if new_text != text:
            urls_py.write_text(new_text, encoding="utf-8")
            old_slugs = set(re.findall(r"path\('([^']+)/',", text))
            new_slugs = set(re.findall(r"path\('([^']+)/',", new_text))
            removed += sorted(old_slugs - new_slugs)

    if views_py.exists() and removed:
        text = views_py.read_text(encoding="utf-8")
        for slug in removed:
            view_name = view_name_from_slug(slug)
            func_re = rf"(^def\s+{re.escape(view_name)}\s*\(request\):)([\s\S]*?)(?=^def\s|\Z)"
            text, _ = re.subn(func_re, "", text, flags=re.M)
        views_py.write_text(text, encoding="utf-8")
    return removed


def main():
    ap = argparse.ArgumentParser(
        description="Generate/Sync Django pages from context menu block."
    )
    ap.add_argument("--context-file", default=DEFAULT_CONTEXT)
    ap.add_argument("--views", default=DEFAULT_VIEWS)
    ap.add_argument("--urls", default=DEFAULT_URLS)
    ap.add_argument("--templates-root", default=DEFAULT_TEMPLATES)
    ap.add_argument(
        "--mode",
        choices=["add", "sync"],
        default="add",
        help="'add' creates missing only; 'sync' also updates view titles.",
    )
    ap.add_argument(
        "--exclude-groups",
        default="featured_pdfs,errors",
        help="Comma-separated groups to ignore dynamically.",
    )
    ap.add_argument(
        "--exclude-slugs",
        default="",
        help="Comma-separated slugs to ignore dynamically.",
    )
    ap.add_argument(
        "--prune",
        action="store_true",
        help="(sync mode only) Remove urls/views for pages no longer in the menu.",
    )
    ap.add_argument(
        "--sync-templates",
        action="store_true",
        help="Conservatively sync template title block, H1, and page marker.",
    )
    args = ap.parse_args()

    ctx_path = Path(args.context_file)
    views_py = Path(args.views)
    urls_py = Path(args.urls)
    templates_dir = Path(args.templates_root)

    if not ctx_path.exists():
        print(f"[ERR] Context file not found: {ctx_path}", file=sys.stderr)
        sys.exit(1)

    ctx_text = ctx_path.read_text(encoding="utf-8")
    block = read_between_markers(ctx_text, MARK_BEGIN, MARK_END)
    if not block:
        print(
            f"[ERR] No block found between {MARK_BEGIN} and {MARK_END} in {ctx_path}",
            file=sys.stderr,
        )
        sys.exit(1)

    try:
        menu = parse_menu_block(block)
    except Exception as e:
        print(f"[ERR] Failed to parse menu block: {e}", file=sys.stderr)
        sys.exit(1)

    exclude_groups = {g.strip() for g in args.exclude_groups.split(",") if g.strip()}
    rows = collect_pages(menu, exclude_groups)

    exclude_slugs = {s.strip() for s in args.exclude_slugs.split(",") if s.strip()}
    rows = [r for r in rows if r[0] not in exclude_slugs]

    if not rows:
        print("[INFO] No pages to process after exclusions.")
        sys.exit(0)

    for slug, view_name, title in rows:
        created = ensure_template_create(templates_dir, slug, title)
        tpl_status = "created" if created else "exists"
        if args.sync_templates and not created:
            changed = sync_template(templates_dir / f"{slug}.html", slug, title)
            if changed:
                tpl_status = "synced"

        v_status = ensure_view(views_py, view_name, title, slug, mode=args.mode)
        u_status = ensure_urlpattern(urls_py, slug, view_name)
        print(f"{slug:25s}  tpl:{tpl_status:7s}  view:{v_status:8s}  url:{u_status:6s}")

    if args.mode == "sync" and args.prune:
        keep = {slug for slug, _, _ in rows}
        existing = find_existing_pages(urls_py)
        extras = sorted(existing - keep)
        if not extras:
            print("[INFO] No extra URLs to prune.")
        else:
            removed = prune_missing(urls_py, views_py, keep_slugs=keep)
            if removed:
                print("[PRUNE] Removed:", ", ".join(removed))
            else:
                print("[INFO] Nothing pruned.")


if __name__ == "__main__":
    main()
