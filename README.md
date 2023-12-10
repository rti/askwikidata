# AskWikidata

A Prototype for a Wikidata Question-Answering System

<p align="center"><img src="./image.jpg" alt="A cute wrap, the mascot of Nixwrap" style="width:400px;"/></p>

This system allows users to query Wikidata using natural language questions. The responses contain links to sources. If Wikidata does not provide the information requested, the system refuses to answer.

**The system is in an early proof of concept state.**

## Quickstart

To give it a try, use ➡️  [this Google Colab Notebook](https://colab.research.google.com/drive/16GoXCVY1YyiEkuEqoXmgftl6X-68eHCi).

**You will need a Huggingface Pro API Key to query the LLM**.

## Implementation

This system integrates Large Language Models (LLMs) to respond to user questions. It converts Wikidata items into text format to ensure compatibility with the LLM. A retrieval-augmented generation (RAG) method is employed, where the user's question initiates a search for relevant "documents" within the Wikidata text item dataset. A reranker then evaluates these documents, prioritizing those most likely to address the question effectively. The chosen documents are then incorporated into the LLM's prompt, directing the model to formulate responses solely based on the provided information.

## Install dependencies
### Nix
On Nix the dev shell will install all required dependencies.
```sh
nix develop .
```

### Pip
Alternatively, install python requirements using pip.
```sh
pip install langchain annoy openai sentence_transformers touch pandas tqdm protobuf
```

## Usage
### Unpack provided caches
For faster execution, the results of some pre-computation steps are caches. In order to use those caches, unpack them:
```sh
bunzip2 --keep --force *.json.bz2
```

### Configure API Keys
AskWikidata requires access to LLM APIs. Configure your API keys in the following environment variables:

Provider | Environment Variable Name | Note
--- | --- | ---
Hugging Face | `HUGGINGFACE_API_KEY` | active
runpod.io | `RUNPOD_API_KEY` | currently disabled
OpenAI | `OPENAI_API_KEY` | currently disabled

### Generate dataset
Generate text representations for Wikidata items. The list of items to use is currently hardcoded in `text_representation.py`.
```sh
python text_representation.py
```

### Interactive REPL
A simple interactive read eval print loop can we used to ask questions.
```sh
python repl.py
```

### Run evaluation
A script to evaluate the performance of different configurations is provided.
```sh
python eval.py
```

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

