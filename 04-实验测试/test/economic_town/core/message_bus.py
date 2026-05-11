"""Agent 间消息总线（同步拉取为主，保证仿真确定性）"""
from __future__ import annotations
from collections import defaultdict
from typing import Callable, Optional
from core.messages import Message


class MessageBus:
    """
    发布/订阅消息总线。
    - 发布者调用 publish() 存入消息历史
    - 消费者调用 get_latest() 拉取最新消息（主模式）
    - 也支持 subscribe() 注册回调（辅助模式）
    所有消息按 topic → list[Message] 存储，完整保留历史。
    """

    def __init__(self):
        self._history: dict[str, list[Message]] = defaultdict(list)
        self._subscribers: dict[str, list[Callable[[Message], None]]] = defaultdict(list)

    # ── 发布 ──────────────────────────────────────────────────
    def publish(self, msg: Message) -> None:
        self._history[msg.topic].append(msg)
        for cb in self._subscribers.get(msg.topic, []):
            cb(msg)

    # ── 订阅（可选，回调式）───────────────────────────────────
    def subscribe(self, topic: str, callback: Callable[[Message], None]) -> None:
        self._subscribers[topic].append(callback)

    # ── 拉取 ──────────────────────────────────────────────────
    def get_latest(self, topic: str) -> Optional[Message]:
        msgs = self._history.get(topic)
        return msgs[-1] if msgs else None

    def get_history(self, topic: str, n: int = 5) -> list[Message]:
        msgs = self._history.get(topic, [])
        return msgs[-n:]

    def get_by_month(self, topic: str, month: int) -> Optional[Message]:
        for msg in reversed(self._history.get(topic, [])):
            if msg.month == month:
                return msg
        return None

    def get_all_by_sender(self, sender: str) -> list[Message]:
        result = []
        for msgs in self._history.values():
            result.extend(m for m in msgs if m.sender == sender)
        return sorted(result, key=lambda m: m.month)

    def topics(self) -> list[str]:
        return list(self._history.keys())

    def count(self, topic: str) -> int:
        return len(self._history.get(topic, []))

    def clear(self) -> None:
        self._history.clear()
        self._subscribers.clear()
