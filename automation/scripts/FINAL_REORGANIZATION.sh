#!/bin/bash

echo "=========================================="
echo "REORGANIZING REPOSITORY STRUCTURE"
echo "=========================================="
echo ""

# Create proper folder structure
echo "1. Creating organized folder structure..."

# Root level organization
mkdir -p .project-root/{configuration,data,source,database,automation,documentation}

# Configuration
mkdir -p .project-root/configuration/{campus,scenarios,reference}

# Data
mkdir -p .project-root/data/{production,generated,archive}

# Source Code
mkdir -p .project-root/source/{digital-twin,legacy-code,utilities}

# Database
mkdir -p .project-root/database/{migrations,schema}

# Automation
mkdir -p .project-root/automation/{tests,scripts,ci-cd}

# Documentation
mkdir -p .project-root/documentation/{guides,audits,architecture}

echo "[OK] Folders created"
echo ""

# Current files in root that need organization
echo "2. Current root-level files:"
ls -1 *.py *.md *.txt 2>/dev/null | head -20

echo ""
echo "Structure ready. Files can be moved to:"
echo "  configuration/ → Campus configs & scenarios"
echo "  data/          → All CSV & data files"
echo "  source/        → digital_twin & source code"
echo "  database/      → Migrations & schema"
echo "  automation/    → Tests & scripts"
echo "  documentation/ → All docs & guides"
echo ""

