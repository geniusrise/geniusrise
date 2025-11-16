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
    version="0.2.0",
    packages=find_packages(exclude=["tests", "tests.*"]),
    install_requires=requirements,
    entry_points=entry_points,
    python_requires=">=3.10",
    author="Geniusrise",
    author_email="ixaxaar@geniusrise.ai",
    description="Unified local AI inference framework for vision, text, and audio models",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/geniusrise/geniusrise",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    keywords="ai, inference, llm, vision, audio, pytorch, transformers, local inference",
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
        "all": [],  # All modalities included by default now
    },
)
