# 📄 Manifest Dashboard Example

This example showcases how Faronix can serve **versioned JSON manifests** directly from disk and present them to developers using a clean, HTMX-powered interface.

---

## 🧪 What It Does

- Reads `.json` files from `/media/manifest/v*/`
- Supports multiple manifest versions (`v2025-09-13`, etc.)
- Lists files like:
  - `index.json`
  - `roles.json`
  - `features.json`
  - `snippets.json`
  - `menu.json`
- Provides a dropdown to switch between manifest versions
- Renders selected file content into an HTMX viewer
- Fully decoupled from Django's internal DB — file-based architecture
- Optional: watch folder with `inotify` for real-time updates

---

## 🛠 File Structure

```bash
examples/manifest_dashboard/
├── manifest/
│   ├── v2025-09-13/
│   │   ├── index.json
│   │   ├── roles.json
│   │   ├── features.json
│   │   ├── snippets.json
│   │   └── menu.json
├── templates/
│   └── manifest_dashboard.html
├── views/
│   └── manifest_views.py
└── README.md
