# AskWikidata

A Prototype for a Wikidata Question-Answering System

<p align="center"><img src="./image.jpg" alt="A cute wrap, the mascot of Nixwrap" style="width:400px;"/></p>

This system allows users to query Wikidata using natural language questions. The responses contain links to sources. If Wikidata does not provide the information requested, the system refuses to answer.

**The system is in an early proof of concept state.**

## Demo

<p align="center"><img src="./askwikidata.gif" alt="A short demo showing the askwikidata repl responding to a question."/></p>

## Quickstart

To give it a try, use ➡️  [this Google Colab Notebook](https://colab.research.google.com/drive/16GoXCVY1YyiEkuEqoXmgftl6X-68eHCi) or load `AskWikidata_Quickstart.ipynb` in your infrastructure.

## Implementation

This system integrates Large Language Models (LLMs) to respond to user questions. It converts Wikidata items into text format to ensure compatibility with the LLM. A retrieval-augmented generation (RAG) method is employed, where the user's question initiates a search for relevant "documents" within the Wikidata text item dataset. A reranker then evaluates these documents, prioritizing those most likely to address the question effectively. The chosen documents are then incorporated into the LLM's prompt, directing the model to formulate responses solely based on the provided information.

## Usage
### Install dependencies
#### Nix
On Nix the dev shell will install all required dependencies.
```sh
nix develop .
```

#### Pip
Alternatively, install python requirements using pip.
```sh
pip install -q langchain annoy sentence_transformers transformers touch pandas tqdm protobuf accelerate bitsandbytes safetensors sentencepiece
```

### Unpack provided caches
For faster execution, the results of some pre-computation steps are caches. In order to use those caches, unpack them:
```sh
bunzip2 --keep --force *.json.bz2
```

### Generate dataset
Generate text representations for Wikidata items. The list of items to use is currently hardcoded in `text_representation.py`.
```sh
python text_representation.py
```

### Answer an question
This python code will use AskWikidata to answer one question.
```python
from askwikidata import AskWikidata

config = {
    "chunk_size": 1280,
    "chunk_overlap": 0,
    "index_trees": 1024,
    "retrieval_chunks": 16,
    "context_chunks": 5,
    "embedding_model_name": "BAAI/bge-small-en-v1.5",
    "reranker_model_name": "BAAI/bge-reranker-base",
    "qa_model_url": "mistralai/Mistral-7B-Instruct-v0.1",
}

askwikidata = AskWikidata(**config)
askwikidata.setup()
print(askwikidata.ask("Who is the current mayor of Berlin? And since when is them serving?"))
```

### Interactive REPL
A simple interactive read eval print loop can be used to ask questions.
```sh
python repl.py
```

### Run evaluation
A script to evaluate the performance of different configurations is provided.
```sh
python eval.py
```

### Configure API Keys
If you do not want to use a local LLM, AskWikidata can access LLM APIs by hosted by Huggingface, runpod.io and OpenAI. Configure your API keys in the following environment variables:

Provider | Environment Variable Name | Note
--- | --- | ---
Hugging Face | `HUGGINGFACE_API_KEY` | active
runpod.io | `RUNPOD_API_KEY` | currently defunct
OpenAI | `OPENAI_API_KEY` | currently defunct

### Run tests
To execute the unit test suite, run:

```sh
$ python -m unittest
```

To get a coverage report, run
```sh
$ coverage run -m unittest
$ coverage report --omit="test_*,/nix/*" --show-missing
```
