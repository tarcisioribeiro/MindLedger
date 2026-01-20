#!/bin/bash
# Script to fix media directory permissions for Docker
# Run this script if you encounter 500 errors when uploading files

echo "Fixing media directory permissions..."

# Get the current user's UID and GID
CURRENT_UID=$(id -u)
CURRENT_GID=$(id -g)

# Create necessary directory structure
mkdir -p ./api/media/security/archives/$(date +%Y)/$(date +%m)
mkdir -p ./api/media/loans

# Fix ownership (requires sudo)
echo "Running: sudo chown -R ${CURRENT_UID}:${CURRENT_GID} ./api/media"
sudo chown -R ${CURRENT_UID}:${CURRENT_GID} ./api/media

# Fix permissions
chmod -R 755 ./api/media

echo "Done! Media directory permissions fixed."
echo "You may need to restart the API container: docker-compose restart api"
