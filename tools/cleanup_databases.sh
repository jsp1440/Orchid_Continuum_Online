#!/bin/bash

# Database Cleanup Script
# Removes duplicate/test database files and updates .gitignore

set -e

echo "=================================================="
echo "  Database Cleanup Script"
echo "=================================================="
echo ""

# Counter for deleted files
deleted_count=0

# List of files to delete
files_to_delete=(
    "tmp/test_orchid.db"
    "cache/orchid_copy.db"
    "old/orchid (1).sqlite"
    "old/orchid (2).sqlite"
    "sandbox/dev_cache.db"
    "archive/test_backup.sqlite"
)

echo "Step 1: Removing duplicate/test database files..."
echo "--------------------------------------------------"

for file in "${files_to_delete[@]}"; do
    if [ -f "$file" ]; then
        rm "$file"
        echo "  ✓ Deleted: $file"
        ((deleted_count++))
    else
        echo "  - Not found: $file (skipped)"
    fi
done

if [ $deleted_count -eq 0 ]; then
    echo "  No files to delete (all already removed or never existed)"
fi

echo ""
echo "Step 2: Updating .gitignore..."
echo "--------------------------------------------------"

# Check if .gitignore exists, create if not
if [ ! -f .gitignore ]; then
    touch .gitignore
    echo "  Created .gitignore file"
fi

# Patterns to add
patterns=(
    "*.db"
    "*.sqlite"
    "*.sqlite3"
    "/tmp/*"
    "/cache/*"
)

# Check and add patterns
added_count=0
for pattern in "${patterns[@]}"; do
    # Escape special characters for grep
    escaped_pattern=$(echo "$pattern" | sed 's/[]\/$*.^[]/\\&/g')
    
    if ! grep -q "^${escaped_pattern}$" .gitignore 2>/dev/null; then
        echo "$pattern" >> .gitignore
        echo "  ✓ Added: $pattern"
        ((added_count++))
    else
        echo "  - Already present: $pattern"
    fi
done

if [ $added_count -eq 0 ]; then
    echo "  All patterns already in .gitignore"
fi

echo ""
echo "Step 3: Listing remaining database files..."
echo "--------------------------------------------------"

# Find all database files, excluding node_modules and .git
remaining_files=$(find . -type f \( -name "*.db" -o -name "*.sqlite" -o -name "*.sqlite3" \) \
    -not -path "./node_modules/*" \
    -not -path "./.git/*" \
    -not -path "./.cache/*" \
    -not -path "./.pythonlibs/*" \
    2>/dev/null | sort)

if [ -z "$remaining_files" ]; then
    echo "  No database files found"
else
    echo "$remaining_files" | while read -r file; do
        size=$(du -h "$file" 2>/dev/null | cut -f1)
        echo "  • $file ($size)"
    done
    
    file_count=$(echo "$remaining_files" | wc -l)
    echo ""
    echo "  Total: $file_count database file(s) remaining"
fi

echo ""
echo "=================================================="
echo "  ✓ Cleanup Complete!"
echo "=================================================="
echo ""
echo "Summary:"
echo "  - Deleted files: $deleted_count"
echo "  - .gitignore patterns added: $added_count"
echo ""
echo "Run 'git status' to see changes to .gitignore"
echo "=================================================="
