<h1 align="center">
  <img src="./assets/logo_with_text.png" alt="Grace Hopper" width="900"/>
</h1>
<h2 align="center">
  <a style="color:#f34960" href="https://docs.geniusrise.ai">Documentation</a>
</h2>

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
and deploy AI agent workflows across various platforms.

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
  http_classifier:
    name: HuggingFaceClassificationFineTuner
    method: fine_tune
    args:
      model_name: bert-base-uncased
      tokenizer_name: bert-base-uncased
      num_train_epochs: 2
      per_device_train_batch_size: 2
      model_class: BertForSequenceClassification
      tokenizer_class: BertTokenizer
      data_masked: true
      hf_repo_id: your/hf_model_repo
      hf_commit_message: 'say hello to geniusrise!'
      hf_create_pr: true
      hf_token: hf_mykey
    state:
      type: none
    input:
      type: batch
      args:
        bucket: my-s3-bucket
        folder: training_data
    output:
      type: batch
      args:
        bucket: my-s3-bucket
        folder: model
    deploy:
      type: k8s
      args:
        kind: deployment
        name: classifier
        context_name: arn:aws:eks:us-east-1:143601010266:cluster/geniusrise-dev
        namespace: geniusrise
        image: geniusrise/geniusrise
        kube_config_path: ~/.kube/config
        cpu: 16
        memory: 50G
        storage: 250Gb
        gpu: 1
```

### 3. Deploy

```bash
genius rise up
```

🙄 This was not even tip of the iceberg. Please see docs.

## <span style="color:#e667aa">Links</span>

- **Website**: [geniusrise.ai](https://geniusrise.ai)
- **Docs**: [docs.geniusrise.ai](https://docs.geniusrise.ai)
- **Hub**: [geniusrise.com](https://geniusrise.com) [coming soon]
