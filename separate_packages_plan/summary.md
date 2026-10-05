# Geniusrise Package Separation Plan Summary

## Current Status

We have successfully merged Bolt and Spout into a unified Task class and
implemented partial modularization by making dependencies optional within the
same codebase. However, the codebase still includes all optional backends,
which:

1. Bloats the core package with unnecessary code
2. Makes maintenance more complex
3. Complicates testing and continuous integration
4. Doesn't provide a clean plugin architecture

## Proposed Solution: Complete Separation

We will completely separate optional components into their own packages:

1. Core Package (geniusrise)

   - Fundamental classes and interfaces
   - Plugin management system
   - No optional dependencies

2. Optional State Backends

   - geniusrise-state-redis
   - geniusrise-state-postgres
   - geniusrise-state-dynamo

3. Optional Data Backends

   - geniusrise-data-s3 (for batch operations)
   - geniusrise-data-kafka (for streaming)

4. Runner Plugins (existing plan)
   - geniusrise-runner-k8s
   - geniusrise-runner-docker
   - geniusrise-runner-openstack

## Benefits

1. **Cleaner Core Package**

   - Smaller size
   - Fewer dependencies
   - Easier to maintain

2. **True Plugin Architecture**

   - Automatic discovery and registration
   - Clear interfaces for extensions
   - Independent release cycles

3. **Improved User Experience**

   - Install only what's needed
   - Reduced dependency conflicts
   - Clearer documentation

4. **Better Development Workflow**
   - Independent testing
   - Focused pull requests
   - Simplified CI/CD

## Implementation Approach

1. **Core Restructuring**

   - Create a plugin system for backend registration
   - Remove optional implementations from core
   - Update Task class to use registered backends

2. **Package Creation**

   - Move implementations to separate packages
   - Create proper entry points for auto-discovery
   - Set up proper dependency management

3. **Testing & Documentation**
   - Test with various backend combinations
   - Update documentation for new architecture
   - Create examples showing plugin usage

## Timeline

- Core restructuring: 2 days
- State backend packages: 2 days
- Data backend packages: 2 days
- Testing and documentation: 2 days

Total: 8 days of development work

## User Migration

For users, migration will be straightforward:

**Current:**

```bash
pip install "geniusrise[redis,s3,kafka]"
```

**New:**

```bash
pip install geniusrise geniusrise-state-redis geniusrise-data-s3 geniusrise-data-kafka
```

The API remains backward compatible with automatic backend discovery, so
existing code will work with minimal changes.

## Conclusion

This complete separation is a significant architectural improvement that will
enhance maintainability, flexibility, and user experience. While it breaks
backward compatibility at the package level, it provides a cleaner, more
scalable foundation for the framework's future.

The detailed implementation plan has been prepared, with example packages ready
to be created as soon as approval is given.
