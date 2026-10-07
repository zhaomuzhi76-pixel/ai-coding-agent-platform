from __future__ import annotations

from backend.persistence.contracts.project_persistence import (
    ProjectPersistenceContract,
)
from backend.storage.mongodb_client import MongoDBClient
from backend.workspace.project.project_descriptor import (
    ProjectDescriptor,
)
from backend.workspace.project.project_model import (
    ProjectModel,
)
from backend.workspace.project.project_state import (
    ProjectState,
)


class MongoProjectPersistence(
    ProjectPersistenceContract,
):
    VERSION = "1.0"
    COLLECTION = "projects"

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
        project: ProjectModel,
    ) -> None:
        if not isinstance(project, ProjectModel):
            raise TypeError(
                "project must ProjectModel"
            )
        document = {
            "project_id": project.project_id,
            "name": project.name,
            "root_path": project.root_path,
            "workspace_id": project.workspace_id,
            "state": project.state.value,
        }
        self.collection.replace_one(
            {"project_id": project.project_id},
            document,
            upsert=True,
        )

    async def get(
        self,
        project_id: str,
    ) -> ProjectModel | None:
        value = str(project_id).strip()
        if not value:
            raise ValueError(
                "project id required"
            )

        document = self.collection.find_one(
            {"project_id": value}
        )
        if document is None:
            return None

        project = ProjectModel(
            ProjectDescriptor(
                project_id=document["project_id"],
                name=document["name"],
                root_path=document["root_path"],
                workspace_id=document.get(
                    "workspace_id"
                ),
            )
        )
        project.state = ProjectState(
            document.get(
                "state",
                ProjectState.CREATED.value,
            )
        )
        return project

    async def list(
        self,
    ) -> tuple[ProjectModel, ...]:
        documents = self.collection.find(
            {},
            {
                "_id": 0,
                "project_id": 1,
                "name": 1,
                "root_path": 1,
                "workspace_id": 1,
                "state": 1,
            },
        )

        result = []
        for document in documents:
            project = await self.get(
                document["project_id"]
            )
            if project is not None:
                result.append(project)

        return tuple(result)

    async def delete(
        self,
        project_id: str,
    ) -> bool:
        value = str(project_id).strip()
        if not value:
            raise ValueError(
                "project id required"
            )

        result = self.collection.delete_one(
            {"project_id": value}
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
    "MongoProjectPersistence",
]
