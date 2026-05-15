"""Basic integration tests for the VB6 language server."""

import pytest

from solidlsp import SolidLanguageServer
from solidlsp.ls_config import Language


@pytest.mark.vb6
class TestVB6LanguageServerBasics:
    """Test basic functionality of the VB6 language server."""

    @pytest.mark.parametrize("language_server", [Language.VB6], indirect=True)
    def test_vb6_language_server_initialization(self, language_server: SolidLanguageServer) -> None:
        assert language_server is not None
        assert language_server.language == Language.VB6

    @pytest.mark.parametrize("language_server", [Language.VB6], indirect=True)
    def test_document_symbols_contains_add(self, language_server: SolidLanguageServer) -> None:
        all_symbols, _roots = language_server.request_document_symbols("MathUtils.bas").get_all_symbols_and_roots()
        names = [s["name"] for s in all_symbols]
        assert "Add" in names, f"Expected 'Add' in symbols, got: {names}"

    @pytest.mark.parametrize("language_server", [Language.VB6], indirect=True)
    def test_workspace_symbol_tree_includes_math_utils(self, language_server: SolidLanguageServer) -> None:
        tree = language_server.request_full_symbol_tree()
        all_names = []

        def collect(syms):
            for s in syms:
                all_names.append(s["name"])
                collect(s.get("children", []))

        collect(tree)
        assert any("Add" in n or "MathUtils" in n for n in all_names), (
            f"Expected 'Add' or 'MathUtils' in symbol tree, got: {all_names}"
        )

    @pytest.mark.parametrize("language_server", [Language.VB6], indirect=True)
    def test_definition_resolves_add_call(self, language_server: SolidLanguageServer) -> None:
        # OrderService.bas line 5 (0-based line 4): "    Call Add(1.0, 2.0)"
        # character 9 is inside "Add"
        locations = language_server.request_definition("OrderService.bas", line=4, column=9)
        assert len(locations) >= 1, f"Expected at least 1 definition location, got: {locations}"
        location_paths = [str(loc) for loc in locations]
        assert any("MathUtils" in p for p in location_paths), (
            f"Expected definition to point to MathUtils.bas, got: {location_paths}"
        )
