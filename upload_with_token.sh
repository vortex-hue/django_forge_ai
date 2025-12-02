#!/bin/bash
# Upload script that uses API tokens directly to avoid trusted publishing issues

set -e

MODE=${1:-test}  # Default to test

echo "📦 DjangoForgeAI Upload Script (Using API Token)"
echo "================================================"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

if [ "$MODE" = "test" ]; then
    echo -e "${YELLOW}Uploading to Test PyPI...${NC}"
    echo -e "${YELLOW}Username: __token__${NC}"
    echo -e "${YELLOW}Password: Enter your Test PyPI API token${NC}"
    echo ""
    
    # Use environment variables if set, otherwise prompt
    if [ -z "$TWINE_PASSWORD" ]; then
        read -sp "Enter Test PyPI API token: " TOKEN
        echo ""
        export TWINE_USERNAME="__token__"
        export TWINE_PASSWORD="$TOKEN"
    fi
    
    python -m twine upload \
        --repository testpypi \
        --username "$TWINE_USERNAME" \
        --password "$TWINE_PASSWORD" \
        --skip-existing \
        --disable-progress-bar \
        dist/*
    
    echo -e "${GREEN}✓ Uploaded to Test PyPI!${NC}"
    
elif [ "$MODE" = "prod" ]; then
    echo -e "${YELLOW}Uploading to Production PyPI...${NC}"
    read -p "Are you sure? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}Cancelled.${NC}"
        exit 0
    fi
    
    echo -e "${YELLOW}Username: __token__${NC}"
    echo -e "${YELLOW}Password: Enter your Production PyPI API token${NC}"
    echo ""
    
    # Use environment variables if set, otherwise prompt
    if [ -z "$TWINE_PASSWORD" ]; then
        read -sp "Enter Production PyPI API token: " TOKEN
        echo ""
        export TWINE_USERNAME="__token__"
        export TWINE_PASSWORD="$TOKEN"
    fi
    
    python -m twine upload \
        --username "$TWINE_USERNAME" \
        --password "$TWINE_PASSWORD" \
        --skip-existing \
        --disable-progress-bar \
        dist/*
    
    echo -e "${GREEN}✓ Uploaded to Production PyPI!${NC}"
    echo -e "${GREEN}Package: https://pypi.org/project/django-forge-ai/${NC}"
else
    echo -e "${RED}Invalid mode. Use 'test' or 'prod'${NC}"
    exit 1
fi

