# BloomBuilder Upgrade / Integration Bundle

This bundle packages the **revised BloomBuilder widget** plus the new **Pollinators** module and a minimal **Trait Databank**.
Drop it into your Flask project on Replit and register the blueprints to get a complete, working experience.

## What’s inside
- `bloombuilder/` – Blueprint with `/widget` route, updated UI & text, notes box, workflow section
- `pollinators/` – Blueprint with `/api/pollinators` and a Jinja ribbon partial
- `traits/` – Lightweight API `/api/traits/<plant_taxon_id>` for adaptation cards (sample data)
- `migrations/schema.sql` – SQLite schema for `taxon`, `media`, `interaction`, `occurrence`
- `sample_data/` – Seed JSON for traits and a demo plant↔pollinators mapping
- `README.md` – This file with step-by-step setup

## Quick Start (Replit)
1) Upload this ZIP and extract it into your project root. You should see `bloombuilder/`, `pollinators/`, `traits/` folders.
2) Install dependencies (if not already present):
   ```bash
   pip install flask
   ```
3) Initialize a local SQLite DB (`bb.db`) and load the sample data:
   ```bash
   python pollinators/seed_pollinators.py
   ```
4) Register the blueprints in your Flask app after you create `app`:
   ```python
   from bloombuilder import bb_bp
   from pollinators import pollinators_bp
   from traits import traits_bp

   app.register_blueprint(bb_bp)  # serves /widget
   app.register_blueprint(pollinators_bp, url_prefix="/api")
   app.register_blueprint(traits_bp, url_prefix="/api")
   ```
5) Launch Replit and visit `/widget`

## Notes system
- The widget exposes a Notes textarea and fires a `bb:pollinator-note` event when you click “Insert pollinator credit” in the ribbon.
- In your page JS, you can listen for the event to append text to your canonical notes field:
  ```js
  window.addEventListener('bb:pollinator-note', e => {
    const ta = document.getElementById('bb-notes');
    if (ta) ta.value = (ta.value ? ta.value + "\n" : "") + e.detail.text;
  });
  ```

## Theming
- Update `bloombuilder/static/css/widget.css` to match FCOS purple/green.
- No CSS frameworks required.

## Next steps
- Replace the sample trait/pollinator JSON with live ETL from GBIF/EOL.
- Expand species list, keys, glossary links, and final artistic rendering step.
