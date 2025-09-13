# webhook_wrapper.tpl.py — AUTO-GENERATED lightweight outbound webhook client
import json
from typing import Optional, Dict
from urllib import request, error


class Webhooks:
    def __init__(
        self,
        base_url: Optional[str],
        headers: Optional[Dict[str, str]],
        routes: Optional[Dict[str, str]],
    ):
        self.base_url = base_url
        self.headers = headers or {}
        self.routes = routes or {}

    def emit(self, event: str, payload: Dict):
        """Fire-and-forget webhook. No-op if base_url or route is missing."""
        base = (self.base_url or "").rstrip("/")
        path = self.routes.get(event)
        if not base or not path:
            return  # disabled
        url = f"{base}{path}"
        data = json.dumps(payload).encode("utf-8")
        req = request.Request(url, data=data, method="POST")
        req.add_header("Content-Type", "application/json")
        for k, v in self.headers.items():
            req.add_header(k, v)
        try:
            request.urlopen(req, timeout=3.0)  # non-blocking-ish
        except error.URLError:
            # intentionally swallow errors to not break UX; replace with logging if desired
            pass
