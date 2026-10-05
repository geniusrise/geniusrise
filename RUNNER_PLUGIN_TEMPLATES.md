# Geniusrise Runner Plugin Templates

This document provides templates for creating the extracted runner plugins.

## 1. OpenStack Runner Plugin

### Directory Structure

```
geniusrise-runner-openstack/
├── geniusrise_runner_openstack/
│   ├── __init__.py
│   ├── instance.py
│   ├── autoscale.py
│   └── templates/
│       ├── network.template
│       └── security_group.template
├── tests/
│   ├── __init__.py
│   ├── test_instance.py
│   └── test_autoscale.py
├── setup.py
├── requirements.txt
├── README.md
└── LICENSE
```

### setup.py

```python
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="geniusrise-runner-openstack",
    version="0.1.0",
    author="Geniusrise",
    author_email="ixaxaar@geniusrise.ai",
    description="OpenStack runner for Geniusrise",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/geniusrise/geniusrise-runner-openstack",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.10",
    install_requires=[
        "geniusrise>=0.2.0",
        "openstacksdk>=3.0.0",
    ],
    package_data={
        "geniusrise_runner_openstack": ["templates/*.template"],
    },
)
```

### **init**.py

```python
from geniusrise.core import register_runner
from .instance import OpenStackInstanceRunner
from .autoscale import OpenStackAutoScaler

# Register with Geniusrise
register_runner('openstack', OpenStackInstanceRunner)
register_runner('openstack_autoscale', OpenStackAutoScaler)

__all__ = ["OpenStackInstanceRunner", "OpenStackAutoScaler"]
```

## 2. AceCloud Runner Plugin

### Directory Structure

```
geniusrise-runner-acecloud/
├── geniusrise_runner_acecloud/
│   ├── __init__.py
│   ├── instance.py
│   └── autoscale.py
├── tests/
│   ├── __init__.py
│   ├── test_instance.py
│   └── test_autoscale.py
├── setup.py
├── requirements.txt
├── README.md
└── LICENSE
```

### setup.py

```python
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="geniusrise-runner-acecloud",
    version="0.1.0",
    author="Geniusrise",
    author_email="ixaxaar@geniusrise.ai",
    description="AceCloud runner for Geniusrise",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/geniusrise/geniusrise-runner-acecloud",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.10",
    install_requires=[
        "geniusrise>=0.2.0",
        "geniusrise-runner-openstack>=0.1.0",
    ],
)
```

### **init**.py

```python
from geniusrise.core import register_runner
from .instance import AceCloudInstanceRunner
from .autoscale import AceCloudAutoScaler

# Register with Geniusrise
register_runner('acecloud', AceCloudInstanceRunner)
register_runner('acecloud_autoscale', AceCloudAutoScaler)

__all__ = ["AceCloudInstanceRunner", "AceCloudAutoScaler"]
```

## 3. E2E Networks Runner Plugin

### Directory Structure

```
geniusrise-runner-e2e/
├── geniusrise_runner_e2e/
│   ├── __init__.py
│   ├── instance.py
│   └── autoscale.py
├── tests/
│   ├── __init__.py
│   ├── test_instance.py
│   └── test_autoscale.py
├── setup.py
├── requirements.txt
├── README.md
└── LICENSE
```

### setup.py

```python
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="geniusrise-runner-e2e",
    version="0.1.0",
    author="Geniusrise",
    author_email="ixaxaar@geniusrise.ai",
    description="E2E Networks runner for Geniusrise",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/geniusrise/geniusrise-runner-e2e",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.10",
    install_requires=[
        "geniusrise>=0.2.0",
        "requests>=2.31.0",
    ],
)
```

### **init**.py

```python
from geniusrise.core import register_runner
from .instance import E2EInstanceRunner
from .autoscale import E2EAutoScaler

# Register with Geniusrise
register_runner('e2e', E2EInstanceRunner)
register_runner('e2e_autoscale', E2EAutoScaler)

__all__ = ["E2EInstanceRunner", "E2EAutoScaler"]
```

## Migration Plan

1. Create these repositories in the geniusrise organization
2. Copy the existing code into the respective repositories
3. Publish the plugins to PyPI
4. Update the main geniusrise package to support the plugin system
5. Mark the embedded runners as deprecated in the main package
6. Remove the embedded runners in a future release

## Documentation Updates

1. Update the main documentation to mention the plugin system
2. Create documentation for each plugin
3. Update examples to demonstrate the use of plugins
4. Create a migration guide for users of the embedded runners
