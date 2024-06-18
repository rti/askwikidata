rti@r25 tmp/wikidata-20240514
❱ cat wikidata-20240514.json | wc -l
108338657
Succeeded after 16:24

sync; echo 3 | sudo tee /proc/sys/vm/drop_caches; python read_wikidata_dump.py > properties.jsonl
python read_wikidata_dump.py > properties.jsonl

parse full dump:
 1532: 100.81 (avg 85.90) entities per ms
Succeeded after 44:28

>>> 108338657/(44*60+28)/1000
40.60669302848576

❱ sqlite3 labels-backup.db
SQLite version 3.45.3 2024-04-15 13:34:05
Enter ".help" for usage hints.
sqlite> select count(*) from labels;
91226199

sqlite> select count(*) from entities;
75497544

$ python wddump_textify.py
 1529: 45.62 (avg 38.28) entities per ms
 1530: 32.24 (avg 39.77) entities per ms
 1531: 26.29 (avg 37.79) entities per ms
 1532: 34.43 (avg 35.34) entities per ms
Succeeded after 130:20


docker run --rm --name pgvecto-rs -e POSTGRES_DB=mydb -e POSTGRES_USER=myuser -e POSTGRES_PASSWORD=mypassword -p 5432:5432 -d tensorchord/pgvecto-rs:pg16-v0.2.1

DROP EXTENSION IF EXISTS vectors;
CREATE EXTENSION vectors;

CREATE TABLE items (
    id CHAR(16) NOT NULL,
    embedding VECTOR(3)
);

