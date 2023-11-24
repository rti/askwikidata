from askwikidata import AskWikidata
from typing import Callable
from pprint import pprint


def kai_wegner_date_correct(text):
    t = text.lower()
    return "27" in t and "2023" in t and ("4" in t or "april" in t)


# fmt: off
quiz = [
    # {"q": "What is Berlin?", "a": ["capital", "germany", "city"]},
    # {"q": "Mayor of Berlin", "a": "Kai Wegner"},
    # {"q": "mayor berlin", "a": "Kai Wegner"},
    # {"q": "Who is the current mayor of Berlin?", "a": "Kai Wegner"},
    # {"q": "since when is kay wegner mayor of berlin?", "a": kai_wegner_date_correct},
    # {"q": "Who was the mayor of Berlin in 2001?", "a": "Klaus Wowereit"},
    # {"q": "What is the population of Berlin?", "a": "3755251"},
    # {"q": "Can you name all twin cities of Berlin?", "a": [ "Los Angeles", "Paris", "Madrid", "Istanbul", "Warsaw", "Moscow", "City of Brussels", "Budapest", "Tashkent", "Mexico City", "Beijing", "Jakarta", "Tokyo", "Buenos Aires", "Prague", "Windhoek", "London", "Sofia", "Tehran", "Seville", "Copenhagen", "Kyiv", "Brasília", "Santo Domingo", "Algiers", "Rio de Janeiro", ], },
    # {"q": "Which River runs through Berlin?", "a": "Spree"},
    # {"q": "Who is the current mayor of Paris?", "a": "Anne Hidalgo"},
    # {"q": "What is the population of Paris?", "a": "2145906"},
    # {"q": "Can you name all twin cities of Paris?", "a": [ "Rome", "Tokyo", "Kyoto", "Berlin", "Ramallah", "Seoul", "Cairo", "Chicago", "Torreón", "San Francisco", "Kyiv", "Washington, D.C.", "Marrakesh", "Porto Alegre", "Dubai", "Beijing", "Mexico City", "Saint Petersburg", ], },
    # {"q": "Which River runs through Paris?", "a": "Seine"},
    # {"q": "Who is the current mayor of London?", "a": "Sadiq Khan"},
    # {"q": "What is the population of London?", "a": "8799728"},
    # {"q": "Can you name all twin cities of London?", "a": [ "Berlin", "Mumbai", "New York City", "Algiers", "Sofia", "Moscow", "Tokyo", "Beijing", "Karachi", "Zagreb", "Tehran", "Arequipa", "Delhi", "Bogotá", "Johannesburg", "Kuala Lumpur", "Oslo", "Sylhet", "Shanghai", "Baku", "Buenos Aires", "Istanbul", "Los Angeles", "Podgorica", "New Delhi", "Phnom Penh", "Jakarta", "Amsterdam", "Bucharest", "Santo Domingo", "La Paz", "Mexico City", ], },
    # {"q": "Which River runs through London?", "a": "River Thames"},
    # {"q": "Who is the current mayor of Prague?", "a": "Bohuslav Svoboda"},
    # {"q": "What is the population of Prague?", "a": "1357326"},
    {"q": "Can you name all twin cities of Prague?", "a": [ "Berlin", "Copenhagen", "Miami-Dade County", "Nuremberg", "Luxembourg", "Guangzhou", "Hamburg", "Helsinki", "Nîmes", "Prešov", "Rosh HaAyin", "Teramo", "Bamberg", "City of Brussels", "Frankfurt", "Jerusalem", "Moscow", "Saint Petersburg", "Chicago", "Taipei", "Terni", "Ferrara", "Trento", "Monza", "Lecce", "Naples", "Vilnius", "Istanbul", "Sofia", "Buenos Aires", "Athens", "Bratislava", "Madrid", "Tunis", "Brussels metropolitan area", "Amsterdam", "Phoenix", "Tirana", "Kyoto", "Cali", "Drancy", "Beijing", "Shanghai", "Tbilisi", ], },
    {"q": "Can you name all twinned administrative bodies of Prague?", "a": [ "Berlin", "Copenhagen", "Miami-Dade County", "Nuremberg", "Luxembourg", "Guangzhou", "Hamburg", "Helsinki", "Nîmes", "Prešov", "Rosh HaAyin", "Teramo", "Bamberg", "City of Brussels", "Frankfurt", "Jerusalem", "Moscow", "Saint Petersburg", "Chicago", "Taipei", "Terni", "Ferrara", "Trento", "Monza", "Lecce", "Naples", "Vilnius", "Istanbul", "Sofia", "Buenos Aires", "Athens", "Bratislava", "Madrid", "Tunis", "Brussels metropolitan area", "Amsterdam", "Phoenix", "Tirana", "Kyoto", "Cali", "Drancy", "Beijing", "Shanghai", "Tbilisi", ], },
    # {"q": "Which River runs through Prague?", "a": "Vltava"},
    # {"q": "What is the capital of Hawaii?", "a": "Honolulu"},
]
# fmt: off

