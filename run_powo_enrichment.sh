#!/bin/bash
exec python -u batch_powo_enrichment.py --full 2>&1 | tee logs/powo_workflow.log
