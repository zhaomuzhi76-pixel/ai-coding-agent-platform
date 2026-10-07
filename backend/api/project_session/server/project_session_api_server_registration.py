from __future__ import annotations

from fastapi import FastAPI

from backend.api.project_session.project_session_api_factory import (
    ProjectSessionAPIFactory,
)
from backend.api.project_session.server.project_session_api_server_registration_contract import (
    ProjectSessionAPIServerRegistrationContract,
)
from backend.api.project_session.server.project_session_api_server_registration_context import (
    ProjectSessionAPIServerRegistrationContextMixin,
)
from backend.api.project_session.server.project_session_api_server_registration_diagnostics import (
    ProjectSessionAPIServerRegistrationDiagnosticsMixin,
)
from backend.api.project_session.server.project_session_api_server_registration_support import (
    ProjectSessionAPIServerRegistrationSupport,
)
from backend.application.project_session.project_session_adapter_contract import (
    ProjectSessionApplicationAdapterContract,
)
from backend.application.project_session.project_session_adapter_factory import (
    ProjectSessionApplicationAdapterFactory,
)
from backend.application.runtime_submission_contract import (
    ApplicationRuntimeSubmissionProtocol,
)


class ProjectSessionAPIServerRegistration(
    ProjectSessionAPIServerRegistrationContextMixin,
    ProjectSessionAPIServerRegistrationDiagnosticsMixin,
    ProjectSessionAPIServerRegistrationContract,
):
    """
    FastAPI registration boundary for the assembled
    project-session application contracts.
    """

    VERSION = "4.0"
    STATE_KEY = "project_session_api_server"

    def __init__(
        self,
        adapter_factory: ProjectSessionApplicationAdapterFactory | None = None,
        api_factory: ProjectSessionAPIFactory | None = None,
        support: ProjectSessionAPIServerRegistrationSupport | None = None,
    ) -> None:
        self.adapter_factory = (
            adapter_factory
            or ProjectSessionApplicationAdapterFactory()
        )
        self.api_factory = (
            api_factory
            or ProjectSessionAPIFactory()
        )
        self.support = (
            support
            or ProjectSessionAPIServerRegistrationSupport()
        )
        self.api = None
        self.router = None
        self.runtime_submission = None
        self._registered_routes: tuple[object, ...] = ()

    def register(
        self,
        app: object,
        startup: object,
    ) -> FastAPI:
        app = self.support.validate_app(app)
        self.unregister(app)

        context = self._startup_context(
            startup
        )

        adapter = context.get(
            "project_session_application_adapter"
        )
        runtime_submission = context.get(
            "runtime_submission"
        )

        if not isinstance(
            adapter,
            ProjectSessionApplicationAdapterContract,
        ):
            raise TypeError(
                "project session application adapter "
                "contract invalid"
            )

        if not adapter.ready():
            raise RuntimeError(
                "project session application adapter "
                "not ready"
            )

        if not isinstance(
            runtime_submission,
            ApplicationRuntimeSubmissionProtocol,
        ):
            raise TypeError(
                "runtime submission contract invalid"
            )

        if not runtime_submission.ready():
            raise RuntimeError(
                "runtime submission not ready"
            )

        api = self.api_factory.create_api(
            adapter=adapter,
            runtime_submission=runtime_submission,
        )

        router = self.api_factory.create_router(
            adapter=adapter,
            runtime_submission=runtime_submission,
        )

        self.support.validate_component(
            api,
            "project session api",
        )
        self.support.validate_component(
            router,
            "project session api router",
        )

        before = self.support.snapshot(
            app
        )

        app.include_router(
            router.router
        )

        added = self.support.route_delta(
            before,
            app,
        )

        if not added:
            raise RuntimeError(
                "project session api router "
                "registration produced no routes"
            )

        self.api = api
        self.router = router
        self.runtime_submission = runtime_submission
        self._registered_routes = added

        setattr(
            app.state,
            self.STATE_KEY,
            self,
        )

        return app

    def registered(
        self,
    ) -> bool:
        return (
            bool(self._registered_routes)
            and self.api is not None
            and self.router is not None
            and self.runtime_submission is not None
        )

    def unregister(
        self,
        app: object,
    ) -> None:
        app = self.support.validate_app(
            app
        )

        self.support.remove_routes(
            app,
            self._registered_routes,
        )

        current = getattr(
            app.state,
            self.STATE_KEY,
            None,
        )

        if current is self:
            delattr(
                app.state,
                self.STATE_KEY,
            )

        self._registered_routes = ()
        self.api = None
        self.router = None
        self.runtime_submission = None


__all__ = [
    "ProjectSessionAPIServerRegistration",
]
