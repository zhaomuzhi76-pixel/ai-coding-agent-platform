from __future__ import annotations

import json
import uuid

from pathlib import Path

from typing import (
    List,
    Dict,
    Any,
)

from backend.knowledge.schema import (
    KnowledgeItem,
)


class KnowledgeRepository:
    """
    JSON based knowledge repository.

    Responsibility:

        - save knowledge
        - load knowledge
        - search by type
        - delete knowledge
        - count knowledge

    Not Responsible:

        - knowledge analysis
        - learning decision
        - ranking
        - LLM calling
    """

    VERSION = "1.1"


    def __init__(
        self,
        storage_path: str = "data/knowledge_store.json",
    ) -> None:

        self.storage_path = Path(
            storage_path
        )

        self.storage_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        if not self.storage_path.exists():

            self.storage_path.write_text(
                "[]",
                encoding="utf-8",
            )


    def _load(
        self,
    ) -> List[Dict[str, Any]]:

        return json.loads(
            self.storage_path.read_text(
                encoding="utf-8"
            )
        )


    def _save(
        self,
        data: List[Dict[str, Any]],
    ) -> None:

        self.storage_path.write_text(
            json.dumps(
                data,
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )


    def save(
        self,
        item: KnowledgeItem,
    ) -> KnowledgeItem:

        data = self._load()

        if not item.item_id:

            item.item_id = str(
                uuid.uuid4()
            )

        data.append(
            item.dump()
        )

        self._save(
            data
        )

        return item


    def get_all(
        self,
    ) -> List[Dict[str, Any]]:

        return self._load()


    def find_by_type(
        self,
        knowledge_type: str,
    ) -> List[Dict[str, Any]]:

        return [

            item

            for item in self._load()

            if item.get(
                "knowledge_type"
            )
            == knowledge_type

        ]


    def delete(
        self,
        item_id: str,
    ) -> bool:

        data = self._load()

        result = [

            item

            for item in data

            if item.get(
                "item_id"
            )
            != item_id

        ]

        if len(result) == len(data):

            return False


        self._save(
            result
        )

        return True


    def count(
        self,
    ) -> int:

        return len(
            self._load()
        )


    def dump(
        self,
    ) -> dict:

        return {

            "name":
                "KnowledgeRepository",

            "version":
                self.VERSION,

            "storage":
                str(
                    self.storage_path
                ),

        }


__all__ = [
    "KnowledgeRepository",
]
