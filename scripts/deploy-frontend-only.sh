#!/bin/bash

# Deploy only frontend by using a special commit message

echo "Deploying frontend only..."

# Add all changes
git add -A

# Commit with [frontend-only] tag
git commit -m "$1 [frontend-only]"

# Push to master
git push origin master

echo "Frontend deployment triggered. Backend deployment will be skipped if configured."
echo "Configure your LangSmith deployment to skip commits with [frontend-only] tag"