# import pandas as pd
import glob
import json
import os
from langchain.text_splitter import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer  # , util

# from langchain.embeddings import OpenAIEmbeddings
# from langchain.embeddings.huggingface import HuggingFaceEmbeddings
from annoy import AnnoyIndex

# import numpy as np
import requests
import json
# import time
import openai

HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")
RUNPOD_API_KEY = os.getenv("RUNPOD_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

chunk_embeddings_cache_file_path = "chunk_embeddings_cache.json"

# embedding_model_name ="all-MiniLM-L6-v2"
embedding_model_name ="BAAI/bge-base-en-v1.5"
# embedding_model_name ="BAAI/bge-large-en-v1.5"
# embedding_model_name ="BAAI/bge-small-en-v1.5"
# embedding_model_name = "paraphrase-MiniLM-L12-v2"
# embedding_model_name = "paraphrase-MiniLM-L12-v2"
# embedding_model_name = "paraphrase-MiniLM-L6-v2"

embeddings_model = SentenceTransformer(embedding_model_name)


def create_chunk_embeddings():
    # data loading
    texts = []
    metas = []
    directory_path = "./text_representations"

    for file_path in glob.glob(os.path.join(directory_path, "*.txt")):
        with open(file_path, "r") as file:
            texts.append(file.read())
            file_name = file_path.split("/")[-1]
            q_id = file_name.split(".")[0]
            metas.append({"source": f"https://www.wikidata.org/wiki/{q_id}"})

    chunks = create_chunks(texts, metas)
    print(f"created {len(chunks)} chunks.")
    embeds = create_embeds(chunks)
    print(f"created {len(embeds)} embeds.")

    return chunks, embeds


# chunk_size = 1280
chunk_size = 768
# chunk_size = 512

def create_chunks(texts, metas):
    # text splitter
    chunk_overlap = 50
    text_splitter = RecursiveCharacterTextSplitter(
        separators=["\n\n", "\n", " ", ""],
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
    )
    chunks = text_splitter.create_documents(texts, metadatas=metas)
    # for c in chunks:
    #     if c.page_content.find("head of government") > 0:
    #         print(c)
    #
    # for c in chunks:
    #     if c.page_content.find("Diepgen") > 0:
    #         print(c)
    return chunks


def create_embeds(chunks):
    embeds = []
    # embeddings_model = OpenAIEmbeddings(
    #         model="text-ebedding-ada-002",
    #         openai_api_base=os.environ["OPENAI_API_BASE"],
    #         openai_api_key=os.environ["OPENAI_API_KEY"])
    # embeddings_model = HuggingFaceEmbeddings(
    #         model_name="BAAI/bge-small-en-v1.5", # the one jeremy used
    #         # model_kwargs={"device": "cuda"},
    #         # encode_kwargs={"device": "cuda", "batch_size": 100},
    #         )
    for t in chunks:
        embeds.append(embeddings_model.encode(t.page_content))  # sentence transformer
        # embeds.append(embeddings_model.embed_documents([t])) # langchain

    return embeds


# def save_chunk_embed_cache(chunks, embeddings):
#     chunks_json = []
#     for chunk in chunks:
#         chunk_json = chunks_json.append(chunk.dict())
#
#     embeds_json = []
#     for embedding in embeddings:
#         embedding_json = embeds_json.append(embedding.tolist())
#
#     chunk_embeds = {"chunks": chunks_json, "embeddings": embeds_json}
#     with open(chunk_embeddings_cache_file_path, "w") as cache_file:
#         json.dump(chunk_embeds, cache_file, indent=2)
#
#
# # TODO: Load chunks & embeddings from cache file if it exists
# if False and os.path.exists(chunk_embeddings_cache_file_path):
#     with open(chunk_embeddings_cache_file_path, "r") as cache_file:
#         cached_chunk_embeds = json.load(cache_file)
# else:
#     chunks, embeds = create_chunk_embeddings()
#     save_chunk_embed_cache(chunks, embeds)

chunks, embeds = create_chunk_embeddings()

# embeddings index
index_trees = 10
embed_dims = len(embeds[0])
print(f"embeddings have {embed_dims} dimensions.")
index = AnnoyIndex(embed_dims, "angular")
for i, e in enumerate(embeds):
    index.add_item(i, e)
index.build(index_trees)




# # context retrieval
# num_chunks = 3
# question = "Who is the current mayor of Berlin?"
# # question = "Who is the current head of government of Berlin?"
# # question = "Who is currently the mayor in Berlin?"
# # question = "Who is currently the mayor in Berlin?"
# question_embedding = embeddings_model.encode(question)
# question_embedding = [float(value) for value in question_embedding]
# nearest_ids = index.get_nns_by_vector(
#     question_embedding, num_chunks, include_distances=True
# )
# context = ""
# for n in zip(nearest_ids[0], nearest_ids[1]):
#     print("\n")
#     print(n)
#     print(chunks[n[0]].page_content)
#     context += chunks[n[0]].page_content + "\n"


def system_from_context(context):
    system = (
        "You are answering questions for a given context.\n"
        + "Answer based on information from the given context only.\n"
        + "If the answer is not in the context say that you do not know the answer.\n"
        + "Only give the answer, do not provide any further explanations.\n"
        + f"Your context is:\n{context}"
    )
    # system = (
    #     "You are answering questions.\n"
    #     + "If you do not have the answer say that you do not know.\n"
    #     + "Only give the answer, do not provide any further explanations.\n"
    # )
    return system


def llama_prompt(text, system="You are a helpful assistent."):
    return f"<s>[INST] <<SYS>>\n{system}\n<</SYS>>\n\n{text} [/INST]"


def ask_llama_runpod(question, context):
    # access LLM on runpod
    url = f"https://api.runpod.ai/v2/llama2-7b-chat/runsync"
    headers = {
        "Authorization": RUNPOD_API_KEY,
        "Content-Type": "application/json",
    }
    system = system_from_context(context)
    prompt = llama_prompt(question, system)
    # print(prompt)
    payload = {
        "input": {
            "prompt": prompt,
            "sampling_params": {
                "max_tokens": 1000,
                "n": 1,
                "presence_penalty": 0.2,
                "frequency_penalty": 0.7,
                "temperature": 0.0,
            },
        }
    }
    response = requests.post(url, headers=headers, json=payload)
    response_json = json.loads(response.text)
   # print(response_json)
    return response_json["output"]["text"][0]



# access LLM on openai
def ask_openai(question, context):
    openai.api_key = OPENAI_API_KEY
    # openai_model = "gpt-3.5-turbo"
    # openai_model = "gpt-4"
    openai_model = "gpt-4-1106-preview"
    system = system_from_context(context)
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": question},
    ]
    # print(messages)
    chat = openai.ChatCompletion.create(model=openai_model, messages=messages)
    # print(chat)
    reply = chat.choices[0].message.content
    return reply


