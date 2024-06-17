from wddump import read_wikidata_dump, line_to_entity
import sqlite3


def process_line(line):
    entity = line_to_entity(line)

    if entity is None:
        return

    if entity.get("type") == "item" or entity.get("type") == "property":
        id = entity.get("id")
        label = entity.get("labels", {}).get("en", {}).get("value", None)
        desc = entity.get("descriptions", {}).get("en", {}).get("value", None)

        if label is None:
            # print(f"found {entity_id} without en label", file=sys.stderr)
            return
        if desc is None:
            # print(f"found {entity_id} without en desc", file=sys.stderr)
            return

        return (id, label, desc)


class ResultHandler:
    LABEL_LEN = 128
    DESC_LEN = 1024

    @classmethod
    def init(cls):
        cls.counter = 0
        cls.conn = sqlite3.connect("entities.db")
        cls.cursor = cls.conn.cursor()
        cls.cursor.execute(
            " CREATE TABLE IF NOT EXISTS entities ("
            + "id CHAR(16) NOT NULL, "
            + ("label_en CHAR(" + str(cls.LABEL_LEN) + ") NOT NULL, ")
            + ("desc_en CHAR(" + str(cls.DESC_LEN) + ") NOT NULL")
            + ")"
        )
        # CREATE INDEX idx_entities_id ON entities (id);

    @classmethod
    def handle_result(cls, result):
        if result is not None:
            # print(result)
            # print(cursor.lastrowid)

            if len(result[1]) > cls.LABEL_LEN:
                # raise Exception(f"label too long in {result}")
                # print(f"label too long in {result}")
                return
            if len(result[2]) > cls.DESC_LEN:
                # raise Exception(f"desc too long in {result}")
                # print(f"desc too long in {result}")
                return

            cls.cursor.execute(
                """
                INSERT INTO entities VALUES (?, ?, ?)
                """,
                (result[0], result[1], result[2]),
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
