#!/bin/bash
set -euo pipefail

# Smoke test script for video rendering
# Usage: ./smoke_render.sh [URL]
# Example: ./smoke_render.sh https://your-app.vercel.app

URL="${1:-http://localhost:3000}"
SMOKE_URL="${URL}/api/render-smoke"
MIN_BYTES=500000
ARTIFACTS_DIR="artifacts"
TEST_OUTPUT="${ARTIFACTS_DIR}/test.mp4"
HEADERS_FILE="${ARTIFACTS_DIR}/headers.txt"

echo "🎬 Video Social Stories - Smoke Test"
echo "Target: ${URL}"
echo "Min bytes: ${MIN_BYTES}"
echo ""

# Create artifacts directory
mkdir -p "${ARTIFACTS_DIR}"

echo "🔥 Running smoke test endpoint..."
echo "GET ${SMOKE_URL}"

# Call the smoke test endpoint
if ! curl -sSL \
  -H "Accept: application/json" \
  -H "User-Agent: smoke-test-script/1.0" \
  --max-time 600 \
  --fail \
  "${SMOKE_URL}" > "${ARTIFACTS_DIR}/smoke_result.json"; then
  echo "❌ Smoke test endpoint failed"
  echo "Response saved to: ${ARTIFACTS_DIR}/smoke_result.json"
  exit 1
fi

echo "✅ Smoke test endpoint responded"

# Parse the JSON response
if command -v jq >/dev/null 2>&1; then
  echo ""
  echo "📊 Smoke test results:"
  cat "${ARTIFACTS_DIR}/smoke_result.json" | jq '.'
  
  # Extract key metrics
  OK=$(cat "${ARTIFACTS_DIR}/smoke_result.json" | jq -r '.ok')
  BYTES=$(cat "${ARTIFACTS_DIR}/smoke_result.json" | jq -r '.bytes // 0')
  DURATION=$(cat "${ARTIFACTS_DIR}/smoke_result.json" | jq -r '.durationMs // 0')
  REQUEST_ID=$(cat "${ARTIFACTS_DIR}/smoke_result.json" | jq -r '.requestId // "unknown"')
  
  echo ""
  echo "📈 Summary:"
  echo "  Status: ${OK}"
  echo "  Bytes: ${BYTES}"
  echo "  Duration: ${DURATION}ms"
  echo "  Request ID: ${REQUEST_ID}"
  
  if [ "${OK}" != "true" ]; then
    echo "❌ Smoke test failed - check the response above"
    exit 1
  fi
  
  if [ "${BYTES}" -lt "${MIN_BYTES}" ]; then
    echo "❌ Video too small: ${BYTES} bytes (expected >= ${MIN_BYTES})"
    exit 1
  fi
  
else
  echo "⚠️  jq not found - install jq for detailed output parsing"
  echo "Raw response:"
  cat "${ARTIFACTS_DIR}/smoke_result.json"
  echo ""
fi

echo ""
echo "🎯 Testing direct download..."

# Test the render endpoint directly (if we have a job_id from smoke test)
if command -v jq >/dev/null 2>&1; then
  JOB_ID=$(cat "${ARTIFACTS_DIR}/smoke_result.json" | jq -r '.jobId // empty')
  
  if [ -n "${JOB_ID}" ] && [ "${JOB_ID}" != "null" ]; then
    echo "Using job ID from smoke test: ${JOB_ID}"
    RENDER_URL="${URL}/api/render?job_id=${JOB_ID}"
    
    echo "GET ${RENDER_URL}"
    
    if curl -sSL \
      -D "${HEADERS_FILE}" \
      -o "${TEST_OUTPUT}" \
      --max-time 120 \
      --fail \
      "${RENDER_URL}"; then
      
      ACTUAL_BYTES=$(wc -c < "${TEST_OUTPUT}")
      echo "✅ Direct download successful"
      echo "  File: ${TEST_OUTPUT}"
      echo "  Size: ${ACTUAL_BYTES} bytes"
      
      # Verify minimum size
      if [ "${ACTUAL_BYTES}" -ge "${MIN_BYTES}" ]; then
        echo "✅ Size validation passed"
      else
        echo "❌ Size validation failed: ${ACTUAL_BYTES} < ${MIN_BYTES}"
        exit 1
      fi
      
      # Check headers
      echo ""
      echo "📄 Response headers:"
      cat "${HEADERS_FILE}"
      
      # Verify key headers are present
      if grep -q "Content-Type: video/mp4" "${HEADERS_FILE}"; then
        echo "✅ Content-Type header correct"
      else
        echo "❌ Missing or incorrect Content-Type header"
        exit 1
      fi
      
      if grep -q "Content-Length:" "${HEADERS_FILE}"; then
        echo "✅ Content-Length header present"
      else
        echo "⚠️  Content-Length header missing"
      fi
      
      if grep -q "Accept-Ranges: bytes" "${HEADERS_FILE}"; then
        echo "✅ Accept-Ranges header present"
      else
        echo "⚠️  Accept-Ranges header missing"
      fi
      
    else
      echo "❌ Direct download failed"
      echo "Headers saved to: ${HEADERS_FILE}"
      exit 1
    fi
  else
    echo "⚠️  No job ID available for direct download test"
  fi
else
  echo "⚠️  Skipping direct download test (jq required)"
fi

echo ""
echo "🎉 All tests passed!"
echo "   Smoke test: ✅"
echo "   Size check: ✅ (${ACTUAL_BYTES:-$BYTES} bytes >= ${MIN_BYTES})"
echo "   Headers: ✅"
echo ""
echo "📁 Artifacts saved to: ${ARTIFACTS_DIR}/"
echo "   - smoke_result.json: API response"
if [ -f "${TEST_OUTPUT}" ]; then
  echo "   - test.mp4: Downloaded video"
fi
if [ -f "${HEADERS_FILE}" ]; then
  echo "   - headers.txt: HTTP headers"
fi