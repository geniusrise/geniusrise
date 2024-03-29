#!/bin/bash

# Directories to be created
declare -a dirs=(
  "geniusrise"
  "geniusrise/data_sources"
  "geniusrise/data_sources/project_management"
  "geniusrise/data_sources/code_hosting"
  "geniusrise/data_sources/communication"
  "geniusrise/data_sources/document_management"
  "geniusrise/data_sources/customer_support"
  "geniusrise/llm"
  "geniusrise/crm"
  "tests"
)

# Create directories
for dir in "${dirs[@]}"; do
  mkdir -p $dir
  touch $dir/__init__.py
done

# Files to be created in each subcategory
declare -a pm=("jira" "asana" "monday" "trello" "basecamp" "clickup")
declare -a ch=("github" "gitlab" "bitbucket")
declare -a comm=("slack" "microsoft_teams" "discord")
declare -a dm=("google_drive" "dropbox" "notion" "confluence")
declare -a cs=("zendesk" "freshdesk" "intercom")
declare -a crm=("salesforce" "hubspot" "zoho")
declare -a llm=("chatgpt" "other_llm")

# Create files in each subcategory
for file in "${pm[@]}"; do
  touch geniusrise/data_sources/project_management/$file.py
done

for file in "${ch[@]}"; do
  touch geniusrise/data_sources/code_hosting/$file.py
done

for file in "${comm[@]}"; do
  touch geniusrise/data_sources/communication/$file.py
done

for file in "${dm[@]}"; do
  touch geniusrise/data_sources/document_management/$file.py
done

for file in "${cs[@]}"; do
  touch geniusrise/data_sources/customer_support/$file.py
done

for file in "${crm[@]}"; do
  touch geniusrise/crm/$file.py
done

for file in "${llm[@]}"; do
  touch geniusrise/llm/$file.py
done

# Create other files
touch geniusrise/main.py
touch tests/test_data_sources.py
touch setup.py
touch README.md
touch .gitignore
