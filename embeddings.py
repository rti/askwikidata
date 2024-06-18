from __future__ import annotations

import sentence_transformers
from torch import Tensor, cuda
from typing import List
import numpy


MODEL_NAME = "paraphrase-MiniLM-L6-v2"
MODEL_PREFIX_DOCUMENT = ""
MODEL_PREFIX_QUERY = ""

_model: sentence_transformers.SentenceTransformer | None = None

def get_model() -> sentence_transformers.SentenceTransformer:
    global _model
    if not _model:
        device = "cpu"
        if cuda.is_available():
            print("CUDA available to torch.")
            device = "cuda"
        else:
            print("torch uses CPU.")

        print("Initializing model...")
        _model = sentence_transformers.SentenceTransformer(MODEL_NAME, device=device)
    return _model


def embed_docs(documents: List[str]) -> numpy.ndarray:
    model = get_model()
    prefixed_documents = [f"{MODEL_PREFIX_DOCUMENT}{s}" for s in documents]
    # print(f"{len(prefixed_documents)=}")
    embeddings = model.encode(prefixed_documents)
    if isinstance(embeddings, numpy.ndarray):
        embeddings = embeddings
    else:
        raise Exception("Unexpected return type.")
    return embeddings


def embed_query(query: str) -> numpy.ndarray:
    model = get_model()
    prefixed_string = f"{MODEL_PREFIX_DOCUMENT}{query}"
    embeddings = model.encode(prefixed_string)
    if isinstance(embeddings, numpy.ndarray):
        embeddings = embeddings
    else:
        raise Exception("Unexpected return type.")
    return embeddings


if __name__ == "__main__":
    print("Testing sentence transformer embedding")

    assert get_model() == get_model(), "Singleton pattern violation."
    assert get_model() is not None, "Model was not created."
    #
    assert embed_query("test query") is not None, "Embeddings were not generated."
    assert embed_query("test query").shape == (384, ), "384 dimension embedding expected."

    assert embed_docs(["test 1", "test2"]) is not None, "Embeddings were not generated."
    assert embed_docs(["test 1", "test2"]).shape == (2,384) , "384 dimension embedding expected."

    print("OK")
