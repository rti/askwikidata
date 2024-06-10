from multiprocessing import Pool, cpu_count
import json
import time
import sys
import asyncio
import aiofiles


async def process(pool, line_handler_func, chunk_of_lines):
    return pool.map(line_handler_func, chunk_of_lines)


async def readlines(file, chunk_size):
    return await file.readlines(chunk_size)


async def process_file(file_path, line_handler_func, num_processes, chunk_size):
    with Pool(num_processes) as pool:
        start = time.time()
        line_per_ms_values = []
        iterations = 0

        file = await aiofiles.open(file_path, mode="r")

        read_task = asyncio.create_task(readlines(file, chunk_size))

        while True:
            chunk_of_lines = await read_task
            if not chunk_of_lines:
                break

            read_task = asyncio.create_task(readlines(file, chunk_size))
            process_task = asyncio.create_task(
                process(pool, line_handler_func, chunk_of_lines)
            )
            results = await process_task

            for result in results:
                if result is not None:
                    print(result)

            time_per_iteration_ms = (time.time() - start) * 1000
            lines_per_ms = len(chunk_of_lines) / time_per_iteration_ms
            line_per_ms_values.append(lines_per_ms)
            line_per_ms_values = line_per_ms_values[-5:]
            lines_per_ms_avg = sum(line_per_ms_values) / len(line_per_ms_values)
            iterations += 1
            print(
                f"{iterations:5}: {lines_per_ms:.2f} (avg {lines_per_ms_avg:.2f}) entities per ms",
                file=sys.stderr,
            )

            # if iterations == 4:
            #     break

            start = time.time()

        await file.close()


def read_wikidata_dump(dump_file, line_handler_func):
    threads = int(cpu_count() * 2)
    chunksize = int(1024 * 1024 * 1024 * 1)
    print(f"using {threads} processes, {chunksize} as chunk_size", file=sys.stderr)
    asyncio.run(process_file(dump_file, line_handler_func, threads, chunksize))


# Example usage
def process_line(line):
    # print(f"'{line}'", file=sys.stderr)

    line = line.strip("\n")
    # line = line[:-1]

    if line == "[" or line == "]":
        return

    # remove tailing ,
    line = line.rstrip(",")
    # line = line[:-1]

    entity = None

    try:
        entity = json.loads(line)
    except ValueError as e:
        print("failed to parse json", e, line)
        raise e

    if entity is None:
        return

    if entity.get("type") == "property":
        print(f"found prop {entity.get('id')}", file=sys.stderr)
        return json.dumps(entity)


if __name__ == "__main__":
    read_wikidata_dump(
        "/home/rti/tmp/wikidata-20240514/wikidata-20240514.json", process_line
    )
