#!/bin/bash
set -e
GITHUB_TOKEN="YOUR_GITHUB_PERSONAL_ACCESS_TOKEN"
GITHUB_USER="YOUR_GITHUB_USERNAME"
REPO_NAME="mobility-booking-api"
if [ "$GITHUB_TOKEN" = "YOUR_GITHUB_PERSONAL_ACCESS_TOKEN" ]; then
  echo "ERROR: Set GITHUB_TOKEN and GITHUB_USER before running."; exit 1
fi
curl -s -X POST -H "Authorization: token $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" https://api.github.com/user/repos \
  -d "{\"name\":\"$REPO_NAME\",\"description\":\"Mobility car rental booking REST API – Flask, Python, Claude AI assistant, mobile check-in, pytest, CI\",\"private\":false}"
cd "$(dirname "$0")"
git init && git add .
git commit -m "Initial commit: Mobility Booking API"
git remote add origin "https://$GITHUB_TOKEN@github.com/$GITHUB_USER/$REPO_NAME.git"
git branch -M main && git push -u origin main
echo "Done! https://github.com/$GITHUB_USER/$REPO_NAME"
