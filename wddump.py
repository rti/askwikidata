from multiprocessing import Pool, cpu_count
import json
import time
import sys
import asyncio
import aiofiles
import os


async def handle_lines(pool, line_handler_func, chunk_of_lines):
    return pool.map(line_handler_func, chunk_of_lines)


def init_worker():
    os.nice(19)


async def process_file(
    file_path, line_handler_func, result_handler_func, num_processes, chunk_size
):
    with Pool(num_processes, init_worker) as pool:
        start = time.time()
        line_per_ms_values = []
        iterations = 0

        file = await aiofiles.open(file_path, mode="r")

        read_task = asyncio.create_task(file.readlines(chunk_size))

        while True:
            chunk_of_lines = await read_task
            if not chunk_of_lines:
                break

            read_task = asyncio.create_task(file.readlines(chunk_size))
            process_task = asyncio.create_task(
                handle_lines(pool, line_handler_func, chunk_of_lines)
            )
            results = await process_task

            if result_handler_func:
                for result in results:
                    result_handler_func(result)

            time_per_iteration_ms = (time.time() - start) * 1000
            lines_per_ms = len(chunk_of_lines) / time_per_iteration_ms
            line_per_ms_values.append(lines_per_ms)
            line_per_ms_values = line_per_ms_values[-16:]
            lines_per_ms_avg = sum(line_per_ms_values) / len(line_per_ms_values)
            iterations += 1
            print(
                f"{iterations:5}: {lines_per_ms:.2f} (avg {lines_per_ms_avg:.2f}) ents/ms",
                file=sys.stderr,
            )

            # if iterations == 4:
            #     break

            start = time.time()

        await file.close()


def read_wikidata_dump(
    dump_file,
    line_handler_func,
    result_handler_func=None,
    threads=None,
    chunk_size=None,
):
    if threads is None:
        threads = int(cpu_count() * 2)

    if chunk_size is None:
        chunk_size = int(1024 * 1024 * 1024 * 1)

    print(f"Using {threads} processes to process lines", file=sys.stderr)
    print(
        f"Reading {int(chunk_size / (1024 * 1024))}MB chunks from disk", file=sys.stderr
    )
    asyncio.run(
        process_file(
            dump_file, line_handler_func, result_handler_func, threads, chunk_size
        )
    )


def line_to_entity(line):
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

    return entity
