"""SQLite 初始化与轻量读写封装。"""
import sqlite3
from contextlib import contextmanager
from typing import Iterator

from .config import DB_PATH


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def cursor() -> Iterator[sqlite3.Cursor]:
    conn = get_conn()
    try:
        cur = conn.cursor()
        yield cur
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with cursor() as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question TEXT NOT NULL,
                context TEXT,
                status TEXT NOT NULL DEFAULT 'open',  -- open | answered | closed
                created_at TEXT NOT NULL DEFAULT (datetime('now','localtime'))
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS kb_audit (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_id INTEGER,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',  -- pending | approved | rejected
                created_at TEXT NOT NULL DEFAULT (datetime('now','localtime'))
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS knowledge (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                vector TEXT NOT NULL,                  -- JSON 序列化的稀疏向量
                source TEXT NOT NULL DEFAULT 'seed',   -- seed | human
                created_at TEXT NOT NULL DEFAULT (datetime('now','localtime'))
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS playbook (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question TEXT NOT NULL,                 -- 客户问题(示范)
                answer TEXT NOT NULL,                   -- 标准答案/话术
                note TEXT,                              -- 这么答的原因/套路
                source TEXT NOT NULL DEFAULT 'taught',  -- taught(对话教) | ticket(工单补充)
                vector TEXT,                            -- 问题的向量(JSON list[float]),供 top-k 语义检索
                vec_model TEXT,                         -- 生成该向量的后端签名,后端切换时据此重算
                created_at TEXT NOT NULL DEFAULT (datetime('now','localtime'))
            )
            """
        )
        # 兼容旧库:老 playbook 表可能没有向量列,缺失则补上(不影响已有数据)
        existing_cols = {row["name"] for row in cur.execute("PRAGMA table_info(playbook)")}
        if "vector" not in existing_cols:
            cur.execute("ALTER TABLE playbook ADD COLUMN vector TEXT")
        if "vec_model" not in existing_cols:
            cur.execute("ALTER TABLE playbook ADD COLUMN vec_model TEXT")
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS metrics_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                question TEXT,
                hit_kb INTEGER NOT NULL DEFAULT 0,
                handoff INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT (datetime('now','localtime'))
            )
            """
        )
