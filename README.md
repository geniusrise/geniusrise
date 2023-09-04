<p align="center">
  <img src="./assets/grace-hopper.jpg" alt="Grace Hopper" width="900"/>
</p>

<h1 align="center">
  🧠 <span style="color:#f34960">Geniusrise</span>
</h1>

<p align="center">
  <img src="https://img.shields.io/github/actions/workflow/status/geniusrise/geniusrise/pytest.yml?branch=master" alt="GitHub Workflow Status"/>
  <img src="https://codecov.io/gh/geniusrise/geniusrise/branch/main/graph/badge.svg?token=0b359b3a-f29c-4966-9661-a79386b3450d" alt="Codecov"/>
  <img src="https://img.shields.io/github/license/geniusrise/geniusrise" alt="Codecov"/>
  <img src="https://img.shields.io/github/issues/geniusrise/geniusrise" alt="Codecov"/>
</p>

---

## <span style="color:#e667aa">About</span>

<span style="color:#e4e48c">Geniusrise</span> is a modular, loosely-coupled
AgentOps / MLOps framework designed for the era of Large Language Models,
offering flexibility, inclusivity, and standardization in designing networks of
AI agents.

It seamlessly integrates tasks, state management, data handling, and model
versioning, all while supporting diverse infrastructures and user expertise
levels. With its plug-and-play architecture,
<span style="color:#e4e48c">Geniusrise</span> empowers teams to build, share,
and deploy AI agent workflows across various platforms efficiently.

## <span style="color:#e667aa">TLDR 🙄</span>

### 1. Install geniusrise

```bash
pip install geniusrise
pip install geniusrise-huggingface
```

### 2. Create genius.yaml

```yaml
version: '1'
bolts:
  HuggingFaceInstructionTuningBolt:
    name: 'hf-fine-tune-my-shit'
    method: fine_tune
    args:
      model_name: bert-base-uncased
      tokenizer_name: bert-base-uncased
      batches: 2
      hf_repo_id: my/repo
      token: 'hf_woohoo'
      commit_message: say hello to genius!
    input:
      type: batch
      args:
        bucket: my-bucket
        folder: my-shit
    output:
      type: batch
      args:
        bucket: my-bucket
        folder: my-model
    deploy:
      type: 'k8s'
      args:
        cluster_name: my-cluster
        namespace: geniusrise-huggingface
        labels: { 'needs': 'gpu' }
        cpu: 16
        memory: 50G
        storage: 250Gb
        gpu: 1
```

### 3. Copy data to s3

```bash
cat > data.jsonl <<- EOM
{"instruction": "instruction1", "output":"output1"}
{"instruction": "instruction2", "output":"output2"}
EOM

aws s3 cp data.jsonl s3://my-bucket/my-shit/
```

### 4. Fine tune

```bash
genius --yaml genius.yaml deploy
```

🙄 This was not even crux of the iceberg. Please see docs.

## <span style="color:#e667aa">Links</span>

- **Website**: [geniusrise.ai](https://geniusrise.ai)
- **Docs**: [docs.geniusrise.ai](https://docs.geniusrise.ai)
- **Hub**: [geniusrise.com](https://geniusrise.com) [coming soon]
