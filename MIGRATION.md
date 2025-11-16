# Migration Guide: 0.1.x → 0.2.0

This guide helps you migrate from Geniusrise 0.1.x to the completely refactored 0.2.0.

## ⚠️ Breaking Changes Overview

Geniusrise 0.2.0 is a **complete architectural rewrite**. This is not a drop-in replacement for 0.1.x.

### What Was Removed

- ❌ **Bolt and Spout classes** - Replaced with unified `InferenceTask`
- ❌ **Training & fine-tuning** - All fine-tuning code removed
- ❌ **Discovery mechanism** - No more plugin auto-discovery
- ❌ **Multiple state backends** - Only PostgreSQL now (removed Redis, DynamoDB, InMemory)
- ❌ **Airflow orchestration** - Removed dependency
- ❌ **OpenStack runners** - Removed completely
- ❌ **Separate packages** - `geniusrise-vision`, `geniusrise-text`, `geniusrise-audio` merged into main package

### What Was Added

- ✅ **Unified InferenceTask** - Single base class for all inference
- ✅ **Clear execution modes** - API, Batch, Streaming
- ✅ **FastAPI** - Modern API framework
- ✅ **Typer + Rich CLI** - Better command-line experience
- ✅ **All modalities included** - Vision, text, audio in one package

---

## Installation Changes

### Old (0.1.x)

```bash
pip install geniusrise
pip install geniusrise-vision  # Separate packages
pip install geniusrise-text
pip install geniusrise-audio
```

### New (0.2.0)

```bash
pip install torch torchvision torchaudio  # PyTorch first
pip install geniusrise==0.2.0              # Everything included
```

---

## Import Changes

### Vision

**Old:**
```python
from geniusrise_vision import VisionAPI, VisionBulk
from geniusrise_vision.imgclass import ImageClassificationAPI
from geniusrise_vision.vqa import VisualQAAPI
```

**New:**
```python
from geniusrise.inference.vision.api.imgclass import ImageClassificationAPI
from geniusrise.inference.vision.api.vqa import VisualQAAPI
from geniusrise.inference.vision.bulk.imgclass import ImageClassificationBulk
```

### Text

**Old:**
```python
from geniusrise_text import TextAPI, TextBulk
from geniusrise_text.classification import TextClassificationAPI
from geniusrise_text.instruction import InstructionAPI
```

**New:**
```python
from geniusrise.inference.text.api.classification import TextClassificationAPI
from geniusrise.inference.text.api.instruction import InstructionAPI
from geniusrise.inference.text.bulk.classification import TextClassificationBulk
```

### Audio

**Old:**
```python
from geniusrise_audio import AudioAPI, AudioBulk
from geniusrise_audio.s2t import SpeechToTextAPI
from geniusrise_audio.t2s import TextToSpeechAPI
```

**New:**
```python
from geniusrise.inference.audio.api.s2t import SpeechToTextAPI
from geniusrise.inference.audio.api.t2s import TextToSpeechAPI
from geniusrise.inference.audio.bulk.s2t import SpeechToTextBulk
```

---

## Code Migration Examples

### Example 1: Bolt → InferenceTask (Custom Inference)

**Old (0.1.x):**
```python
from geniusrise import Bolt, BatchInput, BatchOutput

class MyProcessor(Bolt):
    def process(self, data):
        # Processing logic
        self.output.save(result)

# Usage
bolt = Bolt.create(
    input=BatchInput("./input"),
    output=BatchOutput("./output"),
    state={"type": "redis", ...}
)
bolt("process")
```

**New (0.2.0):**
```python
from geniusrise.inference import InferenceTask, InferenceMode

class MyProcessor(InferenceTask):
    def __init__(self, **kwargs):
        super().__init__(
            task_id="my_processor",
            mode=InferenceMode.BATCH,
            **kwargs
        )

    def load_model(self, **kwargs):
        # Load your model
        pass

    def run_batch(self, input_path, output_path, **kwargs):
        # Process files from input_path
        # Write results to output_path
        pass

    def run_api(self, **kwargs):
        # Not used for batch processing
        raise NotImplementedError()

# Usage
processor = MyProcessor(
    state_config={"host": "localhost", "port": 5432, "database": "mydb"}
)
processor.execute(input_path="./input", output_path="./output")
```

### Example 2: Vision API Migration

**Old (0.1.x):**
```python
from geniusrise_vision.vqa import VisualQAAPI

api = VisualQAAPI.create(
    output=BatchOutput("./output"),
    state={"type": "postgres", ...}
)
api.listen(
    model_name="llava-hf/bakLlava-v1-hf",
    device_map="cuda:0",
    endpoint="*",
    port=3000
)
```

**New (0.2.0):**
```python
from geniusrise.inference.vision.api.vqa import VisualQAAPI

api = VisualQAAPI(
    task_id="vqa_api",
    mode=InferenceMode.API,
    state_config={"host": "localhost", "port": 5432, "database": "mydb"}
)
api.execute(
    model_name="llava-hf/bakLlava-v1-hf",
    device="cuda:0",
    host="0.0.0.0",
    port=3000
)
```

Or use the config file approach:

```yaml
# config.yml
version: '1'

tasks:
  vqa_api:
    type: vision
    mode: api
    model:
      name: 'llava-hf/bakLlava-v1-hf'
      device: 'cuda:0'
    server:
      host: '0.0.0.0'
      port: 3000
```

