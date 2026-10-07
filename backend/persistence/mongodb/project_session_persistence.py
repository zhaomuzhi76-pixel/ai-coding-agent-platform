from __future__ import annotations

from backend.persistence.contracts.project_session_persistence import (
    ProjectSessionPersistenceContract,
)
from backend.storage.mongodb_client import MongoDBClient
from backend.workspace.project.session.project_session_descriptor import (
    ProjectSessionDescriptor,
)
from backend.workspace.project.session.project_session_model import (
    ProjectSessionModel,
)
from backend.workspace.project.session.project_session_state import (
    ProjectSessionState,
)


class MongoProjectSessionPersistence(
    ProjectSessionPersistenceContract,
):
    VERSION = "1.0"
    COLLECTION = "project_sessions"

    def __init__(
        self,
        client: MongoDBClient,
    ) -> None:
        if not isinstance(client, MongoDBClient):
            raise TypeError(
                "client must MongoDBClient"
            )
        self.client = client

    @property
    def collection(self):
        return self.client.database[
            self.COLLECTION
        ]

    async def save(
        self,
        session: object,
    ) -> None:
        if not hasattr(
            session,
            "session_id",
        ):
            raise TypeError(
                "project session required"
            )

        document = {
            "session_id": session.session_id,
            "project_id": session.project_id,
            "workspace_id": session.workspace_id,
            "runtime_id": session.runtime_id,
            "root_path": session.root_path,
            "metadata": dict(
                session.metadata
            ),
            "state": session.status,
        }

        self.collection.replace_one(
            {
                "session_id":
                    session.session_id,
            },
            document,
            upsert=True,
        )

    async def get(
        self,
        session_id: str,
    ) -> ProjectSessionModel | None:
        value = str(session_id).strip()
        if not value:
            raise ValueError(
                "session id required"
            )

        document = self.collection.find_one(
            {"session_id": value}
        )
        if document is None:
            return None

        session = ProjectSessionModel(
            ProjectSessionDescriptor(
                session_id=document["session_id"],
                project_id=document["project_id"],
                workspace_id=document.get(
                    "workspace_id"
                ),
                runtime_id=document.get(
                    "runtime_id"
                ),
                root_path=document["root_path"],
                metadata=dict(
                    document.get(
                        "metadata",
                        {},
                    )
                ),
            )
        )

        state = ProjectSessionState(
            document.get(
                "state",
                ProjectSessionState.CREATED.value,
            )
        )
        session.state = state
        return session

    async def list(
        self,
    ) -> tuple[ProjectSessionModel, ...]:
        result = []

        for document in self.collection.find(
            {},
            {
                "_id": 0,
                "session_id": 1,
            },
        ):
            session = await self.get(
                document["session_id"]
            )
            if session is not None:
                result.append(session)

        return tuple(result)

    async def delete(
        self,
        session_id: str,
    ) -> bool:
        value = str(session_id).strip()
        if not value:
            raise ValueError(
                "session id required"
            )

        result = self.collection.delete_one(
            {"session_id": value}
        )
        return result.deleted_count > 0

    def ready(self) -> bool:
        return (
            self.client is not None
            and bool(self.COLLECTION)
        )

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "collection": self.COLLECTION,
            "ready": self.ready(),
        }


__all__ = [
    "MongoProjectSessionPersistence",
]
