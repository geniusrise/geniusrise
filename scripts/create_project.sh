#!/bin/bash

# Prompt for project details
read -p "Enter your project name: " project_name
read -p "Enter your name: " author_name
read -p "Enter your email: " author_email
read -p "Enter your GitHub username: " github_username
read -p "Enter a brief description of your project: " project_description

# Create project structure
mkdir $project_name
cd $project_name
mkdir $project_name tests

# Create basic files
touch README.md
touch requirements.txt
touch setup.py
touch $project_name/__init__.py
touch tests/__init__.py

# Populate README.md
echo "# $project_name" > README.md
echo "\n$project_description" >> README.md

# Populate setup.py
cat <<EOL > setup.py
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name='$project_name',
    version='0.1.0',
    packages=find_packages(exclude=["tests", "tests.*"]),
    install_requires=[],
    python_requires='>=3.10',
    author='$author_name',
    author_email='$author_email',
    description='$project_description',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/$github_username/$project_name',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
)
EOL

# Fetch .pre-commit-config.yaml and .gitignore from geniusrise/geniusrise
curl -O https://raw.githubusercontent.com/geniusrise/geniusrise/master/.pre-commit-config.yaml
curl -O https://raw.githubusercontent.com/geniusrise/geniusrise/master/.gitignore

echo "Project $project_name initialized!"
