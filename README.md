![logo_with_text](https://github.com/geniusrise/.github/assets/144122/2f8e51ee-0fcd-4f74-90fd-97301ef7943d)

### AI Ecosystem

<h3 align="center">
  <a style="color:#f34960" href="https://docs.geniusrise.ai">Documentation</a>
  ||
  <a style="color:#f34960" href="https://github.com/geniusrise/examples">Examples</a>
  ||
  <a style="color:#f34960" href="https://geniusrise.com">Cloud</a>
</h3>

### <span style="color:#e667aa">About</span>

<span style="color:#e4e48c">Geniusrise</span> is a modular, loosely-coupled
MLOps framework designed for the era of Large Language Models,
offering flexibility and standardization in designing networks of
AI agents.

It defines components and orchestrates them providing observability, state management and data handling,
all while supporting diverse infrastructures. With its modular and unopinonated architecture,
<span style="color:#e4e48c">Geniusrise</span> empowers teams to build, share,
and deploy AI across various platforms.

Geniusrise is powered by its components:

- [geniusrise-text](https://github.com/geniusrise/geniusrise-text): Text components offerring:
  - Inference APIs
  - Bulk inference
  - Fine-tuning
- [geniusrise-audio](https://github.com/geniusrise/geniusrise-audio): Audio components offerring:
  - Inference APIs
  - Bulk inference
  - Fine-tuning
- [geniusrise-vision](https://github.com/geniusrise/geniusrise-vision): Vision components offerring:
  - Inference APIs
  - Bulk inference
  - Fine-tuning
- [geniusrise-listeners](https://github.com/geniusrise/geniusrise-listeners): Streaming data ingestion
- [geniusrise-databases](https://github.com/geniusrise/geniusrise-databases): Bulk data ingestion

# Usage

The easiest way to use geniusrise is to host an API over a desired model.
Use one of the examples from [text](https://github.com/geniusrise/examples/tree/master/cli/api/text), [vision](https://github.com/geniusrise/examples/tree/master/cli/api/vision) or [audio](https://github.com/geniusrise/examples/tree/master/cli/api/audio).

## Run on Local

Say, we are interested in running an API over a vision / multi-modal model such as bakLlava:

### 1. Install geniusrise and vision

```bash
pip install torch
pip install geniusrise
pip install geniusrise-vision # vision multi-modal models
# pip install geniusrise-text # text models, LLMs
# pip install geniusrise-audio # audio models
```

### 2. Use the genius cli to run bakLlava

Create a YAML file named `genius.yml`:

```yaml
version: '1'

bolts:
    my_bolt:
        name: VisualQAAPI
        state:
            type: none
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
            model_class: 'LlavaForConditionalGeneration'
            processor_class: 'AutoProcessor'
            device_map: 'cuda:0'
            use_cuda: True
            precision: 'bfloat16'
            quantization: 0
            max_memory: None
            torchscript: False
            compile: False
            flash_attention: False
            better_transformers: False
            endpoint: '*'
            port: 3000
            cors_domain: 'http://localhost:3000'
            username: 'user'
            password: 'password'
```

Navigate to the directory and do:

```bash
genius rise
```

### 3. Test the API

```bash
MY_IMAGE=/path/to/test/image

(base64 -w 0 $MY_IMAGE | awk '{print "{\"image_base64\": \""$0"\", \"question\": \"<image>\nUSER: Whats the content of the image?\nASSISTANT:\", \"do_sample\": false, \"max_new_tokens\": 128}"}' > /tmp/image_payload.json)
curl -X POST http://localhost:3000/api/v1/answer_question \
    -H "Content-Type: application/json" \
    -u user:password \
    -d @/tmp/image_payload.json | jq
```

# Explore

See [usage](https://docs.geniusrise.ai/guides/usage/) for more advanced examples.
There are over 150 examples for [text](https://github.com/geniusrise/examples/tree/master/cli/api/text), [vision](https://github.com/geniusrise/examples/tree/master/cli/api/vision) and [audio](https://github.com/geniusrise/examples/tree/master/cli/api/audio).

### <span style="color:#e667aa">Links</span>

- **Website**: [geniusrise.ai](https://geniusrise.ai)

# Framework

This is the base geniusrise framework, also the `genius` CLI.
It provides the base structure and orchestration primitives for `Spout`s and `Bolt`s, and also covers operations.
- **Docs**: [docs.geniusrise.ai](https://docs.geniusrise.ai)
- **Examples**: [geniusrise/examples](https://github.com/geniusrise/examples)
- **Cloud**: [geniusrise.com](https://geniusrise.com)

