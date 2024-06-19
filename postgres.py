from __future__ import annotations

import psycopg
import numpy
from psycopg.sql import SQL, Literal
from typing import List, Tuple
from dataclasses import dataclass

_db: psycopg.Connection | None = None


@dataclass
class Chunk:
    id: str
    text: str
    embedding: numpy.ndarray


def get_connection() -> psycopg.Connection:
    global _db
    if not _db:
        _db = psycopg.connect("postgresql://myuser:mypassword@postgres/mydb")
        _db.autocommit = False

    return _db


def init(embeddingLength: int):
    if not isinstance(embeddingLength, int) or embeddingLength <= 0:
        raise ValueError("Invalid embedding length")

    db = get_connection()
    cur = db.cursor()

    try:
        cur.execute("CREATE EXTENSION vectors;")
    except psycopg.errors.Error:
        print("extension 'vector' already exists.")
    db.commit()

    cur.execute(
        SQL(
            """
            CREATE TABLE IF NOT EXISTS chunks ( 
                id CHAR(16) NOT NULL, 
                text TEXT NOT NULL, 
                embedding vector( {} ) NOT NULL
            );
            """
        ).format(Literal(str(embeddingLength)))
    )
    cur.close()
    db.commit()


def insert(chunk: Chunk):
    db = get_connection()
    cur = db.cursor()

    embedding_string = "[" + ", ".join([str(num) for num in chunk.embedding]) + "]"

    cur.execute(
        "INSERT INTO chunks (id, text, embedding) VALUES (%s, %s, %s);",
        (chunk.id, chunk.text, embedding_string),
    )
    cur.close()
    db.commit()


def insertmany(chunks: List[Tuple[str, str, str]]):
    db = get_connection()
    cur = db.cursor()

    cur.executemany(
        "INSERT INTO chunks (id, text, embedding) VALUES (%s, %s, %s)", chunks
    )
    cur.close()
    db.commit()


def get_similar_chunks_with_distance(
    embeddingString: str, limit=5
) -> List[Tuple[Chunk, float]]:
    """<-> in pgvecto.rs is squared euclidean distance as metric"""

    cur = get_connection().cursor()
    cur.execute(
        """
        SELECT 
            c.id, c.text, 
            c.embedding <-> %s AS distance
        FROM chunks c
        ORDER BY c.embedding <-> %s
        LIMIT %s;
        """,
        (
            embeddingString,
            embeddingString,
            limit,
        ),
    )
    res = cur.fetchall()
    cur.close()

    return [
        (
            Chunk(id=r[0], text=r[1], embedding=[]),
            float(r[2]),
        )
        for r in res
    ]
