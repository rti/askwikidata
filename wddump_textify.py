from wddump import read_wikidata_dump, line_to_entity
import sqlite3
import time
import postgres
import embeddings

from multiprocessing import Process, Queue

conn = sqlite3.connect("entities.db")
cursor = conn.cursor()


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
        return (
            f"{subject_label}: {subject_desc}.\n"
            + f"{subject_label} {property_label} {object_label}.\n"
            + f"{object_label}: {object_desc}.\n"
        )

    elif datatype == "string":
        value = statement["mainsnak"]["datavalue"]["value"].rstrip(".")

        # print (
        #     f"{subject_label}: {subject_desc}.\n"
        #     + f"{subject_label} {property_label} {value}.\n"
        # )
        return (
            f"{subject_label}: {subject_desc}.\n"
            + f"{subject_label} {property_label} {value}.\n"
        )

    elif datatype == "time":
        pass

    elif datatype == "quantity":
        pass

    pass


def process_line(line):
    entity = line_to_entity(line)

    if entity is None:
        return

    if entity.get("type") == "item":
        item_statement_texts = []

        subject_id = entity.get("id", None)
        subject_label = entity.get("labels", {}).get("en", {}).get("value", None)
        subject_desc = entity.get("descriptions", {}).get("en", {}).get("value", None)

        if subject_id is None or subject_label is None or subject_desc is None:
            return

        claims = entity.get("claims")

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
    read_wikidata_dump(
        "/home/rti/tmp/wikidata-20240514/wikidata-20240514.json",
        process_line,
        threads=2
    )


GPU_BATCH_SIZE = 65536


def handle_embed_queue():
    embeddings.embed_docs(["warmup"])

    ids = []
    texts = []
    while True:
        if len(texts) == GPU_BATCH_SIZE:
            start_time = time.time()
            embeds = embeddings.embed_docs(texts, batch_size=256)
            end_time = time.time()
            diff = end_time - start_time
            print(
                f" > Embed {GPU_BATCH_SIZE / (1000*diff):.2f}stmt/ms Q:{embed_queue.qsize()}"
            )

            # tuple = (ids.copy(), texts.copy(), embeds.copy())
            # print(f"inserting {len(ids)} {len(texts)} {len(embeds)} to insert_queue")
            # insert_queue.put(tuple, block=False)

            ids = []
            texts = []

        item = embed_queue.get()

        if item is None:
            break

        ids.append(item[0])
        texts.append(item[1])


def handle_insert_queue():
    while True:
        t = insert_queue.get()

        # print(f"{len(t[0])} {len(t[1])} {len(t[2])}")

        if t is None:
            break

        start_time = time.time()
        for id, text, embed in zip(t[0], t[1], t[2]):
            postgres.insert(postgres.Chunk(id=id, text=text, embedding=embed))
        end_time = time.time()
        diff = end_time - start_time
        print(
            f"Inserted batch in {diff:.2f} seconds ({1000 * diff / GPU_BATCH_SIZE:.2f} ms/chunk) Queue: {insert_queue.qsize() * GPU_BATCH_SIZE}"
        )


if __name__ == "__main__":
    ResultHandler.init()

    postgres.init(384)

    global embed_queue
    global insert_queue
    embed_queue = Queue(maxsize=GPU_BATCH_SIZE * 4)
    insert_queue = Queue()

    read_dump_process = Process(target=read_dump)
    insert_process = Process(target=handle_insert_queue)
    read_dump_process.start()
    insert_process.start()

    handle_embed_queue()

    read_dump_process.join()
    insert_process.join()

    # embed_process.join()
