-- SQLite schema for pollinators
CREATE TABLE IF NOT EXISTS taxon (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  rank TEXT,
  source TEXT,
  source_id TEXT
);
CREATE TABLE IF NOT EXISTS media (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  taxon_id INTEGER NOT NULL,
  url TEXT NOT NULL,
  license TEXT,
  attribution TEXT,
  source TEXT,
  source_id TEXT,
  width INTEGER,
  height INTEGER,
  FOREIGN KEY (taxon_id) REFERENCES taxon(id)
);
CREATE TABLE IF NOT EXISTS interaction (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  plant_taxon_id INTEGER NOT NULL,
  pollinator_taxon_id INTEGER NOT NULL,
  predicate TEXT,
  source TEXT,
  evidence TEXT,
  confidence REAL,
  FOREIGN KEY (plant_taxon_id) REFERENCES taxon(id),
  FOREIGN KEY (pollinator_taxon_id) REFERENCES taxon(id)
);
CREATE TABLE IF NOT EXISTS occurrence (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  plant_taxon_id INTEGER,
  pollinator_taxon_id INTEGER,
  date TEXT,
  lat REAL,
  lon REAL,
  source TEXT,
  source_id TEXT,
  FOREIGN KEY (plant_taxon_id) REFERENCES taxon(id),
  FOREIGN KEY (pollinator_taxon_id) REFERENCES taxon(id)
);
