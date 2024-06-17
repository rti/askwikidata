from wddump import read_wikidata_dump, line_to_entity
import sqlite3


conn = sqlite3.connect("entities.db")
cursor = conn.cursor()


def get_label(id):
    global cursor
    cursor.execute("SELECT label_en FROM entities WHERE id=?", (id,))
    results = cursor.fetchall()
    label = results[0][0]
    if label is None:
        raise Exception("could not find label")
    return label


def get_desc(id):
    global cursor
    cursor.execute("SELECT desc_en FROM entities WHERE id=?", (id,))
    results = cursor.fetchall()
    desc = results[0][0]
    if desc is None:
        raise Exception("could not find label")
    return desc


def format_date(date_value):
    # TODO: implement me
    return date_value


def gen_statement_text(subject_label, subject_desc, property_label, statement):
    datatype = statement["mainsnak"]["datatype"]

    if datatype == "wikibase-item":
        object_id = statement["mainsnak"]["datavalue"]["value"]["id"]
        object_label = get_label(object_id).rstrip(".")
        object_desc = get_desc(object_id).rstrip(".")

        print(
            f"{subject_label}: {subject_desc}.\n"
            + f"{subject_label} {property_label} {object_label}.\n"
            + f"{object_label}: {object_desc}.\n"
        )

    elif datatype == "time":
        pass

    elif datatype == "string":
        pass

    elif datatype == "quantity":
        pass

    pass


def process_line(line):
    entity = line_to_entity(line)

    if entity is None:
        return None

    if entity.get("type") == "item":
        item_statement_texts = []

        subject_id = entity.get("id")
        subject_label = entity.get("labels", {}).get("en", {}).get("value", None)
        subject_desc = entity.get("descriptions", {}).get("en", {}).get("value", None)
        claims = entity.get("claims")

        for claim_key in claims:
            property = claim_key
            property_label = get_label(claim_key)
            statement_group = claims[claim_key]
            for statement in statement_group:
                item_statement_texts.append(
                    gen_statement_text(
                        subject_label, subject_desc, property_label, statement
                    )
                )

        return item_statement_texts


class ResultHandler:
    @classmethod
    def init(cls):
        pass

    @classmethod
    def handle_result(cls, result):
        if result is not None:
            print(result)


if __name__ == "__main__":
    ResultHandler.init()

    read_wikidata_dump(
        "/home/rti/tmp/wikidata-20240514/wikidata-20240514.json",
        process_line,
        ResultHandler.handle_result,
    )
