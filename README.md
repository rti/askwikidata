# AskWikidata

Wikidata Question-Answering System


<p align="center"><img src="./image.jpg" alt="A cute wrap, the mascot of Nixwrap" style="width:400px;"/></p>

This project aims to allow users to ask questions naturally and have the system retrieve relevant information from Wikidata to construct a response while also providing sources to the information. It employs a retrieval-augmented generation approach where the system first fetches data points from Wikidata and then weaves them into the context of a large language model response. 

**The project is in an early proof of concept state.**

## Configuration
`askwikidata.py` requires access to LLM APIs. Configure your API keys in the following environment variables:

Provider | Environment Variable Name |
--- | --- |
Hugging Face | `HUGGINGFACE_API_KEY` |
runpod.io | `RUNPOD_API_KEY` |
OpenAI | `OPENAI_API_KEY` |

## Setup
### Nix
On nix the dev shell will install all required dependencies.
```sh
nix develop .
```

### Pip
Install python requirements using pip.
```sh
pip install langchain annoy openai sentence_transformers touch pandas tqdm protobuf
```

## Usage
### Unpack wikidata item/label cache
```sh
bunzip2 --keep wikidata_label_cache.json.bz2
bunzip2 --keep wikidata_item_cache.json.bz2
```

### Interactive repl
```sh
python repl.py
```

### Run evaluation
```sh
python eval.py
```

### Run tests
To execute the test suite, run:

```sh
$ python -m unittest
```

To get a coverage report, run
```sh
$ coverage run -m unittest
$ coverage report --omit="test_*,/nix/*" --show-missing
```

