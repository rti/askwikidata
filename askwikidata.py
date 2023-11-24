import glob
import json
import os
import requests
import datetime
import time
import pandas as pd
from tqdm import tqdm

from langchain.embeddings.huggingface import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from annoy import AnnoyIndex
import openai

import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer


HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")
RUNPOD_API_KEY = os.getenv("RUNPOD_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


class AskWikidata:
    df = pd.DataFrame()

    def __init__(
        self,
        chunk_overlap=0,
        chunk_size=768,
        context_chunks=7,
        embedding_model_name="BAAI/bge-small-en-v1.5",
        index_trees=10,
        qa_model_name="mistral-7b-instruct-v0.1",
        reranker_model_name="BAAI/bge-reranker-base",
        retrieval_chunks=64,
        cache_file=None,
    ):
        self.chunk_overlap = chunk_overlap
        self.chunk_size = chunk_size
        self.context_chunks = context_chunks
        self.embedding_model_name = embedding_model_name
        self.index_trees = index_trees
        self.qa_model_name = qa_model_name
        self.reranker_model_name = reranker_model_name
        self.retrieval_chunks = retrieval_chunks
        self.cache_file = cache_file

        if not cache_file:
            emn = embedding_model_name.replace("/","-")
            self.cache_file = f"cache-{chunk_size}-{chunk_overlap}-{emn}.json"

        self.embedding_model = HuggingFaceEmbeddings(
            model_name=self.embedding_model_name
        )

        self.rerank_tokenizer = AutoTokenizer.from_pretrained(self.reranker_model_name)
        self.rerank_model = AutoModelForSequenceClassification.from_pretrained(
            self.reranker_model_name
        )

    def setup(self):
        if not self.load_cache():
            self.read_data()
            self.create_embeds()
            self.save_cache()
        self.create_index()

    def read_data(self):
        directory_path = "./text_representations"

        texts = []
        metas = []

        files = glob.glob(os.path.join(directory_path, "*.txt"))
        print("Loading files...")
        for file_path in files:
            with open(file_path, "r") as file:
                texts.append(file.read())
                file_name = file_path.split("/")[-1]
                q_id = file_name.split(".")[0]
                metas.append({"source": f"https://www.wikidata.org/wiki/{q_id}"})

        print("Creating chunks...")
        text_splitter = RecursiveCharacterTextSplitter(
            separators=["\n\n", "\n"],
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
        )
        chunks = text_splitter.create_documents(texts, metadatas=metas)

        self.df = pd.DataFrame(columns=["id", "text", "source"])

        for i, c in enumerate(chunks):
            self.df.loc[i] = [i, c.page_content, c.metadata["source"]]

        print(f"  {len(self.df)} chunks.")

    def create_embeds(self):
        embeds = []
        print("Creating embeddings...")
        for _, row in tqdm(self.df.iterrows(), total=len(self.df)):
            text = str(row["text"])
            embeddings = self.embedding_model.embed_documents([text])
            embeds.append(embeddings[0])
        self.df["embeddings"] = embeds

    def save_cache(self):
        self.df.to_json(self.cache_file)
        print(f"Saved embeddings cache to {self.cache_file}.")

    def load_cache(self):
        if os.path.exists(self.cache_file):
            self.df = pd.read_json(self.cache_file)
            print(f"Loaded embeddings cache from {self.cache_file}.")
            return True
        return False

    def create_index(self):
        print("Creating vector space index...")
        embed_dims = len(self.df.iloc[0]["embeddings"])
        self.index = AnnoyIndex(embed_dims, "angular")
        for i, e in enumerate(self.df["embeddings"]):
            self.index.add_item(i, e)
        self.index.build(self.index_trees)

    def retrieve(self, query: str) -> pd.DataFrame:
        print("Retrieving...")
        query_embed = self.embedding_model.embed_documents([query])[0]
        query_embed_float = [float(value) for value in query_embed]
        nns = self.index.get_nns_by_vector(
            query_embed_float, self.retrieval_chunks, include_distances=True
        )
        nns_ids = nns[0]
        nns_distances = nns[1]
        ret = self.df.iloc[nns_ids].copy()
        ret["retrieve_distance"] = nns_distances
        ret = ret.sort_values("retrieve_distance")
        return ret

    def rerank(self, query: str, df: pd.DataFrame):
        print("Reranking...")
        start = time.time()

        pairs = []
        for _, n in df.iterrows():
            pairs.append([query, n["text"]])

        with torch.no_grad():
            inputs = self.rerank_tokenizer(
                pairs,
                padding=True,
                truncation=True,
                return_tensors="pt",
                max_length=512,
            )

            scores = (
                self.rerank_model(**inputs, return_dict=True)
                .logits.view(
                    -1,
                )
                .float()
            )

        df["rank"] = scores
        ret = df.sort_values(by="rank", ascending=False).head(self.context_chunks)
        seconds = time.time() - start
        return ret, seconds

    def print_data(self):
        pd.set_option("display.max_rows", None)
        print(self.df)

    def context(self, df: pd.DataFrame):
        context = ""
        for _, row in df.iterrows():
            context += row["text"] + "\n"
        return context.replace("\n\n", "\n")

    def ask(self, query):
        context = self.context(query)

        if self.qa_model_name == "llama-2-7b-chat":
            return self.ask_llama_hf(query, context)
        elif self.qa_model_name == "mistral-7b-instruct-v0.1":
            return self.ask_mistral_hf(query, context)
        else:
            raise Exception("unknown model")
        # return self.ask_mistral_hf(query, context)
        # return self.ask_llama_runpod(query, context)
        # return self.ask_openai(query, context)

    def system_from_context(self, context):
        system = (
            "You are answering questions for a given context. "
            + "Answer based on information from the given context only, but do not mention the context in your response. "
            + "If the answer is not in the context say that you do not know the answer. "
            + "Only give the answer, do not provide any further explanations. "
            + "Do not mention the context. "
            + "Dates and timespans will be presented to you in YYYY-MM-DD format. Interpret those. "
            + "For reference, today is the "
            + f"{datetime.date.today().strftime('%Y-%m-%d')}. "
            + "Respond with the most current information unless requested otherwise.\n"
            + f"\nCONTEXT:\n{context}"
        )
        return system

    def llama_prompt(self, text, system="You are a helpful assistent."):
        return f"<s>[INST] <<SYS>>\n{system}\n<</SYS>>\n\n{text} [/INST]"

    def ask_llama_runpod(self, question, context):
        # access LLM on runpod
        url = f"https://api.runpod.ai/v2/llama2-7b-chat/runsync"
        headers = {
            "Authorization": RUNPOD_API_KEY,
            "Content-Type": "application/json",
        }
        system = self.system_from_context(context)
        prompt = self.llama_prompt(question, system)
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
    def ask_openai(self, question, context):
        openai.api_key = OPENAI_API_KEY
        openai_model = "gpt-3.5-turbo"
        # openai_model = "gpt-4"
        # openai_model = "gpt-4-1106-preview"
        system = self.system_from_context(context)
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
    def mistral_prompt(self, text, system="You are a helpful assistent."):
        return f"<s>[INST] {system}\n\nQUESTION: {text} [/INST]"

    def ask_mistral_hf(self, question, context):
        if HUGGINGFACE_API_KEY is None:
            raise Exception("HUGGINGFACE_API_KEY is None.")

        API_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.1"
        headers = {"Authorization": f"Bearer {HUGGINGFACE_API_KEY}"}
        system = self.system_from_context(context)
        prompt = self.mistral_prompt(question, system)
        # print(
        #     f"Sending the following prompt to mistral ({len(prompt)} chars , about {int(len(prompt)/3)} tokens)\n{prompt}"
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

    def ask_llama_hf(self, question, context):
        if HUGGINGFACE_API_KEY is None:
            raise Exception("HUGGINGFACE_API_KEY is None.")

        API_URL = (
            "https://api-inference.huggingface.co/models/meta-llama/Llama-2-7b-chat-hf"
        )
        headers = {"Authorization": f"Bearer {HUGGINGFACE_API_KEY}"}
        system = self.system_from_context(context)
        prompt = self.llama_prompt(question, system)
        # print(
        #     f"Sending the following prompt to llama ({len(prompt)} chars , about {int(len(prompt)/3)} tokens)\n{prompt}"
        # )
        response = requests.post(
            API_URL,
            headers=headers,
            json={
                "inputs": prompt,
                "parameters": {
                    # max is 250 https://huggingface.co/docs/api-inference/detailed_parameters#text-generation-task
                    "max_new_tokens": 250,
                },
            },
        )
        # print(response.json())
        return response.json()[0]["generated_text"].replace(prompt, "").strip()


# if __name__ == "__main__":
#     askwikidata = AskWikidata()
#     askwikidata.setup()
#
#     query = "Who is the current mayor of Berlin today?"
#     # query = "Who was the mayor of Berlin in 2001?"
#     print("QUERY: ", query)
#
#     retrieved_ids = askwikidata.retrieve(query)
#     print("RETRIEVED: ", retrieved_ids)
#
#     reranked = askwikidata.rerank(retrieved_ids)
#     print("RERANKED: ", reranked)
#
#     # context = askwikidata.context(query)
#     # print(context)
#     # response = askwikidata.ask(query)
#     # print(response)
