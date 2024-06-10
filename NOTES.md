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
