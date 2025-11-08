#!/bin/bash
exec python -u batch_gbif_eol_enrichment.py --full --no-ai-vision --gbif-only 2>&1 | tee logs/gbif_workflow.log
