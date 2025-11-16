# Changelog

All notable changes to Geniusrise will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2024-11-16

### 🎯 Complete Architectural Rewrite

This is a **major breaking release** that completely refactors Geniusrise from a general-purpose MLOps framework into a focused **local AI inference framework**.

### Added

- ✅ **Unified `InferenceTask` base class** - Replaces Bolt/Spout pattern with simpler architecture
- ✅ **Three clear execution modes**: API, Batch, Streaming
- ✅ **Merged modalities into core**:
  - `geniusrise.inference.vision` - 4 API classes, 3 Bulk classes (~2,400 LOC)
  - `geniusrise.inference.text` - 9 API classes, 9 Bulk classes (~9,000 LOC)
  - `geniusrise.inference.audio` - 4 API classes, 4 Bulk classes (~2,800 LOC)
- ✅ **Modern CLI with Typer + Rich** - Better UX, colored output, progress bars
- ✅ **FastAPI support** - Modern async API framework (replacing Flask/Connexion)
- ✅ **PyTorch-first approach** - Direct PyTorch integration as primary ML framework
- ✅ **Simplified YAML schema** - Clearer configuration with `type`, `mode`, `model`, `server`
- ✅ **Comprehensive migration guide** - MIGRATION.md for 0.1.x users

### Changed

- 🔄 **State management simplified** - PostgreSQL only (removed Redis, DynamoDB, InMemory backends)
- 🔄 **Data I/O clarified** - Clear separation between Batch and Streaming modes
- 🔄 **Dependencies reduced by 60%** - From ~100 packages to ~40 core packages
- 🔄 **Package structure reorganized**:
  ```
  Old: geniusrise.core.{bolt,spout}
  New: geniusrise.inference.{vision,text,audio}/{api,bulk,utils}
  ```
- 🔄 **Import paths changed**:
  - `geniusrise_vision.*` → `geniusrise.inference.vision.*`
  - `geniusrise_text.*` → `geniusrise.inference.text.*`
  - `geniusrise_audio.*` → `geniusrise.inference.audio.*`
- 🔄 **Version bump** - 0.1.7 → 0.2.0
- 🔄 **Package description** - "An LLM framework" → "Unified local AI inference framework for vision, text, and audio models"
- 🔄 **Development status** - Alpha → Beta

### Removed

- ❌ **Bolt and Spout classes** - Old Apache Storm-inspired architecture
- ❌ **All training/fine-tuning code** - Removed from vision, text, audio modules (~4,000 LOC removed)
- ❌ **Discovery mechanism** - No more plugin auto-discovery (`discover.py`, `boltctl.py`, `spoutctl.py`)
- ❌ **Apache Airflow dependency** - Removed orchestration framework and all providers
- ❌ **OpenStack runners** - Removed cloud infrastructure support (`geniusrise/runners/openstack/`)
- ❌ **Non-PostgreSQL state backends**:
  - `geniusrise.core.state.redis.RedisState`
  - `geniusrise.core.state.dynamo.DynamoDBState`
  - `geniusrise.core.state.memory.InMemoryState`
- ❌ **Separate packages requirement** - No longer need `geniusrise-vision`, `geniusrise-text`, `geniusrise-audio`
- ❌ **Flask/Connexion dependencies** - Replaced with FastAPI
- ❌ **HuggingFace training dependencies** - Removed `peft`, `trl`, training-specific packages

### Deprecated

- ⚠️ **Old YAML schema** - `bolts` and `spouts` keys replaced with `tasks`
- ⚠️ **Old CLI commands** - `genius bolt rise`, `genius spout rise` removed

### Fixed

- 🐛 **Import consistency** - All inference code now under unified namespace
- 🐛 **Dependency conflicts** - Removed conflicting Airflow pins
- 🐛 **State backend confusion** - Single clear choice (PostgreSQL)

### Security

- 🔒 **Reduced attack surface** - 60% fewer dependencies means fewer vulnerabilities
- 🔒 **Simplified auth** - FastAPI-based auth instead of complex Flask middleware

## Migration from 0.1.x

See [MIGRATION.md](MIGRATION.md) for detailed upgrade instructions.

**Key changes:**
1. Install: `pip install geniusrise==0.2.0` (includes all modalities)
2. Imports: Update from `geniusrise_*` to `geniusrise.inference.*`
3. Classes: Replace `Bolt`/`Spout` with `InferenceTask` or use pre-built classes
4. State: Migrate to PostgreSQL if using Redis/Dynamo/Memory
5. Config: Update YAML from `bolts`/`spouts` to `tasks` with new schema
6. Training: Move to HuggingFace Transformers or other frameworks

## [0.1.7] - 2024-01-XX

Previous stable release with Bolt/Spout architecture, separate modality packages, and full training support.

See git history for pre-0.2.0 changes.

---

## Versioning Philosophy

- **0.2.x**: Focused local inference framework (current)
- **0.1.x**: General MLOps framework (deprecated)

Breaking changes are documented in MIGRATION.md and this changelog.

[0.2.0]: https://github.com/geniusrise/geniusrise/compare/v0.1.7...v0.2.0
[0.1.7]: https://github.com/geniusrise/geniusrise/releases/tag/v0.1.7