hyperparameters = [
    # {
    #     "chunk_size": 768,
    #     "chunk_overlap": 0,
    #     "index_trees": 10,
    #     "retrieval_chunks": 64,
    #     "context_chunks": 7,
    #     "embedding_model_name": "BAAI/bge-small-en-v1.5",
    #     "reranker_model_name": "BAAI/bge-reranker-base",
    #     "qa_model_name": "mistral-7b-instruct-v0.1",
    #     "cache_file": "bge-small-cache.json",
    # },
    # {
    #     "chunk_size": 768,
    #     "chunk_overlap": 0,
    #     "index_trees": 10,
    #     "retrieval_chunks": 24,
    #     "context_chunks": 5,
    #     "embedding_model_name": "BAAI/bge-small-en-v1.5",
    #     "reranker_model_name": "BAAI/bge-reranker-base",
    #     "qa_model_name": "mistral-7b-instruct-v0.1",
    #     "cache_file": "bge-small-cache.json",
    # },
    {
        "chunk_size": 768,
        "chunk_overlap": 0,
        "index_trees": 10,
        "retrieval_chunks": 48,
        "context_chunks": 5,
        "embedding_model_name": "BAAI/bge-small-en-v1.5",
        "reranker_model_name": "BAAI/bge-reranker-base",
        "qa_model_name": "mistral-7b-instruct-v0.1",
        "cache_file": "bge-small-cache.json",
    },
    # {
    #     "chunk_size": 768,
    #     "chunk_overlap": 0,
    #     "index_trees": 10,
    #     "retrieval_chunks": 48,
    #     "context_chunks": 5,
    #     "embedding_model_name": "BAAI/bge-small-en-v1.5",
    #     "reranker_model_name": "BAAI/bge-reranker-large",
    #     "qa_model_name": "mistral-7b-instruct-v0.1",
    #     "cache_file": "bge-small-cache.json",
    # },
]

for hyperparameter in hyperparameters:
    print("⚙ Hyperparams")
    pprint(hyperparameter)

    askwikidata = AskWikidata(
        chunk_size=hyperparameter["chunk_size"],
        chunk_overlap=hyperparameter["chunk_overlap"],
        embedding_model_name=hyperparameter["embedding_model_name"],
        reranker_model_name=hyperparameter["reranker_model_name"],
        index_trees=hyperparameter["index_trees"],
        retrieval_chunks=hyperparameter["retrieval_chunks"],
        context_chunks=hyperparameter["context_chunks"],
    )
    askwikidata.setup()
    # askwikidata.print_data()

    correct_retrieved_contexts = 0
    correct_reranked_contexts = 0
    correct_answers = 0
    failed_retrieve = []
    failed_rerank = []
    failed_answer = []

    for i, q in enumerate(quiz):
        question = q["q"]
        expected_answer = q["a"]

        if isinstance(expected_answer, str):
            expected_answer = expected_answer.lower()
        if isinstance(expected_answer, list):
            expected_answer = [answer_part.lower() for answer_part in expected_answer]

        print("Question:", question)
        print("Expected answer:", expected_answer)

        retrieved = askwikidata.retrieve(question)
        retrieved_context = askwikidata.context(retrieved)
        retrieved_context_lower = retrieved_context.lower()

        if (
            (
                isinstance(expected_answer, str)
                and expected_answer in retrieved_context_lower
            )
            or (
                isinstance(expected_answer, list)
                and all(
                    (answer_part) in retrieved_context_lower
                    for answer_part in expected_answer
                )
            )
            or (
                isinstance(expected_answer, Callable)
                and expected_answer(retrieved_context_lower) == True
            )
        ):
            correct_retrieved_contexts += 1
            print("✅ Retieved Context")
        else:
            print("‼️ WRONG Retrieved Context")
            failed_retrieve.append(question)
            # print(retrieved_context)

        reranked, rerank_time = askwikidata.rerank(question, retrieved)
        print(f"  {int(rerank_time)} seconds.")
        reranked_context = askwikidata.context(reranked)
        reranked_context_lower = reranked_context.lower()

        if (
            (
                isinstance(expected_answer, str)
                and expected_answer in reranked_context_lower
            )
            or (
                isinstance(expected_answer, list)
                and all(
                    (answer_part) in reranked_context_lower
                    for answer_part in expected_answer
                )
            )
            or (
                isinstance(expected_answer, Callable)
                and expected_answer(reranked_context_lower) == True
            )
        ):
            correct_reranked_contexts += 1
            print("✅ Reranked Context")
        else:
            print("‼️ WRONG Reranked Context")
            failed_rerank.append(question)
            # print(retrieved_context)

        # if (isinstance(expected_answer, str) and expected_answer in answer_lower) or (
        #     isinstance(expected_answer, list)
        #     and all((answer_part) in answer_lower for answer_part in expected_answer)
        #     or isinstance(expected_answer, Callable)
        #     and expected_answer(answer_lower) == True
        # ):
        #     correct_answer += 1
        #     print(f"correct answer '{answer}' ({correct_answer} of {len(quiz)})")
        # else:
        #     print(f"### wrong answer '{answer}'")
        #     print("###")

        print("")

    print("*************\n"
          "🔍 Results 🔎\n")

    pprint(hyperparameter)
    print(f"Retrieved Contexts: {correct_retrieved_contexts} of {len(quiz)}")
    print(f"Reranked Contexts: {correct_reranked_contexts} of {len(quiz)}")
    print(f"Correct Answers: {correct_answers} of {len(quiz)}")
    if len(failed_retrieve): print(f"Failed Retrieve for questions:") 
    for q in failed_retrieve: print(" ", q)
    if len(failed_rerank): print(f"Failed Rerank for questions:") 
    for q in failed_rerank: print(" ", q)
    print("*************\n")
