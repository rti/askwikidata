from askwikidata import AskWikidata

askwikidata = AskWikidata()
askwikidata.create_chunk_embeddings()
askwikidata.create_index()

while True:
    query = input("AskWikidata >> ")
    response = askwikidata.ask(query)
    print(response + "\n")
