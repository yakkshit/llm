#!/bin/bash

NGINX_CONF="nginx.conf"
ENV_FILE=".env.llm"

# Check if nginx.conf exists
if [ ! -f "$NGINX_CONF" ]; then
    echo "❌ Error: $NGINX_CONF not found. Please run this script from ~/fcukoffai-llm"
    exit 1
fi

# Generate a cryptographically secure random string (32 hex characters)
RANDOM_PART=$(openssl rand -hex 32)
NEW_API_KEY="sk-fcukoffai-${RANDOM_PART}"

echo "🔐 Generating new secure API Key..."

# Update the nginx.conf file with the new key
if grep -q "YOUR_SECURE_API_KEY_HERE" "$NGINX_CONF"; then
    sed -i "s/YOUR_SECURE_API_KEY_HERE/${NEW_API_KEY}/g" "$NGINX_CONF"
    echo "✅ Successfully updated $NGINX_CONF with the new API key."
else
    echo "⚠️ Warning: Could not find 'YOUR_SECURE_API_KEY_HERE' in $NGINX_CONF."
    echo "Please ensure you have updated nginx.conf with the placeholder first."
    exit 1
fi

# Save to a local env file for easy reference
echo "CUSTOM_LLM_API_KEY=${NEW_API_KEY}" > "$ENV_FILE"
echo "💾 Key saved to $ENV_FILE for your reference."

echo ""
echo "=========================================="
echo "🔑 YOUR NEW SECURE API KEY:"
echo "$NEW_API_KEY"
echo "=========================================="
echo ""
echo "🚀 Next Steps:"
echo "1. Restart Nginx to apply the new key:"
echo "   docker compose restart nginx"
echo "2. Update your cv-main project (.env.local):"
echo "   CUSTOM_LLM_API_KEY=\"$NEW_API_KEY\""
echo ""
