# 🧠 Geniusrise

### Unified Local AI Inference Framework

<h3 align="center">
  <a href="https://docs.geniusrise.ai">Documentation</a>
  ||
  <a href="https://github.com/geniusrise/examples">Examples</a>
</h3>

## About

**Geniusrise 0.2** is a unified, lean inference framework designed for **local desktop AI workloads**. It consolidates vision, text, and audio model inference into a single, focused package with a simple mental model:

- **API mode**: Serve models via HTTP/REST endpoints
- **Batch mode**: Process files from input → output folders
- **Streaming mode**: Real-time processing via Kafka

**No training. No fine-tuning. Just inference.**

### What's New in 0.2

- 🎯 **Unified Architecture**: Vision, text, and audio merged into one package
- 🗑️ **Removed**: All training/fine-tuning code, Airflow dependency, OpenStack runners
- 🚀 **Simplified**: Single `InferenceTask` base class (no more Bolt/Spout complexity)
- 💾 **State**: PostgreSQL only (removed Redis, DynamoDB, InMemory)
- ⚡ **Modern Stack**: FastAPI, Typer, Rich, PyTorch-first
- 📦 **60% fewer dependencies**: ~40 packages instead of ~100+

## Installation

```bash
pip install torch torchvision torchaudio  # Install PyTorch first
pip install geniusrise==0.2.0
```

That's it! Vision, text, and audio are all included by default.

## Quick Start

### 1. Vision Inference (Visual QA)

Create `config.yml`:

```yaml
version: '1'

tasks:
  my_vision_api:
    type: vision
    mode: api
    model:
      name: 'llava-hf/bakLlava-v1-hf'
      device: 'cuda:0'
      precision: 'bfloat16'
    server:
      host: '0.0.0.0'
      port: 3000
      auth:
        username: 'user'
        password: 'password'
```

Run it:

```bash
genius run config.yml
```

Test it:

```bash
MY_IMAGE=/path/to/image.jpg

(base64 -w 0 $MY_IMAGE | awk '{print "{\"image_base64\": \""$0"\", \"question\": \"What is in this image?\"}"}' > /tmp/payload.json)
curl -X POST http://localhost:3000/api/v1/answer_question \
    -H "Content-Type: application/json" \
    -u user:password \
    -d @/tmp/payload.json | jq
```

### 2. Text Inference (LLM)

```yaml
version: '1'

tasks:
  llama_api:
    type: text
    mode: api
    model:
      name: 'meta-llama/Llama-2-7b-chat-hf'
      device: 'cuda:0'
      precision: 'float16'
      quantization: 4  # 4-bit quantization
    server:
      host: '0.0.0.0'
      port: 8000
```

```bash
genius run config.yml
```

### 3. Audio Inference (Speech-to-Text)

```yaml
version: '1'

tasks:
  whisper_batch:
    type: audio
    mode: batch
    model:
      name: 'openai/whisper-large-v3'
      device: 'cuda:0'
    input:
      path: ./audio_files
      format: mp3
    output:
      path: ./transcriptions
      format: json
```

```bash
genius run config.yml
```

### 4. Batch Processing

Process a folder of images for classification:

```yaml
version: '1'

tasks:
  classify_images:
    type: vision
    mode: batch
    model:
      name: 'google/vit-base-patch16-224'
      device: 'cuda:0'
    input:
      path: ./input_images
      format: jpg,png
    output:
      path: ./results
      format: jsonl
```

## Supported Models

### Vision
- Image Classification (ViT, ResNet, ConvNeXt)
- Segmentation (Mask2Former, SAM, SegFormer)
- OCR (EasyOCR, PaddleOCR, Nougat, Donut)
- Visual QA (LLaVA, BLIP-2, GIT, Uform)

### Text
- Language Models (Llama, Mistral, GPT-2, OPT)
- Instruction Following (Alpaca, Vicuna, Orca)
- Classification (BERT, RoBERTa, DeBERTa)
- NER, NLI, QA, Translation
- Sentence Embeddings (Sentence-BERT)

