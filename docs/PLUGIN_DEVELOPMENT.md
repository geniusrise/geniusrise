# Geniusrise Plugin Development Guide

This document provides guidelines for developing plugins for the Geniusrise
framework.

## Core Concepts

Geniusrise allows extension through a plugin architecture. The following
components can be extended:

1. **Runners** - Infrastructure providers for running Bolts and Spouts
2. **State Managers** - Systems for managing state across executions
3. **Data Handlers** - Input and output mechanisms

## Creating a Runner Plugin

Runners are the most common type of plugin. They let Geniusrise run on different
infrastructure.

### Basic Structure

A runner plugin should be a separate Python package with the following
structure:

```
geniusrise-runner-[provider]/
├── geniusrise_runner_[provider]/
│   ├── __init__.py
│   ├── instance.py
│   ├── autoscale.py (optional)
│   └── templates/ (optional)
├── setup.py
├── requirements.txt
└── README.md
```

### Implementation

1. Create a main runner class that implements the required interface:

```python
from geniusrise.core.task import Task

class MyProviderRunner:
    def __init__(self):
        # Initialize your runner
        pass

    def create_parser(self, parser):
        # Add your CLI arguments
        pass

    def run(self, args):
        # Implementation
        pass

    def execute(self, task: Task, method_name: str, *args, **kwargs):
        # Execute a task on your infrastructure
        pass
```

2. In your `__init__.py`, register the runner with Geniusrise:

```python
from geniusrise.core import register_runner
from .instance import MyProviderRunner

# Register the runner
register_runner('myprovider', MyProviderRunner)

# Export the class directly for Python imports
__all__ = ['MyProviderRunner']
```

### Installation

Users would install your plugin with:

```bash
pip install geniusrise-runner-myprovider
```

Once installed, the runner becomes available automatically.

## Creating a State Manager Plugin

State managers handle how state is persisted between executions.

```python
from geniusrise.core.state import State

class MyCustomState(State):
    def __init__(self, task_id, **kwargs):
        super().__init__(task_id)
        # Initialize your state manager

    def get_state(self, key=None):
        # Implementation
        pass

    def set_state(self, key, value):
        # Implementation
        pass
```

## Creating a Data Handler Plugin

Data handlers manage input and output of data.

```python
from geniusrise.core.data import Input, Output

class MyCustomInput(Input):
    def __init__(self, **kwargs):
        # Initialize your input handler
        pass

    def read(self, **kwargs):
        # Implementation
        pass

class MyCustomOutput(Output):
    def __init__(self, **kwargs):
        # Initialize your output handler
        pass

    def write(self, data, **kwargs):
        # Implementation
        pass
```

## Best Practices

1. Keep dependencies minimal and specific to your plugin
2. Follow the same code style as the main Geniusrise codebase
3. Include comprehensive documentation and examples
4. Write tests for your plugin
5. Use semantic versioning
6. Handle errors gracefully

## Publishing Your Plugin

1. Create a repository on GitHub or another platform
2. Publish your package to PyPI:
   ```bash
   pip install build twine
   python -m build
   twine upload dist/*
   ```
3. Add your plugin to the Geniusrise plugin directory by submitting a PR to the
   main repository

## Example Plugins

- [geniusrise-runner-kubernetes](https://github.com/geniusrise/geniusrise-runner-kubernetes)
- [geniusrise-runner-docker](https://github.com/geniusrise/geniusrise-runner-docker)
- [geniusrise-runner-openstack](https://github.com/geniusrise/geniusrise-runner-openstack)
