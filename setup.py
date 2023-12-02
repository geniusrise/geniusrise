from setuptools import find_packages, setup  # type: ignore

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as f:
    requirements = f.read().splitlines()

entry_points = {
    "console_scripts": [
        "geniusrise = geniusrise.cli.geniusctl:main",
        "genius = geniusrise.cli.geniusctl:main",
    ]
}

setup(
    name="geniusrise",
    version="0.0.28",
    packages=find_packages(exclude=["tests", "tests.*"]),
    install_requires=requirements,
    entry_points=entry_points,
    python_requires=">=3.10",
    author="Geniusrise",
    author_email="ixaxaar@geniusrise.ai",
    description="An LLM framework",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/geniusrise/geniusrise",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Build Tools",
        "License :: OSI Approved :: GNU Affero General Public License v3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
    ],
    keywords="mlops, llm, geniusrise, machine learning, data processing",
    project_urls={
        "Bug Reports": "https://github.com/geniusrise/geniusrise/issues",
        "Source": "https://github.com/geniusrise/geniusrise",
        "Documentation": "https://docs.geniusrise.ai/",
    },
    package_data={
        "geniusrise": [],
    },
    extras_require={
        "dev": ["check-manifest"],
        "test": ["coverage"],
    },
)
