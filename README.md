# AskWikidata

A Prototype for a Wikidata Question-Answering System

<p align="center"><img src="./image.jpg" alt="The askwikidata title image" style="width:400px;"/></p>

This system allows users to query Wikidata using natural language questions. The responses contain links to sources. If Wikidata does not provide the information requested, the system refuses to answer.

**The system is in an early proof of concept state.**

## Demo

<p align="center"><img src="./askwikidata.gif" alt="A short demo showing the askwikidata repl responding to a question."/></p>

## Quickstart

To give it a try, use ➡️  [this Google Colab Notebook](https://colab.research.google.com/drive/1yRZshpNj0kXwY0XuUYw5ziqjw_RffxH-) or load `AskWikidata_Quickstart.ipynb` in your infrastructure.

## Implementation

In order to answer questions based on Wikidata, the system uses retrieval augmented generation. First it transforms Wikidata items to text and generates embeddings for them. The user query is then embedded as well. Using nearest neighbor search, most relevant Wikidata items are identified. A reranker model selects only the best matches from the neighbors. Finally, these matches are incorporated into the LLM prompt in order to allow the LLM to generate using Wikidata knowledge.

All models, including the LLM can run on the local machine using `pytorch`. For nearest neighbor search, an `annoy` index is used.

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
pip install -r requirements.txt
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

### Answer a question
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
    "qa_model_url": "Qwen/Qwen2.5-3B-Instruct",
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
If you do not want to use a local LLM, AskWikidata can access LLM APIs by hosted on Huggingface. Configure your HF API key in the `HUGGINGFACE_API_KEY` environment variable.


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
