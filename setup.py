from setuptools import find_packages, setup  # type: ignore

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements-core.txt", "r", encoding="utf-8") as f:
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
    packages=find_packages(exclude=["tests", "tests.*", "build", "dist", "venv"]),
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
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
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
        "dev": ["check-manifest", "black", "flake8", "mypy"],
        "test": ["coverage", "pytest", "pytest-asyncio"],
        "docs": ["sphinx", "sphinx-rtd-theme"],
        # Runner plugins are now separate packages
        "k8s": ["geniusrise-runner-k8s>=0.1.0"],
        "docker": ["geniusrise-runner-docker>=0.1.0"],
        "openstack": ["geniusrise-runner-openstack>=0.1.0"],
        "airflow": ["geniusrise-runner-airflow>=0.1.0"],
        # State backend plugins
        "redis": ["geniusrise-state-redis>=0.1.0"],
        "postgres": ["geniusrise-state-postgres>=0.1.0"],
        "dynamo": ["geniusrise-state-dynamo>=0.1.0"],
        # Data backend plugins
        "s3": ["geniusrise-data-s3>=0.1.0"],
        "kafka": ["geniusrise-data-kafka>=0.1.0"],
        # Full installation with all plugins
        "full": [
            "geniusrise-runner-k8s>=0.1.0",
            "geniusrise-runner-docker>=0.1.0",
            "geniusrise-runner-openstack>=0.1.0",
            "geniusrise-runner-airflow>=0.1.0",
            "geniusrise-state-redis>=0.1.0",
            "geniusrise-state-postgres>=0.1.0",
            "geniusrise-state-dynamo>=0.1.0",
            "geniusrise-data-s3>=0.1.0",
            "geniusrise-data-kafka>=0.1.0",
        ],
    },
)
