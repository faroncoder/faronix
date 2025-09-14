from email import errors
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
INDEX_PATH = ROOT / "tpl" / "component_index.json"

# minimal runtime components we expect in your /tpl library
REQUIRED_FORM_COMPONENTS = {"TextField.tpl", "CheckboxField.tpl"}
GENERIC_TABLE_COMPONENT = "DataTable.tpl"


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: yofaron_validator.py <spec.json>")
        return 2

    spec_path = ROOT / sys.argv[1]
    if not spec_path.exists():
        print(f"❌ Spec not found: {spec_path}")
        return 2
    if not INDEX_PATH.exists():
        print(f"❌ Missing {INDEX_PATH} (run generate_component_index.py first)")
        return 2

    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    index = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    comps = index.get("components", {})

    errors = []

    # required top-level keys
    for k in ("app_label", "view_name", "tabs"):
        if k not in spec:
            errors.append(f"Spec missing key: {k}")
    # tab checks
    seen = set()
    for t in spec.get("tabs", []):
        slug = t.get("slug")
        if not slug:
            errors.append("tab missing slug")
            continue
        if slug in seen:
            errors.append(f"duplicate tab slug: {slug}")
        seen.add(slug)

        if "form_template" not in t or not isinstance(t["form_template"], str):
            errors.append(f"tab {slug} missing valid form_template")

        # table component exists?
        comp = (t.get("table") or {}).get("component")
        if comp:
            present = any(comp in names for names in comps.values())
            if not present:
                errors.append(f"tab {slug} references missing component '{comp}'")

    # model sanity
    if spec.get("model") and not isinstance(spec.get("fields"), list):
        errors.append("model declared but 'fields' is not a list")

    # runtime requirements
    have_forms = set(comps.get("forms", []))
    missing = sorted(REQUIRED_FORM_COMPONENTS - have_forms)
    if missing:
        errors.append("missing runtime /tpl/forms components: " + ", ".join(missing))

    have_tables = set(comps.get("tables", []))
    if GENERIC_TABLE_COMPONENT not in have_tables:
        errors.append(f"missing runtime /tpl/tables/{GENERIC_TABLE_COMPONENT}.html")

    if errors:
        print("❌ Validation failed:")
        for e in errors:
            print("  -", e)
        return 1

    print("✅ Spec validated successfully")
    return 0


if __name__ == "__main__":
    sys.exit(main())
