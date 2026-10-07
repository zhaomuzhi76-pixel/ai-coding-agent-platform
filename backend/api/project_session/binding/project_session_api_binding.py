from __future__ import annotations

from backend.api.project_session.project_session_api import (
    ProjectSessionAPI,
)
from backend.api.project_session.project_session_api_factory import (
    ProjectSessionAPIFactory,
)
from backend.api.project_session.project_session_api_router import (
    ProjectSessionAPIRouter,
)
from backend.api.project_session.binding.project_session_api_binding_contract import (
    ProjectSessionAPIBindingContract,
)
from backend.application.project_session.project_session_adapter_contract import (
    ProjectSessionApplicationAdapterContract,
)
from backend.application.runtime_submission_contract import (
    ApplicationRuntimeSubmissionProtocol,
)


class ProjectSessionAPIBinding(
    ProjectSessionAPIBindingContract,
):
    """
    API/application project-session dependency binding.

    Receives already assembled application contracts.
    """

    VERSION = "2.0"

    def __init__(
        self,
        adapter: ProjectSessionApplicationAdapterContract,
        runtime_submission: ApplicationRuntimeSubmissionProtocol,
        api_factory: ProjectSessionAPIFactory,
    ) -> None:
        if not isinstance(
            adapter,
            ProjectSessionApplicationAdapterContract,
        ):
            raise TypeError(
                "adapter must "
                "ProjectSessionApplicationAdapterContract"
            )

        if not adapter.ready():
            raise RuntimeError(
                "project session application adapter not ready"
            )

        if not isinstance(
            runtime_submission,
            ApplicationRuntimeSubmissionProtocol,
        ):
            raise TypeError(
                "runtime submission contract required"
            )

        if not runtime_submission.ready():
            raise RuntimeError(
                "runtime submission not ready"
            )

        if not isinstance(
            api_factory,
            ProjectSessionAPIFactory,
        ):
            raise TypeError(
                "api_factory must ProjectSessionAPIFactory"
            )

        self._adapter = adapter
        self._runtime_submission = runtime_submission
        self._api_factory = api_factory
        self._api: ProjectSessionAPI | None = None
        self._router: ProjectSessionAPIRouter | None = None

    def build(
        self,
    ) -> dict[str, object]:
        if not self.ready():
            raise RuntimeError(
                "project session API binding unavailable"
            )

        try:
            api = self._api_factory.create_api(
                adapter=self._adapter,
                runtime_submission=self._runtime_submission,
            )

            router = ProjectSessionAPIRouter(
                api
            )

            if not router.ready():
                raise RuntimeError(
                    "project session API router unavailable"
                )

            self._api = api
            self._router = router

            return {
                "adapter": self._adapter,
                "runtime_submission":
                    self._runtime_submission,
                "api": self._api,
                "router": self._router,
            }

        except Exception:
            self.close()
            raise

    def api(
        self,
    ) -> ProjectSessionAPI:
        self._require_built()
        return self._api

    def router(
        self,
    ) -> ProjectSessionAPIRouter:
        self._require_built()
        return self._router

    def adapter(
        self,
    ) -> ProjectSessionApplicationAdapterContract:
        return self._adapter

    def runtime_submission(
        self,
    ) -> ApplicationRuntimeSubmissionProtocol:
        return self._runtime_submission

    def close(
        self,
    ) -> None:
        self._api = None
        self._router = None

    def ready(
        self,
    ) -> bool:
        return (
            self._adapter.ready()
            and self._runtime_submission.ready()
            and self._api_factory.ready()
            and (
                self._api is None
                and self._router is None
                or (
                    self._api is not None
                    and self._router is not None
                    and self._api.ready()
                    and self._router.ready()
                )
            )
        )

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "built": (
                self._api is not None
                and self._router is not None
            ),
            "adapter": type(
                self._adapter
            ).__name__,
            "runtime_submission": type(
                self._runtime_submission
            ).__name__,
            "api": (
                type(self._api).__name__
                if self._api is not None
                else None
            ),
            "router": (
                type(self._router).__name__
                if self._router is not None
                else None
            ),
        }

    def _require_built(
        self,
    ) -> None:
        if (
            self._api is None
            or self._router is None
        ):
            raise RuntimeError(
                "project session API binding not built"
            )


__all__ = [
    "ProjectSessionAPIBinding",
]
