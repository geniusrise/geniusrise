# Geniusrise Cleanup and Modernization Plan

## Summary of Completed Changes

1. **Unified Architecture**: Merged Bolt and Spout into a single Task class with
   optional input/output
2. **Optional Dependencies**: Implemented pip extras for state backends, data
   backends, and runners
3. **Dependency Management**: Created requirements-core.txt and updated setup.py
   extras_require
4. **Component Discovery**: Added availability tracking for all optional
   components
5. **Documentation**: Updated README and docstrings to reflect the new
   architecture
6. **Error Handling**: Improved error messages for missing dependencies
7. **Code Quality**: Updated to consistent copyright years and improved typing

## COMPLETED: Task Unification (Removal of Bolt and Spout)

The framework previously had three similar concepts:

- Task: General purpose component
- Bolt: Component that consumes and produces data
- Spout: Component that only produces data

These have now been unified into a single Task class that can:

- Consume data (with optional input)
- Process data
- Produce data (with optional output)

This simplification makes the framework more intuitive and easier to maintain.

## COMPLETED: Dependency Management

- Created a `requirements-core.txt` with only essential dependencies
- Moved specialized dependencies to setup.py extras_require:
  - State backends: redis, postgres, dynamo
  - Data handling: s3, kafka
  - Runners: k8s, docker, openstack, full
- Updated requirements.txt to document optional dependencies
- Updated import structure to handle missing dependencies gracefully
- Added detailed error messages directing users to install specific extras

## 2. Cloud Provider Runners

### Current Issues

- Specialized cloud providers (acecloud, e2e_networks, openstack) in main
  package
- Tightly coupled with main framework
- Increases binary size and dependency list

### Solutions

- Move cloud providers to separate packages:
  - geniusrise-runner-openstack
  - geniusrise-runner-acecloud
  - geniusrise-runner-e2e
- Create a plugin system for runners in core/**init**.py
- Allow dynamic registration of runners

## 3. Build Artifacts

### Current Issues

- build/ and dist/ directories in repository
- **pycache** files checked in
- Increases repository size

### Solutions

- Update .gitignore to exclude all build artifacts
- Clean up existing build artifacts
- Document build process

## COMPLETED: Code Organization

- Created clear separation between core and optional components
- Implemented availability tracking for optional components:
  - AVAILABLE_DATA_INPUTS
  - AVAILABLE_DATA_OUTPUTS
  - AVAILABLE_STATE_BACKENDS
  - AVAILABLE_RUNNERS
- Created proper plugin points for:
  - State management backends
  - Data input/output backends
  - Infrastructure runners
- Added helper function to show available components:
  `show_available_components()`
- Updated documentation with examples of component availability checking
- Improved import structure with lazy loading of optional dependencies

## 5. Python Version Support

### Current Issues

- Only supports Python 3.10+
- Doesn't take advantage of newer Python features

### Solutions

- Update to support Python 3.11+ (primary)
- Use Python 3.10 compatibility layer for backward compatibility
- Document Python version requirements

## 6. Implementation Plan

### COMPLETED: Phase 1 - Core Cleanup

- ✅ Unified Bolt and Spout into Task
- ✅ Separated core dependencies
- ✅ Updated setup.py with extras_require
- ✅ Created requirements-core.txt

### COMPLETED: Phase 2 - Plugin Architecture (Partial)

- ✅ Created optional component structure with proper pip extras
- ✅ Improved import system for optional dependencies
- ✅ Added component availability tracking
- ✅ Updated documentation for optional components
- ⏳ Move cloud providers to separate packages

### Remaining: Phase 3 - Modernization

- ⏳ Update Python version support
- ⏳ Use newer Python features
- ⏳ Performance optimizations

## 7. Testing Plan

### Completed

- ✅ Basic verification of Task functionality
- ✅ Manual testing of import system with/without dependencies

### Remaining

- ⏳ Comprehensive test suite for Task with various input/output combinations
- ⏳ Test with and without optional dependencies (in CI/CD)
- ⏳ Test plugin loading mechanism for runners
- ⏳ Performance benchmarks before and after changes
- ⏳ Update existing tests for the new architecture
