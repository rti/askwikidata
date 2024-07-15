from dask.distributed import Client, progress
from dask import bag as db
from dask import dataframe as df
import dask

from json import loads as json_loads

def process(batch):
    batch = map(lambda s: s.lstrip("[").lstrip("]").rstrip(","), batch)
    batch = map(json_loads, batch)

def main():
    client = Client(n_workers=8, threads_per_worker=1, memory_limit="auto")
    print(client.dashboard_link)


    file_path = "/home/rti/tmp/wikidata-20240514/wikidata-20240514.json"

    batch_size = 512
    with open(file_path, 'r') as file:
        batch = []
        for line in file:
            batch.append(line)
            if len(batch) >= batch_size:
                future = client.submit(process, batch)
                batch = []
                future.result()


    # with ProgressBar():
    # x = (
    #     db.read_text(
    #         "", blocksize="32M"
    #     )
    #     .map(lambda s: s.rstrip(",\n"))
    #     # .map(lambda s: s.rstrip("[\n"))
    #     # .map(lambda s: s.rstrip("]\n"))
    #     # .filter(len)
    #     # .map(json_load)
    #     # .take(2)
    #     .compute()
    # )
    # progress(x)
    # # print(x)
    #

if __name__ == "__main__":
    main()
