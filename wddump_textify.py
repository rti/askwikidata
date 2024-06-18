from wddump import read_wikidata_dump, line_to_entity
import sqlite3
import postgres
import embeddings
import pandas as pd
from typing import List

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

                item_statement_texts.append((subject_id, text))

        df = pd.DataFrame(item_statement_texts, columns=["id", "text"])
        return df


class ResultHandler:
    @classmethod
    def init(cls):
        # test_embedding = embeddings.embed_query("test")
        # postgres.init(len(test_embedding))
        postgres.init(384)

        pass

    @classmethod
    def handle_result(cls, df):
        if df is not None:
            embeds = embeddings.embed_docs(df["text"].values)

            # print("========")
            # print(embeds)
            # print("========")

            for index, row in df.iterrows():
                # print(index, row["id"], row["text"], embeds[index])
                # e = embeds.
                postgres.insert(
                    postgres.Chunk(id=row["id"], text=row["text"], embedding=embeds[index])
                )


if __name__ == "__main__":
    ResultHandler.init()

    read_wikidata_dump(
        "/home/rti/tmp/wikidata-20240514/wikidata-20240514.json",
        process_line,
        ResultHandler.handle_result,
    )
