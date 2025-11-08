import json, os
from app.manifest import get_manifest, is_widget_active, active_widgets_for

def test_manifest_loads():
    data = get_manifest()
    assert "pages" in data
    assert "widgets_flat" in data

def test_helpers_ok():
    # should not raise
    _ = is_widget_active("Orchid of the Day")
    _ = active_widgets_for("Home")
