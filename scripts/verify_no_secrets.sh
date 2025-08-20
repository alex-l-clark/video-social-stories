#!/usr/bin/env bash
set -euo pipefail

echo "🔍 Scanning for leaked secrets..."

# Check current tracked files for certificate/key patterns (skip scripts and docs)
echo "Checking tracked files..."
if git grep -qE "(BEGIN (RSA )?PRIVATE KEY|BEGIN CERTIFICATE)" -- ':!scripts/' ':!*.md' ':!SECURITY.md' 2>/dev/null; then
    echo "❌ Found certificate patterns in tracked files:"
    git grep -nE "(BEGIN (RSA )?PRIVATE KEY|BEGIN CERTIFICATE)" -- ':!scripts/' ':!*.md' ':!SECURITY.md' 2>/dev/null || true
    SECRET_COUNT=1
else
    echo "✅ No certificate patterns found in tracked files"
    SECRET_COUNT=0
fi

# Check that specific leaked files are not in history
echo "Checking for removed certificate files in history..."
if git log --all --full-history --oneline -- \
  "render_worker/tmp_smoke/depot-cert1453891451" \
  "render_worker/tmp_smoke/depot-key40424928" \
  "render_worker/tmp_smoke/depot-ca-cert391968814" 2>/dev/null | grep -q .; then
    echo "❌ Found references to removed cert files in history"
    HISTORY_COUNT=1
else
    echo "✅ No references to removed cert files in history"
    HISTORY_COUNT=0
fi

# Quick check for certificate content in recent commits (last 10)
echo "Checking recent commits for certificate patterns..."
if git log -10 --all -p | grep -qE "(BEGIN (RSA )?PRIVATE KEY|BEGIN CERTIFICATE)" 2>/dev/null; then
    echo "❌ Found certificate patterns in recent commits"
    CERT_HISTORY_COUNT=1
else
    echo "✅ No certificate patterns in recent commits"
    CERT_HISTORY_COUNT=0
fi

# Final assessment
TOTAL_ISSUES=$((SECRET_COUNT + HISTORY_COUNT + CERT_HISTORY_COUNT))

if [ "$TOTAL_ISSUES" -eq 0 ]; then
    echo "✅ No secrets detected in current files or git history"
    exit 0
else
    echo "❌ Found $TOTAL_ISSUES potential security issues:"
    echo "  - Tracked files: $SECRET_COUNT"
    echo "  - Removed cert files in history: $HISTORY_COUNT" 
    echo "  - Certificate patterns in history: $CERT_HISTORY_COUNT"
    echo ""
    echo "Action required: Review and clean up remaining issues"
    exit 1
fi
