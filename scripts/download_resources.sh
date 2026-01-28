#!/bin/bash
set -e

DATA_DIR="data"
mkdir -p "$DATA_DIR"

echo "Starting resource download..."

# 1. Download Postgres DB dumps from Google Drive
DB_ZIP="$DATA_DIR/postgres_dumps.zip"
DB_ID="1V9SFIWebi27JtaDUAScG1xE9ELbYcWLR"
EXTRACTED_DIR="$DATA_DIR/bird-interact-full-dumps"

if [ -d "$EXTRACTED_DIR" ]; then
    echo "Database directory $EXTRACTED_DIR already exists. Skipping download and extraction."
else
    if [ -f "$DB_ZIP" ]; then
        echo "Zip file $DB_ZIP already exists. Skipping download."
    else
        echo "Downloading Postgres DB dumps..."
        # Using uv to run gdown without installing it globally
        uv run --with gdown gdown --id "$DB_ID" -O "$DB_ZIP"
    fi

    echo "Extracting zip file..."
    unzip -q "$DB_ZIP" -d "$DATA_DIR"
    echo "Extraction complete."
fi

# 2. Clone HuggingFace repository
REPO_URL="https://huggingface.co/datasets/birdsql/livesqlbench-base-full-v1"
REPO_DIR="$DATA_DIR/livesqlbench-base-full-v1"

if [ -d "$REPO_DIR" ]; then
    echo "Repository $REPO_DIR already exists. Pulling latest changes..."
    cd "$REPO_DIR" && git pull && cd - > /dev/null
else
    echo "Cloning HuggingFace repository..."
    git clone "$REPO_URL" "$REPO_DIR"
fi

echo "All resources downloaded successfully."
