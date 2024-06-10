from read_wikidata_dump import read_wikidata_dump
import json
import sqlite3


def process_line(line):
    # print(f"'{line}'", file=sys.stderr)

    line = line.strip("\n")

    if line == "[" or line == "]":
        return

    line = line.rstrip(",")

    entity = None

    try:
        entity = json.loads(line)
    except ValueError as e:
        print("failed to parse json", e, line)
        raise e

    if entity is None:
        return

    if entity.get("type") == "item" or entity.get("type") == "property":
        entity_id = entity.get("id")
        entity_label = entity.get("labels", {}).get("en", {}).get("value", None)

        if entity_label is None:
            # print(f"found {entity_id} without en label", file=sys.stderr)
            return

        return (entity_id, entity_label)


class ResultHandler:
    @classmethod
    def init(cls):
        cls.counter = 0
        cls.conn = sqlite3.connect("labels.db")
        cls.cursor = cls.conn.cursor()
        cls.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS labels (
                item_id CHAR(16) NOT NULL,
                label_en CHAR(64) NOT NULL
            )
            """
        )

    @classmethod
    def handle_result(cls, result):
        if result is not None:
            # print(result)
            # print(cursor.lastrowid)
            cls.cursor.execute(
                """
                INSERT INTO labels VALUES (?, ?)
                """,
                (result[0], result[1]),
            )
            cls.counter = cls.counter + 1

            if cls.counter > 1024 * 1024:
                cls.counter = 0
                print("commit to db")
                cls.conn.commit()


if __name__ == "__main__":
    ResultHandler.init()

    read_wikidata_dump(
        "/home/rti/tmp/wikidata-20240514/wikidata-20240514.json",
        process_line,
        ResultHandler.handle_result,
    )
