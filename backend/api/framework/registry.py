from __future__ import annotations

from backend.api.framework.contracts import (
    APITransportProtocol,
)


class APITransportRegistry:
    """
    API transport registration boundary.

    Owns transport identity and lookup only.
    """

    VERSION = "2.0"

    def __init__(self) -> None:
        self._transports: dict[
            str,
            APITransportProtocol,
        ] = {}

    def register(
        self,
        transport: APITransportProtocol,
    ) -> None:
        if not isinstance(
            transport,
            APITransportProtocol,
        ):
            raise TypeError(
                "invalid API transport"
            )

        if not transport.name:
            raise ValueError(
                "API transport name required"
            )

        if transport.name in self._transports:
            raise ValueError(
                "API transport already exists: "
                f"{transport.name}"
            )

        self._transports[
            transport.name
        ] = transport

    def resolve(
        self,
        name: str,
    ) -> APITransportProtocol:
        if not name:
            raise ValueError(
                "API transport name required"
            )

        try:
            return self._transports[name]
        except KeyError as error:
            raise LookupError(
                f"API transport not found: {name}"
            ) from error

    def exists(
        self,
        name: str,
    ) -> bool:
        return name in self._transports

    def names(
        self,
    ) -> tuple[str, ...]:
        return tuple(self._transports)

    def ready(self) -> bool:
        return all(
            transport.ready()
            for transport in self._transports.values()
        )

    def dump(self) -> dict[str, object]:
        return {
            "name": self.__class__.__name__,
            "version": self.VERSION,
            "transports": self.names(),
            "ready": self.ready(),
        }


__all__ = [
    "APITransportRegistry",
]
