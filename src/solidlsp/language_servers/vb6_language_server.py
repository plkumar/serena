"""
Provides VB6 language support for SolidLSP via the vb6_parser LSP server.
"""

import logging
import os
import pathlib
import sys
import threading

from solidlsp.ls import (
    DocumentSymbols,
    LanguageServerDependencyProvider,
    LanguageServerDependencyProviderSinglePath,
    LSPFileBuffer,
    SolidLanguageServer,
)
from solidlsp.ls_config import LanguageServerConfig
from solidlsp.lsp_protocol_handler.lsp_types import InitializeParams
from solidlsp.settings import SolidLSPSettings

log = logging.getLogger(__name__)


class VB6LanguageServer(SolidLanguageServer):
    """SolidLSP wrapper for the VB6 language server (vb6_parser)."""

    def __init__(
        self,
        config: LanguageServerConfig,
        repository_root_path: str,
        solidlsp_settings: SolidLSPSettings,
    ):
        super().__init__(
            config,
            repository_root_path,
            None,
            "vb6",
            solidlsp_settings,
        )
        self.server_ready = threading.Event()

    def _create_dependency_provider(self) -> LanguageServerDependencyProvider:
        return self.DependencyProvider(self._custom_settings, self._ls_resources_dir)

    class DependencyProvider(LanguageServerDependencyProviderSinglePath):
        def _get_or_install_core_dependency(self) -> str:
            try:
                import vb6_parser  # noqa: F401
            except ImportError:
                raise RuntimeError(
                    "vb6_parser is not installed. Install it with: pip install vb6-parser"
                )
            return sys.executable

        def _create_launch_command(self, core_path: str) -> list[str]:
            return [core_path, "-m", "vb6_parser.lsp.server", "--stdio"]

    @staticmethod
    def _get_initialize_params(repository_absolute_path: str) -> InitializeParams:
        root_uri = pathlib.Path(repository_absolute_path).as_uri()
        return {  # type: ignore
            "processId": os.getpid(),
            "rootUri": root_uri,
            "rootPath": repository_absolute_path,
            "capabilities": {
                "textDocument": {
                    "documentSymbol": {
                        "dynamicRegistration": True,
                        "hierarchicalDocumentSymbolSupport": True,
                    },
                    "definition": {"dynamicRegistration": True},
                    "references": {"dynamicRegistration": True},
                },
                "workspace": {
                    "symbol": {"dynamicRegistration": True},
                },
            },
            "workspaceFolders": [
                {
                    "uri": root_uri,
                    "name": os.path.basename(repository_absolute_path),
                }
            ],
        }

    def _start_server(self) -> None:
        """Start the VB6 language server and wait for it to be ready."""

        def do_nothing(params: dict) -> None:
            return

        self.server.on_notification("textDocument/publishDiagnostics", do_nothing)
        self.server.on_notification("$/progress", do_nothing)

        log.info("Starting VB6 language server process")
        self.server.start()

        initialize_params = self._get_initialize_params(self.repository_root_path)
        log.info("Sending initialize request to VB6 language server")
        init_response = self.server.send.initialize(initialize_params)
        log.debug(f"VB6 server initialize response: {init_response}")

        assert "capabilities" in init_response, (
            f"VB6 language server did not return capabilities: {init_response}"
        )

        self.server.notify.initialized({})
        self.server_ready.set()
        log.info("VB6 language server ready")
