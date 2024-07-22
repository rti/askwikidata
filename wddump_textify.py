import time
import sqlite3

from multiprocessing import Process, Queue
import setproctitle

from dask.distributed import Client, LocalCluster

from wddump import read_wikidata_dump, line_to_entity
import embeddings
import postgres



EMBED_QUEUE_SIZE = 1024
EMBED_BATCH_SIZE = 32
INSERT_QUEUE_SIZE = 1


def get_label(id):
    global cursor
    cursor.execute("SELECT label_en FROM entities WHERE id=?", (id,))
    results = cursor.fetchall()

    if len(results) == 0:
        # raise Exception(f"could not find label for id {id}")
        # print(f"could not find label for id {id}")
        return

    label = results[0][0]
    if label is None:
        # raise Exception(f"could not find label for id {id}")
        # print(f"could not find label for id {id}")
        return

    return label


def get_desc(id):
    global cursor
    cursor.execute("SELECT desc_en FROM entities WHERE id=?", (id,))
    results = cursor.fetchall()

    if len(results) == 0:
        # raise Exception(f"could not find description for id {id}")
        # print(f"could not find description for id {id}")
        return

    desc = results[0][0]
    if desc is None:
        # raise Exception(f"could not find description for id {id}")
        # print(f"could not find description for id {id}")
        return

    return desc


def format_date(date_value):
    # TODO: implement me
    return date_value


def gen_statement_text(subject_label, subject_desc, property_label, statement):
    snaktype = statement["mainsnak"]["snaktype"]
    if snaktype != "value":
        return

    datatype = statement["mainsnak"]["datatype"]

    if datatype == "wikibase-item":
        mainsnak = statement.get("mainsnak")
        datavalue = mainsnak.get("datavalue")
        value = datavalue.get("value")
        object_id = value.get("id")
        object_label = get_label(object_id)
        object_desc = get_desc(object_id)

        if object_label is None or object_desc is None:
            return

        object_label = object_label.rstrip(".")
        object_desc = object_desc.rstrip(".")

        # print (
        #     f"{subject_label}: {subject_desc}.\n"
        #     + f"{subject_label} {property_label} {object_label}.\n"
        #     + f"{object_label}: {object_desc}.\n"
        # )
        # return (
        #     f"{subject_label}: {subject_desc}.\n"
        #     + f"{subject_label} {property_label} {object_label}.\n"
        #     + f"{object_label}: {object_desc}.\n"
        # )
        return f"{subject_label} ({subject_desc}) {property_label} {object_label} ({object_desc})."

    elif datatype == "string":
        value = statement["mainsnak"]["datavalue"]["value"].rstrip(".")

        # print (
        #     f"{subject_label}: {subject_desc}.\n"
        #     + f"{subject_label} {property_label} {value}.\n"
        # )
        # return (
        #     f"{subject_label}: {subject_desc}.\n"
        #     + f"{subject_label} {property_label} {value}.\n"
        # )
        return f"{subject_label} ({subject_desc}) {property_label} {value}."

    elif datatype == "time":
        pass

    elif datatype == "quantity":
        pass

    pass


def is_scholar_article(entity):
    claims = entity.get("claims")

    instance_of = claims.get("P31")
    if instance_of is None:
        return

    for statement in instance_of:
        mainsnak = statement["mainsnak"]
        snaktype = mainsnak["snaktype"]

        if snaktype != "value":
            continue

        datatype = mainsnak["datatype"]

        if datatype != "wikibase-item":
            continue

        datavalue = mainsnak.get("datavalue")
        value = datavalue.get("value")
        id = value.get("id")

        if id == "Q13442814":  # scholar article
            return True


def process_line(line):
    entity = line_to_entity(line)

    if entity is None:
        return

    if entity.get("type") != "item":
        return

    subject_id = entity.get("id", None)
    subject_label = entity.get("labels", {}).get("en", {}).get("value")
    subject_desc = entity.get("descriptions", {}).get("en", {}).get("value")
    claims = entity.get("claims")

    if is_scholar_article(entity):
        print(f"Skipping scholar article {subject_id} ({subject_label})")
        return  # skip

    if subject_id is None or subject_label is None or subject_desc is None:
        return

    for claim_key in claims:
        property_label = get_label(claim_key)

        if property_label is None:
            continue

        statement_group = claims[claim_key]

        for statement in statement_group:
            text = gen_statement_text(
                subject_label, subject_desc, property_label, statement
            )

            if text is None:
                continue
            if len(text) == 0:
                continue

            embed_queue.put((subject_id, text), block=True)


def read_dump():
    setproctitle.setproctitle("wddump-read")
    read_wikidata_dump("/wikidata.json", process_line, threads=8)




async def embed_batch(ids, texts):
    embeds = embeddings.embed_docs(texts, batch_size=256)
    return (ids, texts, embeds)


def handle_embed_queue():
    setproctitle.setproctitle("wddump-embed-queue")
    print("Start handle embed queue...")

    daskCluster = Client(
        LocalCluster(
            n_workers=2,
            threads_per_worker=1,
            memory_limit="auto",
            dashboard_address="0.0.0.0:8787",
        )
    )
    print(daskCluster.dashboard_link)

    embeddings.embed_query("warmup")

    ids = []
    texts = []
    tasks = []

    while True:
        item = embed_queue.get()

        if item is not None:
            ids.append(item[0])
            texts.append(item[1])

        if len(texts) == EMBED_BATCH_SIZE or (len(texts) and item is None):
            future = daskCluster.submit(embed_batch, ids, texts)
            tasks.append(future)
            ids = []
            texts = []

        if len(tasks) and tasks[0].status == "finished":  # TODO: handle last batch
            future = tasks[0]
            tasks = tasks[1:]
            result = future.result()
            insert_queue.put(result, block=True)


def handle_insert_queue():
    setproctitle.setproctitle("wddump-insert-queue")
    print("Start handle insert queue...")

    while True:
        start_time = time.time()

        insert_data = insert_queue.get()
        if insert_data is None:
            break

        chunks = []

        for id, text, embed in zip(insert_data[0], insert_data[1], insert_data[2]):
            embedding_string = "[" + ", ".join([str(num) for num in embed]) + "]"
            chunks.append((id, text, embedding_string))
        postgres.insertmany(chunks)

        end_time = time.time()
        diff = end_time - start_time
        print(
            f" # DBins {EMBED_BATCH_SIZE / (1000*diff):.2f}stmt/ms Q:{float(insert_queue.qsize()):.1f}"
        )


if __name__ == "__main__":
    setproctitle.setproctitle("wddump-main")

    conn = sqlite3.connect("entities.db")

    global cursor
    cursor = conn.cursor()

    # TODO: do not hardcode embedding dims
    postgres.init(384)

    global embed_queue
    global insert_queue
    embed_queue = Queue(maxsize=EMBED_QUEUE_SIZE)
    insert_queue = Queue(maxsize=1)

    read_dump_process = Process(target=read_dump)
    embed_process = Process(target=handle_embed_queue)
    insert_process = Process(target=handle_insert_queue)
    read_dump_process.start()
    embed_process.start()
    insert_process.start()

    read_dump_process.join()
    embed_process.join()
    insert_process.join()
