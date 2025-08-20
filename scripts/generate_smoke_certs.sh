#!/usr/bin/env bash
set -euo pipefail

echo "Generating ephemeral test certificates..."

# Create directory if it doesn't exist
mkdir -p render_worker/tmp_smoke

# Generate a temporary CA
openssl req -x509 -nodes -newkey rsa:2048 -days 7 \
  -subj "/CN=SmokeTestCA" \
  -keyout render_worker/tmp_smoke/depot-ca.key \
  -out    render_worker/tmp_smoke/depot-ca-cert.crt

# Generate a server key and CSR
openssl req -new -nodes -newkey rsa:2048 -subj "/CN=localhost" \
  -keyout render_worker/tmp_smoke/depot-key.key \
  -out    render_worker/tmp_smoke/depot.csr

# Sign the server cert with the temporary CA
openssl x509 -req -days 7 \
  -in render_worker/tmp_smoke/depot.csr \
  -CA render_worker/tmp_smoke/depot-ca-cert.crt \
  -CAkey render_worker/tmp_smoke/depot-ca.key -CAcreateserial \
  -out render_worker/tmp_smoke/depot-cert.crt

# Clean up CSR
rm -f render_worker/tmp_smoke/depot.csr

echo "✅ Generated test certificates (valid for 7 days):"
echo "SMOKE_CERT=render_worker/tmp_smoke/depot-cert.crt"
echo "SMOKE_KEY=render_worker/tmp_smoke/depot-key.key"
echo "SMOKE_CA=render_worker/tmp_smoke/depot-ca-cert.crt"
echo ""
echo "⚠️  These are test certificates only. Do not commit to git!"