```bash
genius run config.yml
```

### Example 3: Text Bulk Processing

**Old (0.1.x):**
```python
from geniusrise_text.classification import TextClassificationBulk

bulk = TextClassificationBulk.create(
    input=BatchInput("./input"),
    output=BatchOutput("./output"),
    state={"type": "memory"}
)
bulk.classify(
    model_name="bert-base-uncased",
    device_map="cuda:0"
)
```

**New (0.2.0):**
```python
from geniusrise.inference.text.bulk.classification import TextClassificationBulk

bulk = TextClassificationBulk(
    task_id="text_classify",
    mode=InferenceMode.BATCH,
    state_config={"host": "localhost", "port": 5432, "database": "mydb"}
)
bulk.execute(
    model_name="bert-base-uncased",
    device="cuda:0",
    input_path="./input",
    output_path="./output"
)
```

---

## YAML Configuration Changes

### Old (0.1.x)

```yaml
version: '1'

bolts:
  my_bolt:
    name: VisualQAAPI
    state:
      type: redis
      host: localhost
      port: 6379
    input:
      type: batch
      args:
        input_folder: ./input
    output:
      type: batch
      args:
        output_folder: ./output
    method: listen
    args:
      model_name: 'llava-hf/bakLlava-v1-hf'
      device_map: 'cuda:0'
      endpoint: '*'
      port: 3000
```

### New (0.2.0)

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
    state:
      host: localhost
      port: 5432
      database: mydb
      user: postgres
      password: secret
```

---

## State Management Changes

### Only PostgreSQL Supported

**Old (0.1.x):**
```python
# Multiple backends available
from geniusrise import RedisState, DynamoDBState, InMemoryState

state = RedisState(id="task", host="localhost", port=6379)
state = DynamoDBState(id="task", table_name="tasks", region="us-east-1")
state = InMemoryState(id="task")
```

**New (0.2.0):**
```python
# Only PostgreSQL
from geniusrise import PostgresState

state = PostgresState(
    id="task",
    host="localhost",
    port=5432,
    database="mydb",
    user="postgres",
    password="secret"
)
```

---

## CLI Changes

### Old (0.1.x)

```bash
# Complex bolt/spout commands
genius bolt rise \
    --bolt-class MyBolt \
    --bolt-module mymodule \
    ...

genius spout rise \
    --spout-class MySpout \
    ...
```

### New (0.2.0)

```bash
# Simple config-based approach
genius run config.yml
genius run config.yml --task my_task
genius deploy config.yml --target kubernetes
genius status
genius logs <task-id>
```

---

## Fine-Tuning Removed

### What To Use Instead

Fine-tuning has been completely removed from Geniusrise 0.2. For training/fine-tuning, use:

**Recommended alternatives:**
- [HuggingFace Transformers](https://huggingface.co/docs/transformers/training) - Direct training APIs
- [PyTorch Lightning](https://lightning.ai/) - Training framework
- [Axolotl](https://github.com/OpenAccess-AI-Collective/axolotl) - LLM fine-tuning
- [PEFT](https://github.com/huggingface/peft) - Parameter-efficient fine-tuning
- [TRL](https://github.com/huggingface/trl) - Transformer reinforcement learning

Geniusrise 0.2 focuses **exclusively on inference**.

---

## Deployment Changes

### Removed: OpenStack

OpenStack runners have been completely removed. Use Kubernetes or Docker instead.

**Old (0.1.x):**
```bash
genius bolt deploy openstack \
    --image my-image \
    --flavor m1.large \
    ...
```

**New (0.2.0):**
```bash
# Use Kubernetes
genius deploy config.yml --target kubernetes

# Or deploy individual tasks
kubectl apply -f deployment.yaml  # Generated from config
```

---

## Testing Your Migration

After migrating, test your setup:

```bash
# 1. Install new version
pip install geniusrise==0.2.0

# 2. Create a simple config
cat > test.yml <<EOF
version: '1'
tasks:
  test_api:
    type: text
    mode: api
    model:
      name: 'gpt2'
      device: 'cpu'
    server:
      host: '127.0.0.1'
      port: 8000
EOF

# 3. Run it
genius run test.yml

# 4. Test the API
curl http://localhost:8000/health
```

---

## Common Issues

### Issue: Import errors

**Problem:**
```python
ImportError: cannot import name 'Bolt' from 'geniusrise.core'
```

**Solution:**
`Bolt` and `Spout` have been removed. Use `InferenceTask` or the pre-built inference classes.

### Issue: State backend not found

**Problem:**
```python
ImportError: cannot import name 'RedisState'
```

**Solution:**
Only `PostgresState` is supported now. Migrate your state to PostgreSQL.

### Issue: Fine-tuning code not found

**Problem:**
```python
ImportError: cannot import name 'FineTuner'
```

**Solution:**
Fine-tuning has been removed. Use HuggingFace Transformers or other training frameworks directly.

---

## Need Help?

- **Documentation**: https://docs.geniusrise.ai
- **Issues**: https://github.com/geniusrise/geniusrise/issues
- **Discord**: (coming soon)

For complex migrations, consider:
1. Reviewing the [examples](https://github.com/geniusrise/examples)
2. Starting fresh with the new API
3. Opening an issue for migration support

---

**Note**: This is a major version bump in spirit (0.1→0.2 but architecturally equivalent to 1.0→2.0). Take time to understand the new architecture before migrating production workloads.
