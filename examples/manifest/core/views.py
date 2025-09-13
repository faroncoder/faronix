from django.http import HttpResponse
from django.template.loader import render_to_string
import json
from pathlib import Path
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse, Http404



BASE_MANIFEST_PATH = Path("/home/faron/app_pwa/media/manifest")

def manifest_dashboard(request):
    if not BASE_MANIFEST_PATH.exists():
        BASE_MANIFEST_PATH.mkdir(parents=True, exist_ok=True)

    # Get all versions
    versions = list_manifest_versions()
    if not versions:
        return HttpResponse("<h2>No manifest versions found.</h2>", status=404)

    # Get selected version from GET param or fallback to latest
    selected = request.GET.get("v", versions[0])
    selected_path = BASE_MANIFEST_PATH / selected

    # List manifest files inside selected version
    manifest_files = [f.name for f in selected_path.glob("*.json")] if selected_path.exists() else []

    return render(request, "manifest_dashboard.html", {
        "manifest_names": manifest_files,
        "version": selected,
        "all_versions": versions
    })


def load_manifest(request, name):
    try:
        versions = sorted([d for d in BASE_MANIFEST_PATH.iterdir() if d.is_dir()], reverse=True)
        latest = versions[0] if versions else None

        if not latest:
            raise Http404("No versioned manifest folder found.")

        file_path = latest / name

        if not file_path.exists():
            raise Http404(f"Manifest {name} not found")

        with open(file_path, "r", encoding="utf-8") as f:
            content = json.load(f)

        return HttpResponse(f"<h2>{name}</h2><pre>{json.dumps(content, indent=2)}</pre>")
    except Exception as e:
        return HttpResponse(f"<h1>Error loading manifest</h1><pre>{e}</pre>", status=500)


def load_revcat_snippet(request):
    platform = request.GET.get("platform", "web")
    entitlement = request.GET.get("entitlement", "pro")
    license_type = request.GET.get("license_type", "public")

    template_path = f"revcat/snippets/{platform}.tpl"

    try:
        html = render_to_string(
            template_path,
            {
                "entitlement": entitlement,
                "license_type": license_type,
            },
        )
    except Exception as e:
        return HttpResponse(f"Error: {str(e)}", status=500)

    return HttpResponse(html, content_type="application/javascript")



def list_manifest_versions():
    return sorted(
        [d.name for d in BASE_MANIFEST_PATH.iterdir() if d.is_dir()],
        reverse=True
    )

import difflib

def diff_manifest_versions(request):
    version_a = request.GET.get("a")
    version_b = request.GET.get("b")

    if not version_a or not version_b:
        return HttpResponse("<p>⚠️ Select both versions to compare.</p>")

    path_a = BASE_MANIFEST_PATH / version_a / "bootstrap.json"
    path_b = BASE_MANIFEST_PATH / version_b / "bootstrap.json"

    if not path_a.exists() or not path_b.exists():
        return HttpResponse("<p>❌ One of the selected versions is missing bootstrap.json</p>")

    text_a = path_a.read_text().splitlines()
    text_b = path_b.read_text().splitlines()

    html_diff = difflib.HtmlDiff().make_table(text_a, text_b, fromdesc=version_a, todesc=version_b)

    return HttpResponse(f"<div class='diff-table'>{html_diff}</div>")
