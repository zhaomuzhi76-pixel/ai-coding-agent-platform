from __future__ import annotations

import asyncio
import threading
from typing import Awaitable, TypeVar


T = TypeVar("T")


class PersistenceSyncBridge:
    VERSION = "1.0"

    def run(
        self,
        operation: Awaitable[T],
    ) -> T:
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(operation)

        result: list[T] = []
        error: list[BaseException] = []

        def worker() -> None:
            try:
                result.append(
                    asyncio.run(operation)
                )
            except BaseException as exc:
                error.append(exc)

        thread = threading.Thread(
            target=worker,
            daemon=True,
        )
        thread.start()
        thread.join()

        if error:
            raise error[0]

        if not result:
            raise RuntimeError(
                "persistence operation produced no result"
            )

        return result[0]

    def ready(self) -> bool:
        return True

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
        }


__all__ = [
    "PersistenceSyncBridge",
]
