import glob
import json
import os
import requests
import datetime

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings.huggingface import HuggingFaceEmbeddings
from annoy import AnnoyIndex
import openai


HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")
RUNPOD_API_KEY = os.getenv("RUNPOD_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


class AskWikidata:
    chunk_embeddings_cache_file_path = "wikidata_embed_cache.json"
    chunks = []
    embeds = []

    def __init__(
        self,
        chunk_size=768,
        chunk_overlap=0,
        embedding_model_name="BAAI/bge-small-en-v1.5",
        index_trees=10,
        retrieval_chunks=3,
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.index_trees = index_trees
        self.retrieval_chunks = retrieval_chunks
        self.embedding_model_name = embedding_model_name

    def setup(self):
        self.create_chunk_embeddings()
        self.create_index()

    def create_chunk_embeddings(self):
        texts = []
        metas = []
        directory_path = "./text_representations"

        for file_path in glob.glob(os.path.join(directory_path, "*.txt")):
            with open(file_path, "r") as file:
                texts.append(file.read())
                file_name = file_path.split("/")[-1]
                q_id = file_name.split(".")[0]
                metas.append({"source": f"https://www.wikidata.org/wiki/{q_id}"})

        self.chunks = self.create_chunks(texts, metas)
        print(f"Created {len(self.chunks)} chunks.")

        self.embeds = self.create_embeds(self.chunks, self.embedding_model_name)
        print(
            f"Created {len(self.embeds)} embeddings with {len(self.embeds[0])} dimensions."
        )

        self.save_embeddings_cache()

        return self.chunks, self.embeds

    def create_chunks(self, texts, metas):
        text_splitter = RecursiveCharacterTextSplitter(
            separators=["\n\n", "\n"],
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
        )
        chunks = text_splitter.create_documents(texts, metadatas=metas)
        return chunks

    def create_embeds(self, chunks, embedding_model_name):
        embeds = []

        self.embeddings_model = HuggingFaceEmbeddings(model_name=embedding_model_name)

        if self.load_embeddings_cache():
            return self.embeds;

        for t in chunks:
            embeds.append(self.embeddings_model.embed_documents([t.page_content])[0])

        return embeds

    def save_embeddings_cache(self):
        cache_data = {
            "embeds": self.embeds
        }
        with open(self.chunk_embeddings_cache_file_path, 'w') as cache_file:
            json.dump(cache_data, cache_file)
        print(f"Saved embeddings cache to {self.chunk_embeddings_cache_file_path}.")

    def load_embeddings_cache(self):
        if os.path.exists(self.chunk_embeddings_cache_file_path):
            with open(self.chunk_embeddings_cache_file_path, 'r') as cache_file:
                cache_data = json.load(cache_file)
            self.embeds = cache_data["embeds"]
            print(f"Loaded embeddings cache from {self.chunk_embeddings_cache_file_path}.")
            return True
        return False

    def create_index(self):
        embed_dims = len(self.embeds[0])
        self.index = AnnoyIndex(embed_dims, "angular")
        for i, e in enumerate(self.embeds):
            self.index.add_item(i, e)
        self.index.build(self.index_trees)

    def ask(self, query):
        query_embed = self.embeddings_model.embed_documents([query])[0]
        query_embed_float = [float(value) for value in query_embed]
        nearest_ids = self.index.get_nns_by_vector(
            query_embed_float, self.retrieval_chunks, include_distances=True
        )
        context = ""
        for n in zip(nearest_ids[0], nearest_ids[1]):
            context += self.chunks[n[0]].page_content + "\n"
            # print(n)
            # print(self.chunks[n[0]].page_content)
            # print("\n")

        return self.ask_llama_hf(query, context)
        # return self.ask_mistral_hf(query, context)
        # return self.ask_llama_runpod(query, context)
        # return self.ask_openai(query, context)

    def system_from_context(self, context):
        system = (
            "You are answering questions for a given context. "
            + "Answer based on information from the given context only. "
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
        print(
            f"Sending the following prompt to mistral ({len(prompt)} chars , about {int(len(prompt)/3)} tokens)\n{prompt}"
        )
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
        print(
            f"Sending the following prompt to llama ({len(prompt)} chars , about {int(len(prompt)/3)} tokens)\n{prompt}"
        )
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
# print("openai: " + ask_openai(queostion, context))

if __name__ == "__main__":
    askwikidata = AskWikidata()
    askwikidata.create_chunk_embeddings()
    askwikidata.create_index()

    # TODO: mistral does not get it atm, why?
    query = "Who is the current mayor of Berlin today?"
    response = askwikidata.ask(query)
    print(response + "\n")
