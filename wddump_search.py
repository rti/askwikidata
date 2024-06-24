import postgres
import embeddings
import time

query = "Capital of Belgium"

if __name__ == "__main__":
    while True:
        print(f"Searching {query}")

        start = time.time()
        embs = embeddings.embed_query(query)
        print(f"embedding took {time.time() - start:.2f}s")
        start = time.time()
        res = postgres.get_similar_chunks_with_distance(embs, limit=5, threshold=30)
        print(f"searching took {time.time() - start:.2f}s")

        if len(res) == 0:
            print("no results, showing 5 nearest")
            res = postgres.get_similar_chunks_with_distance(embs, limit=5, threshold=100)

        for r in res:
            chunk = r[0]
            distance = r[1]
            print(f"{chunk.text} {distance:.2f}")

        query = input("\n\nAskWikidata >> ")
