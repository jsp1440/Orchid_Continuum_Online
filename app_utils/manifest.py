from __future__ import annotations
import json, os, time
from pathlib import Path
from typing import Any, Dict, List, Tuple

_MANIFEST_PATH = Path("WIDGET_DEPLOYMENT_MANIFEST.json")
_CACHE: Dict[str, Any] = {}
_CACHE_MTIME: float | None = None
_ENV = os.getenv("APP_ENV", "dev")

def _needs_reload() -> bool:
    global _CACHE_MTIME
    if not _MANIFEST_PATH.exists():
        return _CACHE_MTIME is None  # load once to set empty
    mtime = _MANIFEST_PATH.stat().st_mtime
    if _CACHE_MTIME is None:
        return True
    if _ENV != "prod":
        return mtime > _CACHE_MTIME  # hot reload in dev
    return False

def _load_manifest() -> Dict[str, Any]:
    global _CACHE, _CACHE_MTIME
    if not _MANIFEST_PATH.exists():
        _CACHE = {"pages": [], "widgets_flat": [], "errors": ["Manifest file not found."]}
        _CACHE_MTIME = time.time()
        return _CACHE
    try:
        data = json.loads(_MANIFEST_PATH.read_text(encoding="utf-8"))
        # Normalize into {"pages":[{page,widgets:[...] }], "widgets_flat":[...]}
        pages = []
        widgets_flat = []
        if isinstance(data, list):
            for page_block in data:
                page = str(page_block.get("page", "")).strip()
                widgets = page_block.get("widgets", []) or []
                norm_widgets = []
                for w in widgets:
                    name = str(w.get("name","")).strip()
                    entry = {
                        "name": name,
                        "type": w.get("type",""),
                        "delivery": w.get("delivery","cdn").lower(),
                        "status": w.get("status","inactive").lower(),
                        "notes": w.get("notes",""),
                        "page": page,
                    }
                    norm_widgets.append(entry)
                    if entry["status"] in ("active","restricted"):
                        widgets_flat.append(entry)
                pages.append({"page": page, "widgets": norm_widgets})
        _CACHE = {"pages": pages, "widgets_flat": widgets_flat, "errors": []}
        _CACHE_MTIME = _MANIFEST_PATH.stat().st_mtime
        return _CACHE
    except Exception as e:
        _CACHE = {"pages": [], "widgets_flat": [], "errors": [f"Manifest parse error: {e}"]}
        _CACHE_MTIME = time.time()
        return _CACHE

def get_manifest() -> Dict[str, Any]:
    if _needs_reload():
        return _load_manifest()
    return _CACHE

def is_widget_active(name: str) -> bool:
    mf = get_manifest()
    for w in mf.get("widgets_flat", []):
        if w.get("name","").lower() == name.lower():
            return w.get("status") in ("active","restricted")
    return False

def active_widgets_for(page: str) -> List[Dict[str, Any]]:
    mf = get_manifest()
    for p in mf.get("pages", []):
        if p.get("page","").lower() == page.lower():
            return [w for w in p.get("widgets",[]) if w.get("status") in ("active","restricted")]
    return []
