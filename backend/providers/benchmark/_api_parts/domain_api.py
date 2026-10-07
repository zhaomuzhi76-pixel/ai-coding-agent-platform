"""领域能力汇总 API 片段"""
from fastapi.responses import JSONResponse

from ..domains import domain_list


class _DomainMixin:
    async def list_domains(self) -> JSONResponse:
        try:
            return self._ok({"domains": domain_list()})
        except Exception as exc:
            return self._err(exc)