# access mistral LLM on huggingface
def mistral_prompt(text, system="You are a helpful assistent."):
    return f"<s>[INST] {system}\n\n{text} [/INST]"


def ask_mistral(question, context):
    API_URL = (
        "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.1"
    )
    headers = {"Authorization": f"Bearer {HUGGINGFACE_API_KEY}"}
    system = system_from_context(context)
    prompt = mistral_prompt(question, system)
    print("Sending the following prompt to mistral:")
    print(prompt)
    # print(
    #     f"Sending {len(prompt)} characters prompt length, about {int(len(prompt)/3)} tokens."
    # )
    response = requests.post(
        API_URL,
        headers=headers,
        json={
            "inputs": prompt,
        },
    )
    # print(response.json())
    return response.json()[0]["generated_text"].replace(prompt, "").strip()


# context = "head of government also known as mayor, prime minister, premier, first minister, head of national government, chancellor, governor, government headed by, executive power headed by, president.\n\nBerlin is nice.\n\nBerlin is cool.\n\nBerlin head of government Susi"
# context = "Berlin is nice.\n\nBerlin is cool.\n\nBerlin head of government Susi"

# context = context.replace("Kai Wegner", "")

# print(context)

# print(f"Question: {question}")
# print("mistral: " + ask_mistral(question, context))
# print("llama: " + ask_llama_runpod(question, context))
# print("openai: " + ask_openai(question, context))






num_chunks = 5

