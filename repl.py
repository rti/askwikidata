from askwikidata import AskWikidata

askwikidata = AskWikidata(retrieval_chunks=3)
askwikidata.setup()

while True:
    query = input("AskWikidata >> ")
    response = askwikidata.ask(query)
    print(response + "\n")
