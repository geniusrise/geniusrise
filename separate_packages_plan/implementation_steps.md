# Implementation Steps for Splitting Optional Components

## Phase 1: Prepare the Core Package

1. **Remove Optional Backend Files**

   - Remove `geniusrise/core/state/redis.py`
   - Remove `geniusrise/core/state/postgres.py`
   - Remove `geniusrise/core/state/dynamo.py`
   - Remove `geniusrise/core/data/batch_input.py`
   - Remove `geniusrise/core/data/batch_output.py`
   - Remove `geniusrise/core/data/streaming_input.py`
   - Remove `geniusrise/core/data/streaming_output.py`

2. **Create Registry System**

   - Create `geniusrise/core/state/registry.py` for state backend registration
   - Create `geniusrise/core/data/input_registry.py` for input backend
     registration
   - Create `geniusrise/core/data/output_registry.py` for output backend
     registration

3. **Update Module Imports**

   - Update `geniusrise/core/state/__init__.py` to use registry
   - Update `geniusrise/core/data/__init__.py` to use registry
   - Update `geniusrise/core/__init__.py` with new registry exports

4. **Update Task Class**

   - Modify the `create` method in `geniusrise/core/task.py` to use registry
   - Add error handling for missing backends

5. **Update Setup Files**
   - Update `setup.py` to remove optional extras
   - Create/update `requirements-core.txt` with minimal dependencies
   - Update `requirements.txt` to document optional packages

## Phase 2: Create Separate Packages

1. **Create State Backend Packages**

   For each state backend (redis, postgres, dynamo):

   a. Create package structure:

   ```
   mkdir -p geniusrise-state-{backend}/geniusrise_state_{backend}
   touch geniusrise-state-{backend}/geniusrise_state_{backend}/__init__.py
   touch geniusrise-state-{backend}/setup.py
   touch geniusrise-state-{backend}/README.md
   touch geniusrise-state-{backend}/requirements.txt
   ```

   b. Move implementation:

   ```
   cp <existing_backend_file> geniusrise-state-{backend}/geniusrise_state_{backend}/{backend}_state.py
   ```

   c. Update imports and necessary code

   d. Complete setup.py, README.md and other files

   e. Test the package locally:

   ```
   cd geniusrise-state-{backend}
   pip install -e .
   ```

2. **Create Data Backend Packages**

   For each data backend (s3, kafka):

   a. Create package structure:

   ```
   mkdir -p geniusrise-data-{backend}/geniusrise_data_{backend}
   touch geniusrise-data-{backend}/geniusrise_data_{backend}/__init__.py
   touch geniusrise-data-{backend}/setup.py
   touch geniusrise-data-{backend}/README.md
   touch geniusrise-data-{backend}/requirements.txt
   ```

   b. Move implementation:

   ```
   # For S3
   cp <existing_batch_input_file> geniusrise-data-s3/geniusrise_data_s3/batch_input.py
   cp <existing_batch_output_file> geniusrise-data-s3/geniusrise_data_s3/batch_output.py

   # For Kafka
   cp <existing_streaming_input_file> geniusrise-data-kafka/geniusrise_data_kafka/streaming_input.py
   cp <existing_streaming_output_file> geniusrise-data-kafka/geniusrise_data_kafka/streaming_output.py
   ```

   c. Update imports and necessary code

   d. Complete setup.py, README.md and other files

   e. Test the package locally:

   ```
   cd geniusrise-data-{backend}
   pip install -e .
   ```

## Phase 3: Testing and Documentation

1. **Test Core Package**

   - Install geniusrise core without any backends
   - Verify that AVAILABLE\_\* dictionaries are empty
   - Test that Task creation works with InMemoryState

2. **Test Plugin Loading**

   - Install geniusrise core
   - Install one or more backend packages
   - Verify that backends are correctly registered
   - Test Task creation with different backends

3. **Update Documentation**

   - Update main README.md with new package structure
   - Create individual package documentation
   - Update YAML example with new structure
   - Document plugin development process

4. **Create Example Projects**
   - Create example showing how to use multiple backends
   - Create example showing how to discover available backends
   - Create example showing fallback behavior

## Phase 4: Publishing

1. **Publish Core Package**

   - Update version number
   - Publish to PyPI

2. **Publish Backend Packages**

   - Publish all state backend packages
   - Publish all data backend packages
   - Test installation from PyPI

3. **Announce Changes**
   - Create blog post or announcement
   - Update documentation site

## Quick-Start Commands

Here are the quick-start commands to create the package structure:

```bash
# Create state backend packages
mkdir -p geniusrise-state-redis/geniusrise_state_redis
mkdir -p geniusrise-state-postgres/geniusrise_state_postgres
mkdir -p geniusrise-state-dynamo/geniusrise_state_dynamo

# Create data backend packages
mkdir -p geniusrise-data-s3/geniusrise_data_s3
mkdir -p geniusrise-data-kafka/geniusrise_data_kafka

# Create basic files for each package
for pkg in redis postgres dynamo; do
  touch geniusrise-state-$pkg/geniusrise_state_$pkg/__init__.py
  touch geniusrise-state-$pkg/setup.py
  touch geniusrise-state-$pkg/README.md
  touch geniusrise-state-$pkg/requirements.txt
done

for pkg in s3 kafka; do
  touch geniusrise-data-$pkg/geniusrise_data_$pkg/__init__.py
  touch geniusrise-data-$pkg/setup.py
  touch geniusrise-data-$pkg/README.md
  touch geniusrise-data-$pkg/requirements.txt
done

# Copy implementation files
cp geniusrise/geniusrise/core/state/redis.py geniusrise-state-redis/geniusrise_state_redis/redis_state.py
cp geniusrise/geniusrise/core/state/postgres.py geniusrise-state-postgres/geniusrise_state_postgres/postgres_state.py
cp geniusrise/geniusrise/core/state/dynamo.py geniusrise-state-dynamo/geniusrise_state_dynamo/dynamo_state.py

cp geniusrise/geniusrise/core/data/batch_input.py geniusrise-data-s3/geniusrise_data_s3/batch_input.py
cp geniusrise/geniusrise/core/data/batch_output.py geniusrise-data-s3/geniusrise_data_s3/batch_output.py
cp geniusrise/geniusrise/core/data/streaming_input.py geniusrise-data-kafka/geniusrise_data_kafka/streaming_input.py
cp geniusrise/geniusrise/core/data/streaming_output.py geniusrise-data-kafka/geniusrise_data_kafka/streaming_output.py
```
