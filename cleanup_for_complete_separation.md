# Directory Structure Cleanup Plan for Complete Separation

## Files to Remove from Core Package

These files should be removed from the core package as they are now part of
separate packages:

### State Backends to Remove

- `/run/media/ixaxaar/src/code/src/ORGS/geniusrise/geniusrise/geniusrise/core/state/redis.py`
- `/run/media/ixaxaar/src/code/src/ORGS/geniusrise/geniusrise/geniusrise/core/state/postgres.py`
- `/run/media/ixaxaar/src/code/src/ORGS/geniusrise/geniusrise/geniusrise/core/state/dynamo.py`

### Data Backends to Remove

- `/run/media/ixaxaar/src/code/src/ORGS/geniusrise/geniusrise/geniusrise/core/data/batch_input.py`
- `/run/media/ixaxaar/src/code/src/ORGS/geniusrise/geniusrise/geniusrise/core/data/batch_output.py`
- `/run/media/ixaxaar/src/code/src/ORGS/geniusrise/geniusrise/geniusrise/core/data/streaming_input.py`
- `/run/media/ixaxaar/src/code/src/ORGS/geniusrise/geniusrise/geniusrise/core/data/streaming_output.py`

## Packages to Create

The complete separation approach requires creating the following separate
packages:

### State Backend Packages

1. geniusrise-state-redis (completed)
2. geniusrise-state-postgres
3. geniusrise-state-dynamo

### Data Backend Packages

1. geniusrise-data-s3 (completed - batch input/output)
2. geniusrise-data-kafka (streaming input/output)

### Runner Packages

1. geniusrise-runner-k8s
2. geniusrise-runner-docker
3. geniusrise-runner-openstack

## Implementation Steps

For each new package, follow these steps:

1. Create package structure:

   ```
   mkdir -p geniusrise-{type}-{backend}/geniusrise_{type}_{backend}
   ```

2. Create basic files:

   ```
   touch geniusrise-{type}-{backend}/setup.py
   touch geniusrise-{type}-{backend}/README.md
   touch geniusrise-{type}-{backend}/requirements.txt
   touch geniusrise-{type}-{backend}/geniusrise_{type}_{backend}/__init__.py
   ```

3. Copy implementation files from the core package to the new package:

   ```
   cp geniusrise/geniusrise/core/state/{backend}.py geniusrise-state-{backend}/geniusrise_state_{backend}/{backend}_state.py
   # or for data backends
   cp geniusrise/geniusrise/core/data/{backend}_input.py geniusrise-data-{backend}/geniusrise_data_{backend}/{backend}_input.py
   cp geniusrise/geniusrise/core/data/{backend}_output.py geniusrise-data-{backend}/geniusrise_data_{backend}/{backend}_output.py
   ```

4. Update imports in the new package files to use the core package interfaces.

5. Implement plugin registration in the package's **init**.py.

6. Complete setup.py with proper dependencies and entry_points.

## After Implementing All Packages

1. Run tests to ensure functionality:

   ```
   pip install -e .
   pytest geniusrise/core/tests/
   ```

2. Test plugin discovery:

   ```
   cd geniusrise-state-redis
   pip install -e .
   python -c "from geniusrise import show_available_components; print(show_available_components())"
   ```

3. Remove the old implementation files from the core package.

4. Update documentation to reflect the new architecture.