quiz = [
    # { "q": "Who is the current mayor of Berlin?", "a": "Kai Wegner" },
    # { "q": "What is the population of Berlin?", "a": "3755251" },
    # { "q": "Can you name a twin city of Berlin?", "a": [ "Los Angeles","Paris","Madrid","Istanbul","Warsaw","Moscow","City of Brussels","Budapest","Tashkent","Mexico City","Beijing","Jakarta","Tokyo","Buenos Aires","Prague","Windhoek","London","Sofia","Tehran","Seville","Copenhagen","Kyiv","Brasília","Santo Domingo","Algiers","Rio de Janeiro" ] },
    # { "q": "Which River runs through Berlin?", "a": "Spree" },
    # { "q": "Who is the current mayor of Paris?", "a": "Anne Hidalgo" },
    # { "q": "What is the population of Paris?", "a": "2145906" },
    # { "q": "Can you name a twin city of Paris?", "a": [ "Rome","Tokyo","Kyoto","Berlin","Ramallah","Seoul","Cairo","Chicago","Torreón","San Francisco","Kyiv","Washington, D.C.","Marrakesh","Porto Alegre","Dubai","Beijing","Mexico City","Saint Petersburg" ] },
    # { "q": "Which River runs through Paris?", "a": "Seine" },
    # { "q": "Who is the current mayor of London?", "a": "Sadiq Khan" },
    # { "q": "What is the population of London?", "a": "8799728" },
    # { "q": "Can you name a twin city of London?", "a": [ "Berlin","Mumbai","New York City","Algiers","Sofia","Moscow","Tokyo","Beijing","Karachi","Zagreb","Tehran","Arequipa","Delhi","Bogotá","Johannesburg","Kuala Lumpur","Oslo","Sylhet","Shanghai","Baku","Buenos Aires","Istanbul","Los Angeles","Podgorica","New Delhi","Phnom Penh","Jakarta","Amsterdam","Bucharest","Santo Domingo","La Paz","Mexico City" ] },
    # { "q": "Which River runs through London?", "a": "River Thames" },
    { "q": "Who is the current mayor of Prague?", "a": "Bohuslav Svoboda" },
    # { "q": "What is the population of Prague?", "a": "1357326" },
    # { "q": "Can you name a twin city of Prague?", "a": [ "Berlin","Copenhagen","Miami-Dade County","Nuremberg","Luxembourg","Guangzhou","Hamburg","Helsinki","Nîmes","Prešov","Rosh HaAyin","Teramo","Bamberg","City of Brussels","Frankfurt","Jerusalem","Moscow","Saint Petersburg","Chicago","Taipei","Terni","Ferrara","Trento","Monza","Lecce","Naples","Vilnius","Istanbul","Sofia","Buenos Aires","Athens","Bratislava","Madrid","Tunis","Brussels metropolitan area","Amsterdam","Phoenix","Tirana","Kyoto","Cali","Drancy","Beijing","Shanghai","Tbilisi" ] },
    # { "q": "Which River runs through Prague?", "a": "Vltava" },
]

correct_contexts = 0

mistral_correct = 0
llama_correct = 0
openai_correct = 0

for i, qa in enumerate(quiz):
    question=qa["q"]
    answer=qa["a"]
    question_embedding = embeddings_model.encode(question)
    question_embedding = [float(value) for value in question_embedding]
    nearest_ids = index.get_nns_by_vector(
        question_embedding, num_chunks, include_distances=True
    )
    context=""
    for n in zip(nearest_ids[0], nearest_ids[1]):
        chunk_id=n[0]
        distance=n[1]
        # print("\n")
        # print(n)
        # print(chunks[n[0]].page_content)
        context+=chunks[chunk_id].page_content+"\n"

    print("\n####################################\n")
    print("Question: ", question)
    print("Expected answer: ", answer)
    if answer in context:
        # print("context has answer")
        correct_contexts+=1
    else:
        # print("context MISSING answer")
        print(context)

    # print("mistral: " + ask_mistral(question, context))
    mistral_response = ask_mistral(question, context)
    # print("llama: " + ask_llama_runpod(question, context))
    llama_response = ask_llama_runpod(question, context)
    # print("openai: " + ask_openai(question, context))
    openai_response = ask_openai(question, context)

    print(mistral_response)
    if answer in mistral_response.replace(',', '').replace('.', ''):
        mistral_correct+=1
        print("mistral correct")
    else:
        print("mistral wrong")

    print(llama_response)
    if answer in llama_response.replace(',', '').replace('.', ''):
        llama_correct+=1
        print("llama correct")
    else:
        print("llama wrong")

    print(openai_response)
    if answer in openai_response.replace(',', '').replace('.', ''):
        openai_correct+=1
        print("openai correct")
    else:
        print("openai wrong")

# print(f"Question: {question}")
# print("mistral: " + ask_mistral(question, context))
# print("llama: " + ask_llama_runpod(question, context))
# print("openai: " + ask_openai(question, context))
print("embedding_model\tchunk_size\tnum_chunks\tcorrect_contexts\tmistral_correct\tllama_correct\topenai_correct") 
print(f"{embedding_model_name}\t{chunk_size}\t{num_chunks}\t{correct_contexts}\t{mistral_correct}\t{llama_correct}\t{openai_correct}")
 
