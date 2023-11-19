import askwikidata

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
    embeddings_model = SentenceTransformer(embedding_model_name)
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
 
