#!/bin/bash
# AI Knowledge Hub - Deploy Script
set -e

SERVER="root@192.168.31.150"
REMOTE_DIR="/opt/ai-knowledge-hub"
KEY_FILE="$HOME/.ssh/ai-knowledge-studio-key"

echo "=== Creating remote directory ==="
ssh -i "$KEY_FILE" "$SERVER" "mkdir -p $REMOTE_DIR"

echo "=== Copying project files ==="
rsync -avz --exclude 'node_modules' --exclude '__pycache__' --exclude '.git' --exclude '*.pyc' \
  -e "ssh -i $KEY_FILE" \
  ./ "$SERVER:$REMOTE_DIR/"

echo "=== Building and starting services ==="
ssh -i "$KEY_FILE" "$SERVER" "cd $REMOTE_DIR && docker compose up -d --build"

echo "=== Checking status ==="
sleep 3
ssh -i "$KEY_FILE" "$SERVER" "cd $REMOTE_DIR && docker compose ps"

echo "=== Deployment complete ==="
echo "Access: http://192.168.31.150"
