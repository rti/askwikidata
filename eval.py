from askwikidata import AskWikidata
from typing import Callable, List, Dict, Optional
from dataclasses import dataclass, field, asdict
from pprint import pprint
import json
import datetime


def kai_wegner_date_correct(text: str):
    t = text.lower()
    return "27" in t and "2023" in t and ("4" in t or "april" in t)


def correct(answer: str, expected: str | list | Callable) -> bool:
    answer_lower = answer.lower()
    expected_lower = None
    if isinstance(expected, str):
        expected_lower = expected.lower()
    if isinstance(expected, list):
        expected_lower = [answer_part.lower() for answer_part in expected]

    return (
        (isinstance(expected_lower, str) and expected_lower in answer_lower)
        or (
            isinstance(expected_lower, list)
            and all((answer_part) in answer_lower for answer_part in expected_lower)
        )
        or (isinstance(expected, Callable) and expected(answer_lower) == True)
    )


# fmt: off
quiz = [
    {"q": "What is Berlin?", "a": ["capital", "germany", "city"]},
    {"q": "Mayor of Berlin", "a": "Kai Wegner"},
    {"q": "mayor berlin", "a": "Kai Wegner"},
    {"q": "Who is the current mayor of Berlin?", "a": "Kai Wegner"},
    {"q": "since when is kay wegner mayor of berlin?", "a": kai_wegner_date_correct},
    {"q": "Who was the mayor of Berlin in 2001?", "a": "Klaus Wowereit"},
    {"q": "What is the population of Berlin?", "a": "3755251"},
    {"q": "Can you name all twin cities of Berlin?", "a": [ "Los Angeles", "Paris", "Madrid", "Istanbul", "Warsaw", "Moscow", "City of Brussels", "Budapest", "Tashkent", "Mexico City", "Beijing", "Jakarta", "Tokyo", "Buenos Aires", "Prague", "Windhoek", "London", "Sofia", "Tehran", "Seville", "Copenhagen", "Kyiv", "Brasília", "Santo Domingo", "Algiers", "Rio de Janeiro", ], },
    {"q": "Which River runs through Berlin?", "a": "Spree"},
    {"q": "Who is the current mayor of Paris?", "a": "Anne Hidalgo"},
    {"q": "What is the population of Paris?", "a": "2145906"},
    {"q": "Can you name all twin cities of Paris?", "a": [ "Rome", "Tokyo", "Kyoto", "Berlin", "Ramallah", "Seoul", "Cairo", "Chicago", "Torreón", "San Francisco", "Kyiv", "Washington, D.C.", "Marrakesh", "Porto Alegre", "Dubai", "Beijing", "Mexico City", "Saint Petersburg", ], },
    {"q": "Which River runs through Paris?", "a": "Seine"},
    {"q": "Who is the current mayor of London?", "a": "Sadiq Khan"},
    {"q": "What is the population of London?", "a": "8799728"},
    {"q": "Can you name all twin cities of London?", "a": [ "Berlin", "Mumbai", "New York City", "Algiers", "Sofia", "Moscow", "Tokyo", "Beijing", "Karachi", "Zagreb", "Tehran", "Arequipa", "Delhi", "Bogotá", "Johannesburg", "Kuala Lumpur", "Oslo", "Sylhet", "Shanghai", "Baku", "Buenos Aires", "Istanbul", "Los Angeles", "Podgorica", "New Delhi", "Phnom Penh", "Jakarta", "Amsterdam", "Bucharest", "Santo Domingo", "La Paz", "Mexico City", ], },
    {"q": "Which River runs through London?", "a": "River Thames"},
    {"q": "Who is the current mayor of Prague?", "a": "Bohuslav Svoboda"},
    {"q": "What is the population of Prague?", "a": "1357326"},
    {"q": "Can you name all twin cities of Prague?", "a": [ "Berlin", "Copenhagen", "Miami-Dade County", "Nuremberg", "Luxembourg", "Guangzhou", "Hamburg", "Helsinki", "Nîmes", "Prešov", "Rosh HaAyin", "Teramo", "Bamberg", "City of Brussels", "Frankfurt", "Jerusalem", "Moscow", "Saint Petersburg", "Chicago", "Taipei", "Terni", "Ferrara", "Trento", "Monza", "Lecce", "Naples", "Vilnius", "Istanbul", "Sofia", "Buenos Aires", "Athens", "Bratislava", "Madrid", "Tunis", "Brussels metropolitan area", "Amsterdam", "Phoenix", "Tirana", "Kyoto", "Cali", "Drancy", "Beijing", "Shanghai", "Tbilisi", ], },
    {"q": "Can you name all twinned administrative bodies of Prague?", "a": [ "Berlin", "Copenhagen", "Miami-Dade County", "Nuremberg", "Luxembourg", "Guangzhou", "Hamburg", "Helsinki", "Nîmes", "Prešov", "Rosh HaAyin", "Teramo", "Bamberg", "City of Brussels", "Frankfurt", "Jerusalem", "Moscow", "Saint Petersburg", "Chicago", "Taipei", "Terni", "Ferrara", "Trento", "Monza", "Lecce", "Naples", "Vilnius", "Istanbul", "Sofia", "Buenos Aires", "Athens", "Bratislava", "Madrid", "Tunis", "Brussels metropolitan area", "Amsterdam", "Phoenix", "Tirana", "Kyoto", "Cali", "Drancy", "Beijing", "Shanghai", "Tbilisi", ], },
    {"q": "Which River runs through Prague?", "a": "Vltava"},
    {"q": "What is the elevation of Bobo-Dioulasso?", "a": "445"},
]
# fmt: on

