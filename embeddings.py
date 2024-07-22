from __future__ import annotations
from typing import List

import sentence_transformers
from torch import cuda
import numpy


MODEL_NAME = "paraphrase-MiniLM-L6-v2"
MODEL_PREFIX_DOCUMENT = ""
MODEL_PREFIX_QUERY = ""
# TRY_GPU = True
TRY_GPU = False

_model: sentence_transformers.SentenceTransformer | None = None


def get_model() -> sentence_transformers.SentenceTransformer:
    global _model
    if not _model:
        device = "cpu"
        if TRY_GPU and cuda.is_available():
            print("CUDA available to torch.")
            device = "cuda"
        else:
            print("torch uses CPU.")

        print("Initializing model...")
        _model = sentence_transformers.SentenceTransformer(
            MODEL_NAME,
            prompts={"query": MODEL_PREFIX_QUERY, "document": MODEL_PREFIX_DOCUMENT},
            device=device,
        )
    return _model


def embed_docs(documents: List[str], batch_size=32) -> numpy.ndarray:
    model = get_model()
    embeddings = model.encode(documents, prompt_name="document", batch_size=batch_size)
    if isinstance(embeddings, numpy.ndarray):
        embeddings = embeddings
    else:
        raise Exception("Unexpected return type.")
    return embeddings


def embed_query(query: str) -> numpy.ndarray:
    model = get_model()
    embeddings = model.encode(query, prompt_name="query")
    if isinstance(embeddings, numpy.ndarray):
        embeddings = embeddings
    else:
        raise Exception("Unexpected return type.")
    return embeddings


# ################################################################
# TESTS

import random

if __name__ == "__main__":
    print("Smoke Testing")

    assert get_model() == get_model(), "Singleton pattern violation."
    assert get_model() is not None, "Model was not created."

    assert embed_query("test query") is not None, "Embeddings were not generated."
    assert embed_query("test query").shape == (
        384,
    ), "384 dimension embedding expected."

    assert embed_docs(["test 1", "test2"]) is not None, "Embeddings were not generated."
    assert embed_docs(["test 1", "test2"]).shape == (
        2,
        384,
    ), "384 dimension embedding expected."

    print("OK")

    print("Performance Testing")
    import time

    start = time.time()
    documents = []

    # array with common words
    words = [
        "the",
        "be",
        "to",
        "of",
        "and",
        "a",
        "in",
        "that",
        "have",
        "I",
        "it",
        "for",
        "not",
        "on",
        "with",
        "he",
        "as",
        "you",
        "do",
        "at",
        "this",
        "but",
        "his",
        "by",
        "from",
        "they",
        "we",
        "say",
        "her",
        "she",
        "or",
        "an",
        "will",
        "my",
        "one",
        "all",
        "would",
        "there",
        "their",
        "what",
        "so",
        "up",
        "out",
        "if",
        "about",
        "who",
        "get",
        "which",
        "go",
        "me",
        "when",
        "make",
        "can",
        "like",
        "time",
        "no",
        "just",
        "him",
        "know",
        "take",
        "people",
        "into",
        "year",
        "your",
        "apple",
        "banana",
        "cherry",
        "date",
        "fig",
        "grape",
        "kiwi",
        "lemon",
        "mango",
        "orange",
        "papaya",
        "peach",
        "pear",
        "pineapple",
        "plum",
        "raspberry",
        "strawberry",
        "watermelon",
        "apricot",
        "avocado",
        "blueberry",
        "coconut",
        "cranberry",
        "currant",
        "dragonfruit",
        "durian",
        "elderberry",
        "gooseberry",
        "guava",
        "honeydew",
        "jackfruit",
        "kumquat",
        "lime",
        "lychee",
        "mandarin",
        "nectarine",
        "olive",
        "passionfruit",
        "pear",
        "pomegranate",
        "quince",
        "raisin",
        "tamarind",
        "tangerine",
        "tomato",
        "ugli",
        "watercress",
        "yuzu",
        "acai",
        "apricot",
        "banana",
    ]
    examples = [
        "Sint Geertruid: village in Eijsden-Margraten, Netherlands. Sint Geertruid Commons category Sint Geertruid. ",
        "Sint Geertruid: village in Eijsden-Margraten, Netherlands. Sint Geertruid country Netherlands. Netherlands: country in Northwestern Europe with territories in the Caribbean. ",
        "Sint Geertruid: village in Eijsden-Margraten, Netherlands. Sint Geertruid instance of village. village: small clustered human settlement smaller than a town. ",
        "Sint Geertruid: village in Eijsden-Margraten, Netherlands. Sint Geertruid instance of cadastral populated place in the Netherlands. cadastral populated place in the Netherlands: officially designated place (woonplaats) (city/town/village) in the Netherlands. ",
        "Sint Geertruid: village in Eijsden-Margraten, Netherlands. Sint Geertruid located in the administrative territorial entity Eijsden-Margraten. Eijsden-Margraten: municipality in the Netherlands. ",
        "Sint Geertruid: village in Eijsden-Margraten, Netherlands. Sint Geertruid located in the administrative territorial entity Margraten. Margraten: former municipality in Limburg, the Netherlands. ",
        "Sint Geertruid: village in Eijsden-Margraten, Netherlands. Sint Geertruid located in the administrative territorial entity Sint Geertruid. Sint Geertruid: former municipality in Limburg, the Netherlands. ",
        "Sint Geertruid: village in Eijsden-Margraten, Netherlands. Sint Geertruid list of monuments Rijksmonumenten in Sint Geertruid. Rijksmonumenten in Sint Geertruid: Wikimedia list article. ",
        "Sint Geertruid: village in Eijsden-Margraten, Netherlands. Sint Geertruid located in time zone UTC+01:00. UTC+01:00: identifier for a time offset from UTC of +1. ",
        "Sint Geertruid: village in Eijsden-Margraten, Netherlands. Sint Geertruid located in/on physical feature Plateau of Margraten. Plateau of Margraten: plateau in the Netherlands and Belgium. ",
    ]

    # doc_counts = [16384, 32768, 65536, 131072, 262144]
    doc_counts = [65536]
    # doc_lengths = [8, 16, 32, 64, 128, 256, 512]
    # doc_lengths = [32]
    doc_lengths = [16]
    batch_sizes = [32, 64, 128, 256, 512, 2048, 4096]

    for batch_size in batch_sizes:
        for doc_count in doc_counts:
            for doc_length in doc_lengths:
                documents = []
                for i in range(0, doc_count):
                    document = " ".join(
                        [
                            words[random.randint(0, len(words) - 1)]
                            for _ in range(random.randint(doc_length, doc_length * 2))
                        ]
                    )
                    # document = examples[i % len(examples)]
                    documents.append(document)

                start = time.time()
                embed_docs(documents, batch_size=batch_size)
                end = time.time()
                print(
                    f"Embed {len(documents)} Documents of {doc_length}-{doc_length * 2} words each with batch size {batch_size} in {(end - start):.2f}s ({doc_count / ((end - start) * 1000):.2f}) docs/ms."
                )

    print("DONE")
