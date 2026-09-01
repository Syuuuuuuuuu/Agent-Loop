"""套路库(训练样本)服务。

一条训练样本 = 老师教的一次示范:客户问题 + 标准答案 + 这么答的原因(套路)。
服务时按客户当前问句做 embedding 语义检索,只召回最相关的 top-k 条样本交给
大模型精判并模仿作答 —— 库变大也不会撑爆上下文。总纲归纳仍取全量(recall_all)。
"""
from __future__ import annotations
import json
from typing import Any

from ..db import cursor
from ..knowledge import embedder


def add_sample(question: str, answer: str, note: str = "",
               source: str = "taught") -> int:
    vector, sig = embedder.embed(question)
    with cursor() as cur:
        cur.execute(
            "INSERT INTO playbook (question, answer, note, source, vector, vec_model) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (question, answer, note, source, json.dumps(vector), sig),
        )
        return cur.lastrowid


def list_samples() -> list[dict[str, Any]]:
    with cursor() as cur:
        cur.execute("SELECT * FROM playbook ORDER BY id DESC")
        return [dict(r) for r in cur.fetchall()]


def recall_all() -> list[dict[str, Any]]:
    """召回全部样本(供总纲归纳用,需要看到所有示范)。"""
    with cursor() as cur:
        cur.execute("SELECT id, question, answer, note FROM playbook ORDER BY id")
        return [dict(r) for r in cur.fetchall()]


def _sample_vector(row: dict[str, Any], sig: str) -> list[float]:
    """取样本问句向量;缺失或后端签名不一致(切了 embedding 后端)则重算并回写。"""
    if row.get("vector") and row.get("vec_model") == sig:
        try:
            return json.loads(row["vector"])
        except (json.JSONDecodeError, TypeError):
            pass
    vector, new_sig = embedder.embed(row["question"])
    with cursor() as cur:
        cur.execute("UPDATE playbook SET vector=?, vec_model=? WHERE id=?",
                    (json.dumps(vector), new_sig, row["id"]))
    return vector


def recall_topk(query: str, k: int) -> list[dict[str, Any]]:
    """按客户问句语义检索,返回最相关的 top-k 条样本(按相似度降序,带 score)。

    query 为空时退化为全量返回,避免空检索导致答不上。
    """
    with cursor() as cur:
        cur.execute("SELECT id, question, answer, note, vector, vec_model FROM playbook ORDER BY id")
        rows = [dict(r) for r in cur.fetchall()]
    if not rows:
        return []
    if not (query or "").strip():
        return [{"id": r["id"], "question": r["question"], "answer": r["answer"],
                 "note": r["note"]} for r in rows]

    sig = embedder.signature()
    qvec, _ = embedder.embed(query)
    scored = []
    for r in rows:
        score = embedder.cosine(qvec, _sample_vector(r, sig))
        scored.append((score, r))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [{"id": r["id"], "question": r["question"], "answer": r["answer"],
             "note": r["note"], "score": round(score, 3)}
            for score, r in scored[:k]]


def update_sample(sample_id: int, question: str, answer: str, note: str) -> dict[str, Any]:
    vector, sig = embedder.embed(question)
    with cursor() as cur:
        cur.execute(
            "UPDATE playbook SET question=?, answer=?, note=?, vector=?, vec_model=? WHERE id=?",
            (question, answer, note, json.dumps(vector), sig, sample_id),
        )
    return {"ok": True}


def delete_sample(sample_id: int) -> dict[str, Any]:
    with cursor() as cur:
        cur.execute("DELETE FROM playbook WHERE id=?", (sample_id,))
    return {"ok": True}


def count() -> int:
    with cursor() as cur:
        cur.execute("SELECT COUNT(*) AS c FROM playbook")
        return cur.fetchone()["c"]