configurations = [
    {
        "chunk_size": 1280,
        "chunk_overlap": 0,
        "index_trees": 10,
        "retrieval_chunks": 16,
        "context_chunks": 5,
        "embedding_model_name": "BAAI/bge-small-en-v1.5",
        # "embedding_model_name": "BAAI/bge-base-en-v1.5",
        # "embedding_model_name": "BAAI/bge-large-en-v1.5",
        "reranker_model_name": "BAAI/bge-reranker-base",
        # "reranker_model_name": "BAAI/bge-reranker-large",
        # "qa_model_url": "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.1",
        "qa_model_url": "https://api-inference.huggingface.co/models/meta-llama/Llama-2-7b-chat-hf",
    },
    {
        "chunk_size": 1280,
        "chunk_overlap": 0,
        "index_trees": 10,
        "retrieval_chunks": 16,
        "context_chunks": 5,
        # "embedding_model_name": "BAAI/bge-small-en-v1.5",
        "embedding_model_name": "BAAI/bge-base-en-v1.5",
        # "embedding_model_name": "BAAI/bge-large-en-v1.5",
        "reranker_model_name": "BAAI/bge-reranker-base",
        # "reranker_model_name": "BAAI/bge-reranker-large",
        # "qa_model_url": "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.1",
        "qa_model_url": "https://api-inference.huggingface.co/models/meta-llama/Llama-2-7b-chat-hf",
    },
    {
        "chunk_size": 1280,
        "chunk_overlap": 0,
        "index_trees": 10,
        "retrieval_chunks": 16,
        "context_chunks": 5,
        # "embedding_model_name": "BAAI/bge-small-en-v1.5",
        # "embedding_model_name": "BAAI/bge-base-en-v1.5",
        "embedding_model_name": "BAAI/bge-large-en-v1.5",
        "reranker_model_name": "BAAI/bge-reranker-base",
        # "reranker_model_name": "BAAI/bge-reranker-large",
        # "qa_model_url": "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.1",
        "qa_model_url": "https://api-inference.huggingface.co/models/meta-llama/Llama-2-7b-chat-hf",
    }
]


@dataclass
class QERCA:
    question: str
    expected_answer: str | List[str]
    retrieved_context: str
    reranked_context: Optional[str] = None
    answer: Optional[str] = None


@dataclass
class EvalResult:
    config: Dict[str, str | int]
    total_chunks: int
    total_questions: int
    correct_retrievals: int = 0
    correct_reranks: int = 0
    correct_answers: int = 0
    correct_answers_plain: int = 0
    failed_retrieval_questions: List[QERCA] = field(default_factory=list)
    failed_rerank_questions: List[QERCA] = field(default_factory=list)
    failed_answer_questions: List[QERCA] = field(default_factory=list)
    datatime: str = datetime.datetime.now().isoformat()


eval_results: List[EvalResult] = []

for config in configurations:
    pprint(config)

    askwikidata = AskWikidata(**config)
    askwikidata.setup()
    # askwikidata.print_data()

    eval_result = EvalResult(
        config, total_questions=len(quiz), total_chunks=len(askwikidata.df)
    )
    eval_results.append(eval_result)

    for i, q in enumerate(quiz):
        question = q["q"]
        expected_answer = q["a"]

        print("")
        print("Question:", question)
        print("Expected answer:", expected_answer)

        answer_plain = askwikidata.llm_generate_plain(question)
        if correct(answer_plain, expected_answer):
            eval_result.correct_answers_plain += 1
            print("🙈 Plain Answer correct:", answer_plain)
        else:
            print("👍 Plain Answer wrong:", answer_plain)

        retrieved = askwikidata.retrieve(question)
        retrieved_context = askwikidata.context(retrieved)
        retrieved_context_lower = retrieved_context.lower()

        if correct(retrieved_context, expected_answer):
            eval_result.correct_retrievals += 1
            print("✅ Retrieved Context")
        else:
            print("‼️ WRONG Retrieved Context")
            eval_result.failed_retrieval_questions.append(
                QERCA(question, expected_answer, retrieved_context)
            )
            continue

        reranked, rerank_time = askwikidata.rerank(question, retrieved)
        print(f"  {int(rerank_time)} seconds.")
        reranked_context = askwikidata.context(reranked)

        if correct(reranked_context, expected_answer):
            eval_result.correct_reranks += 1
            print("✅ Reranked Context")
        else:
            print("‼️ WRONG Reranked Context")
            eval_result.failed_rerank_questions.append(
                QERCA(question, expected_answer, retrieved_context, reranked_context)
            )
            continue

        answer = askwikidata.llm_generate(question, reranked)

        if correct(answer, expected_answer):
            eval_result.correct_answers += 1
            print("✅ Answer:", answer)
        else:
            print("‼️ WRONG Answer:", answer)
            eval_result.failed_answer_questions
            eval_result.failed_answer_questions.append(
                QERCA(
                    question,
                    expected_answer,
                    retrieved_context,
                    reranked_context,
                    answer,
                )
            )


for eval_result in eval_results:
    print("")
    print("***************************************")
    print("          🔍 Results 🔎\n")
    print("\n")
    pprint(eval_result.config)
    print("\n")
    pprint(eval_result, width=120, depth=1)
    print("\n")
    print("***************************************")
    print("\n")


with open(f"eval_resuls.json", "a") as file:
    for eval_result in eval_results:
        file.write(json.dumps(asdict(eval_result)))
