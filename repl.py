from askwikidata import AskWikidata

hyperparams = {
    "chunk_size": 1280,
    "chunk_overlap": 0,
    "index_trees": 1024,
    "retrieval_chunks": 16,
    "context_chunks": 5,
    "embedding_model_name": "BAAI/bge-small-en-v1.5",
    "reranker_model_name": "BAAI/bge-reranker-base",
    "qa_model_url": "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.1",
}

askwikidata = AskWikidata(**hyperparams)
askwikidata.setup()

while True:
    query = input("AskWikidata >> ")
    response = askwikidata.ask(query)
    print(response + "\n")