### Audio
- Speech-to-Text (Whisper, Wav2Vec2, SeamlessM4T)
- Text-to-Speech (MMS, Bark, SpeechT5)

## CLI Commands

The new CLI is built with Typer and Rich for a better experience:

```bash
# Run a config file
genius run config.yml

# Run a specific task from config
genius run config.yml --task llama_api

# Deploy to Kubernetes
genius deploy config.yml --target kubernetes

# Show running tasks
genius status

# View logs
genius logs <task-id>

# Stop a task
genius stop <task-id>
```

## Architecture

### Old (0.1.x) - Removed
```
❌ Bolt → Spout chains (Storm-like)
❌ Discovery mechanism for plugins
❌ Multiple state backends (Redis, Dynamo, Memory)
❌ Separate packages (geniusrise-vision, geniusrise-text, geniusrise-audio)
❌ Training & fine-tuning code
❌ Airflow orchestration
❌ OpenStack runners
```

### New (0.2.x) - Simplified
```
✅ Single InferenceTask base class
✅ Three modes: API, Batch, Streaming
✅ All modalities in one package
✅ Inference only
✅ PostgreSQL state only
✅ FastAPI servers
✅ Kubernetes + Docker runners
```

## Migration from 0.1.x

See [MIGRATION.md](MIGRATION.md) for detailed upgrade instructions.

**Breaking changes:**
- `Bolt` and `Spout` classes removed → Use `InferenceTask`
- Package imports changed: `geniusrise_text.*` → `geniusrise.inference.text.*`
- YAML schema updated
- State backends limited to PostgreSQL
- Training/fine-tuning removed

## Configuration Schema

```yaml
version: '1'

tasks:
  <task_name>:
    type: vision | text | audio
    mode: api | batch | streaming

    # Model configuration
    model:
      name: str                    # HuggingFace model ID or path
      device: str                  # 'cuda:0', 'cpu', etc.
      precision: str               # 'float32', 'float16', 'bfloat16'
      quantization: int            # 4, 8, or 0 (no quantization)
      max_memory: dict             # Optional memory limits

    # API mode specific
    server:
      host: str
      port: int
      auth:
        username: str
        password: str
      cors:
        origins: list[str]

    # Batch mode specific
    input:
      path: str
      format: str

    output:
      path: str
      format: str
      s3_bucket: str               # Optional S3 sync

    # Streaming mode specific
    streaming:
      kafka_brokers: list[str]
      input_topic: str
      output_topic: str

    # State management
    state:
      host: str
      port: int
      database: str
      user: str
      password: str
```

## Development

```bash
# Clone the repo
git clone https://github.com/geniusrise/geniusrise
cd geniusrise

# Install in dev mode
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black geniusrise/
flake8 geniusrise/
```

## Philosophy

Geniusrise 0.2 embraces simplicity:

1. **Local first**: Optimized for GPU workstations, not distributed cloud
2. **Inference only**: Training belongs elsewhere (use HuggingFace Transformers directly)
3. **One way to do things**: PostgreSQL for state, FastAPI for servers, Kafka for streaming
4. **Clear modes**: API xor Batch xor Streaming - no mixing
5. **Batteries included**: All modalities in one package

## Use Cases

✅ **Perfect for:**
- Local development with LLMs/Vision/Audio models
- Prototyping inference APIs
- Batch processing of media files
- Deploying to Kubernetes clusters
- Desktop AI applications

❌ **Not designed for:**
- Training models (use PyTorch/HuggingFace directly)
- Fine-tuning (removed in 0.2)
- Distributed training orchestration
- Cloud-native MLOps pipelines

## License

Apache 2.0

## Links

- **Documentation**: [docs.geniusrise.ai](https://docs.geniusrise.ai)
- **GitHub**: [github.com/geniusrise/geniusrise](https://github.com/geniusrise/geniusrise)
- **Issues**: [github.com/geniusrise/geniusrise/issues](https://github.com/geniusrise/geniusrise/issues)

---

**v0.2.0** - Complete rewrite focused on local inference. See changelog for full details.
