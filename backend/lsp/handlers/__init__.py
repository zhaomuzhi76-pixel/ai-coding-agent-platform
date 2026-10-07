"""LSP method handlers."""
from backend.lsp.handlers.completion import handle_completion
from backend.lsp.handlers.hover import handle_hover
from backend.lsp.handlers.diagnostics import handle_diagnostics

__all__ = ["handle_completion", "handle_hover", "handle_diagnostics"]
