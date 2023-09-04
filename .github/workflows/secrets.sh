#!/bin/bash

# Set secrets for the GitHub repository
gh secret set AWS_ACCESS_KEY_ID --body="$AWS_ACCESS_KEY_ID" --repo=geniusrise/geniusrise
gh secret set AWS_SECRET_ACCESS_KEY --body="$AWS_SECRET_ACCESS_KEY" --repo=geniusrise/geniusrise
gh secret set OPENAI_ORGANIZATION --body="$OPENAI_ORGANIZATION" --repo=geniusrise/geniusrise
gh secret set OPENAI_API_KEY --body="$OPENAI_API_KEY" --repo=geniusrise/geniusrise
gh secret set OPENAI_API_VERSION --body="$OPENAI_API_VERSION" --repo=geniusrise/geniusrise
gh secret set HUGGINGFACE_ACCESS_TOKEN --body="$HUGGINGFACE_ACCESS_TOKEN" --repo=geniusrise/geniusrise
gh secret set PALM_KEY --body="$PALM_KEY" --repo=geniusrise/geniusrise
