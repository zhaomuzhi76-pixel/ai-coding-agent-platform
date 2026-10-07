from __future__ import annotations

from backend.application.project.project_registration_contract import (
    ApplicationProjectRegistrationContract,
    ProjectModelFactoryProtocol,
)
from backend.workspace.project.registry.project_registry_contract import (
    ProjectRegistryContract,
)


class ApplicationProjectRegistration(
    ApplicationProjectRegistrationContract,
):
    """
    Application project-registration boundary.

    工业级幂等契约：
      - find_by_root 命中 → 返回已有
      - 注册竞态（并发/恢复期）→ 兜底重查 → 返回已有
      - 只有真正失败才向上抛

    Project model construction is injected from assembly root.
    """

    VERSION = "2.1"

    def __init__(
        self,
        project_registry: ProjectRegistryContract,
        project_factory: ProjectModelFactoryProtocol,
    ) -> None:
        if not isinstance(
            project_registry,
            ProjectRegistryContract,
        ):
            raise TypeError(
                "project registry contract required"
            )

        if not isinstance(
            project_factory,
            ProjectModelFactoryProtocol,
        ):
            raise TypeError(
                "project model factory contract required"
            )

        if not project_registry.ready():
            raise RuntimeError(
                "project registry not ready"
            )

        if not project_factory.ready():
            raise RuntimeError(
                "project model factory not ready"
            )

        self.project_registry = project_registry
        self.project_factory = project_factory
        self.register_count = 0
        self.reuse_count = 0
        self.remove_count = 0

    def register(
        self,
        name: str,
        root_path: str,
        project_id: str | None = None,
        workspace_id: str | None = None,
    ) -> object:
        # ── 快路径：root 已存在 → 复用 ──
        existing = self.project_registry.find_by_root(
            root_path
        )
        if existing is not None:
            self.reuse_count += 1
            return existing

        project = self.project_factory.create(
            name=name,
            root_path=root_path,
            project_id=project_id,
            workspace_id=workspace_id,
        )

        try:
            self.project_registry.register(project)
        except ValueError as exc:
            # ── 慢路径：竞态兜底 ──
            # 并发调用 / 恢复期并行注册时，
            # 另一个调用可能已抢先注册了同一 root。
            # 工业级契约：幂等，不向上抛。
            if "already registered" not in str(exc):
                raise
            existing = self.project_registry.find_by_root(
                root_path
            )
            if existing is None:
                # 真异常，无法恢复
                raise
            self.reuse_count += 1
            return existing

        self.register_count += 1
        return project

    def get(
        self,
        project_id: str,
    ) -> object:
        return self.project_registry.get(
            project_id
        )

    def contains(
        self,
        project_id: str,
    ) -> bool:
        return self.project_registry.contains(
            project_id
        )

    def remove(
        self,
        project_id: str,
    ) -> object:
        project = self.project_registry.remove(
            project_id
        )
        self.remove_count += 1
        return project

    def ready(self) -> bool:
        return (
            isinstance(
                self.project_registry,
                ProjectRegistryContract,
            )
            and self.project_registry.ready()
            and self.project_factory.ready()
        )

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "register_count": self.register_count,
            "reuse_count": self.reuse_count,
            "remove_count": self.remove_count,
            "project_factory": type(
                self.project_factory
            ).__name__,
        }


__all__ = [
    "ApplicationProjectRegistration",
]
