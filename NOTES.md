rti@r25 tmp/wikidata-20240514
❱ cat wikidata-20240514.json | wc -l
108338657
Succeeded after 16:24

sync; echo 3 | sudo tee /proc/sys/vm/drop_caches; python read_wikidata_dump.py > properties.jsonl
python read_wikidata_dump.py > properties.jsonl

parse full dump:
    1532: 86.84 (avg 73.79) entities per ms
    Succeeded after 51:53       

>>> 108338657/52/60
34723.92852564102
