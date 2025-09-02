#!/usr/bin/env python3
"""
Unit tests for Phase 2: Symbol Origin Tracking functionality.

Tests focused, non-overlapping functionality:
1. test_symbol_definition_detection - LSP definition detection
2. test_reference_identification - Reference marking
3. test_inheritance_chain_tracking - Parent class detection
4. test_origin_signature_generation - Unique signature creation
5. test_metadata_persistence - ChromaDB storage/retrieval

Each test has a single, specific purpose without overlap.
"""

import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

# Setup import paths
try:
    from utils import path_resolver  # noqa: F401
    from ci.integration.symbol_extractor import Symbol, SymbolType
    from ci.core.lsp_symbol_extractor import LSPSymbolExtractor, SymbolExtractionConfig
    from ci.core.chromadb_storage import ChromaDBStorage, ChromaDBConfig
except ImportError as e:
    print(f"Import error: {e}", file=sys.stderr)
    sys.exit(1)


class TestSymbolDefinitionDetection(unittest.TestCase):
    """Test LSP correctly identifies original definitions."""

    def setUp(self):
        """Set up test fixtures."""
        self.config = SymbolExtractionConfig(enable_origin_tracking=True)
        self.extractor = LSPSymbolExtractor(self.config, str(Path.cwd()))

    def test_definition_location_detection(self):
        """Test _get_symbol_definition correctly identifies definition location."""
        # Create mock symbol
        symbol = Symbol(
            name="test_function",
            symbol_type=SymbolType.FUNCTION,
            file_path="test.py",
            line_number=10,
            line_content="def test_function():",
            scope="module",
        )

        # Mock LSP server response for definition
        mock_server = Mock()
        mock_definition_response = (
            [
                {
                    "uri": "file:///path/to/source.py",
                    "range": {
                        "start": {"line": 5, "character": 0},
                        "end": {"line": 5, "character": 10},
                    },
                }
            ],
        )
        mock_server.request_definition.return_value = mock_definition_response

        # Test definition detection
        result = self.extractor._get_symbol_definition(mock_server, symbol, "test.py")

        # Verify results
        self.assertIsNotNone(result)
        self.assertEqual(result["definition_file"], "/path/to/source.py")
        self.assertEqual(result["definition_line"], 6)  # LSP 0-based -> 1-based

    def test_no_definition_found(self):
        """Test handling when no definition is found."""
        symbol = Symbol(
            name="undefined_symbol",
            symbol_type=SymbolType.VARIABLE,
            file_path="test.py",
            line_number=5,
            line_content="undefined_symbol = 42",
            scope="module",
        )

        mock_server = Mock()
        mock_server.request_definition.return_value = ([],)  # Empty response

        result = self.extractor._get_symbol_definition(mock_server, symbol, "test.py")

        self.assertIsNone(result)


class TestReferenceIdentification(unittest.TestCase):
    """Test references are correctly marked as is_reference=True."""

    def setUp(self):
        """Set up test fixtures."""
        self.config = SymbolExtractionConfig(enable_origin_tracking=True)
        self.extractor = LSPSymbolExtractor(self.config, str(Path.cwd()))

    def test_import_reference_detection(self):
        """Test import symbols are marked as references."""
        symbol = Symbol(
            name="imported_module",
            symbol_type=SymbolType.IMPORT,
            file_path="test.py",
            line_number=1,
            line_content="import imported_module",
            scope="module",
            is_import=True,
        )

        # Mock LSP server to return different definition location
        mock_server = Mock()
        mock_definition_response = (
            [
                {
                    "uri": "file:///different/path/imported_module.py",
                    "range": {
                        "start": {"line": 0, "character": 0},
                        "end": {"line": 0, "character": 10},
                    },
                }
            ],
        )
        mock_server.request_definition.return_value = mock_definition_response
        mock_server.request_references.return_value = ([],)

        # Test origin determination
        origin_info = self.extractor._determine_symbol_origin(
            symbol, mock_server, "test.py"
        )

        # Verify reference is detected
        self.assertTrue(origin_info["is_reference"])
        self.assertFalse(origin_info["is_definition"])

    def test_type_annotation_reference_detection(self):
        """Test type annotation symbols are identified as references."""
        symbol = Symbol(
            name="CustomType",
            symbol_type=SymbolType.TYPE,
            file_path="usage.py",
            line_number=5,
            line_content="def func(param: CustomType) -> None:",
            scope="module",
        )

        mock_server = Mock()
        # Different file for definition indicates reference
        mock_definition_response = (
            [
                {
                    "uri": "file:///path/to/types.py",
                    "range": {
                        "start": {"line": 10, "character": 0},
                        "end": {"line": 10, "character": 10},
                    },
                }
            ],
        )
        mock_server.request_definition.return_value = mock_definition_response
        mock_server.request_references.return_value = ([],)

        origin_info = self.extractor._determine_symbol_origin(
            symbol, mock_server, "usage.py"
        )

        self.assertTrue(origin_info["is_reference"])

    def test_local_definition_not_reference(self):
        """Test symbols defined locally are not marked as references."""
        symbol = Symbol(
            name="local_function",
            symbol_type=SymbolType.FUNCTION,
            file_path="/absolute/path/test.py",
            line_number=10,
            line_content="def local_function():",
            scope="module",
        )

        mock_server = Mock()
        # Same file and line indicates definition
        mock_definition_response = (
            [
                {
                    "uri": "file:///absolute/path/test.py",
                    "range": {
                        "start": {"line": 9, "character": 0},  # LSP is 0-based
                        "end": {"line": 9, "character": 10},
                    },
                }
            ],
        )
        mock_server.request_definition.return_value = mock_definition_response
        mock_server.request_references.return_value = ([],)

        origin_info = self.extractor._determine_symbol_origin(
            symbol, mock_server, "test.py"
        )

        self.assertFalse(origin_info["is_reference"])
        self.assertTrue(origin_info["is_definition"])


class TestInheritanceChainTracking(unittest.TestCase):
    """Test parent_class field is correctly populated."""

    def setUp(self):
        """Set up test fixtures."""
        self.config = SymbolExtractionConfig(
            enable_origin_tracking=True, enable_inheritance_detection=True
        )
        self.extractor = LSPSymbolExtractor(self.config, str(Path.cwd()))

    def test_method_parent_class_detection(self):
        """Test methods inherit parent class information."""
        symbol = Symbol(
            name="inherited_method",
            symbol_type=SymbolType.METHOD,
            file_path="child.py",
            line_number=15,
            line_content="def inherited_method(self):",
            scope="class",
        )

        mock_server = Mock()
        # Mock definition in parent class
        mock_definition_response = (
            [
                {
                    "uri": "file:///path/to/parent.py",
                    "range": {
                        "start": {"line": 5, "character": 4},
                        "end": {"line": 5, "character": 20},
                    },
                }
            ],
        )
        mock_server.request_definition.return_value = mock_definition_response
        mock_server.request_references.return_value = ([],)

        with patch.object(
            self.extractor, "_detect_parent_class", return_value="BaseClass"
        ):
            origin_info = self.extractor._determine_symbol_origin(
                symbol, mock_server, "child.py"
            )

        self.assertEqual(origin_info["parent_class"], "BaseClass")
        # Origin signature should include parent class
        self.assertIn("BaseClass::", origin_info["origin_signature"])

    def test_no_parent_class_for_functions(self):
        """Test functions don't get parent class information."""
        symbol = Symbol(
            name="standalone_function",
            symbol_type=SymbolType.FUNCTION,
            file_path="module.py",
            line_number=20,
            line_content="def standalone_function():",
            scope="module",
        )

        mock_server = Mock()
        mock_definition_response = ([],)  # No definition
        mock_server.request_definition.return_value = mock_definition_response
        mock_server.request_references.return_value = ([],)

        origin_info = self.extractor._determine_symbol_origin(
            symbol, mock_server, "module.py"
        )

        self.assertIsNone(origin_info["parent_class"])
        self.assertNotIn("::", origin_info["origin_signature"])


class TestOriginSignatureGeneration(unittest.TestCase):
    """Test unique signatures are generated for same-origin symbols."""

    def setUp(self):
        """Set up test fixtures."""
        self.config = SymbolExtractionConfig(enable_origin_tracking=True)
        self.extractor = LSPSymbolExtractor(self.config, str(Path.cwd()))

    def test_unique_signatures_for_same_definition(self):
        """Test symbols from same definition get identical signatures."""
        symbol1 = Symbol(
            name="shared_function",
            symbol_type=SymbolType.FUNCTION,
            file_path="usage1.py",
            line_number=10,
            line_content="def shared_function():",
            scope="module",
        )

        symbol2 = Symbol(
            name="shared_function",
            symbol_type=SymbolType.FUNCTION,
            file_path="usage2.py",
            line_number=20,
            line_content="shared_function()",
            scope="module",
        )

        # Mock same definition location for both
        origin_info1 = {
            "definition_file": "/path/to/source.py",
            "definition_line": 5,
            "import_source": None,
        }

        origin_info2 = {
            "definition_file": "/path/to/source.py",
            "definition_line": 5,
            "import_source": None,
        }

        sig1 = self.extractor._generate_origin_signature(symbol1, origin_info1)
        sig2 = self.extractor._generate_origin_signature(symbol2, origin_info2)

        self.assertEqual(sig1, sig2)

    def test_different_signatures_for_different_definitions(self):
        """Test symbols from different definitions get unique signatures."""
        symbol1 = Symbol(
            name="function_a",
            symbol_type=SymbolType.FUNCTION,
            file_path="file1.py",
            line_number=10,
            line_content="def function_a():",
            scope="module",
        )

        symbol2 = Symbol(
            name="function_b",
            symbol_type=SymbolType.FUNCTION,
            file_path="file2.py",
            line_number=20,
            line_content="def function_b():",
            scope="module",
        )

        origin_info1 = {
            "definition_file": "/path/to/file1.py",
            "definition_line": 10,
            "import_source": None,
        }

        origin_info2 = {
            "definition_file": "/path/to/file2.py",
            "definition_line": 20,
            "import_source": None,
        }

        sig1 = self.extractor._generate_origin_signature(symbol1, origin_info1)
        sig2 = self.extractor._generate_origin_signature(symbol2, origin_info2)

        self.assertNotEqual(sig1, sig2)

    def test_import_source_in_signature(self):
        """Test import source is included in signature."""
        symbol = Symbol(
            name="imported_function",
            symbol_type=SymbolType.FUNCTION,
            file_path="usage.py",
            line_number=5,
            line_content="from mymodule import imported_function",
            scope="module",
        )

        origin_info = {
            "definition_file": "/path/to/mymodule.py",
            "definition_line": 15,
            "import_source": "mymodule",
        }

        signature = self.extractor._generate_origin_signature(symbol, origin_info)

        self.assertIn("import:mymodule", signature)


class TestMetadataPersistence(unittest.TestCase):
    """Test ChromaDB correctly stores and retrieves origin fields."""

    def setUp(self):
        """Set up test fixtures."""
        self.config = ChromaDBConfig()
        # Use in-memory storage for testing
        self.config.persist_directory = Path("/tmp/test_chromadb")

    @patch("ci.core.chromadb_storage.chromadb")
    def test_origin_metadata_storage(self, mock_chromadb):
        """Test origin tracking metadata is stored in ChromaDB."""
        # Mock ChromaDB client and collection
        mock_client = Mock()
        mock_collection = Mock()
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_chromadb.PersistentClient.return_value = mock_client

        storage = ChromaDBStorage(self.config)

        # Create symbol with origin tracking information
        symbol = Symbol(
            name="test_symbol",
            symbol_type=SymbolType.FUNCTION,
            file_path="test.py",
            line_number=10,
            line_content="def test_symbol():",
            scope="module",
        )

        # Add origin tracking fields
        symbol.definition_file = "/path/to/source.py"
        symbol.definition_line = 5
        symbol.is_reference = True
        symbol.is_definition = False
        symbol.parent_class = "BaseClass"
        symbol.import_source = "mymodule"
        symbol.origin_signature = "source.py::5::function::test_symbol"
        symbol.reference_count = 3

        # Test metadata extraction
        metadata = storage._extract_metadata(symbol)

        # Verify origin tracking fields are included
        self.assertEqual(metadata["definition_file"], "/path/to/source.py")
        self.assertEqual(metadata["definition_line"], 5)
        self.assertTrue(metadata["is_reference"])
        self.assertFalse(metadata["is_definition"])
        self.assertEqual(metadata["parent_class"], "BaseClass")
        self.assertEqual(metadata["import_source"], "mymodule")
        self.assertEqual(
            metadata["origin_signature"], "source.py::5::function::test_symbol"
        )
        self.assertEqual(metadata["reference_count"], 3)

    @patch("ci.core.chromadb_storage.chromadb")
    def test_origin_metadata_retrieval(self, mock_chromadb):
        """Test origin tracking metadata is correctly restored from ChromaDB."""
        # Mock ChromaDB client and collection
        mock_client = Mock()
        mock_collection = Mock()
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_chromadb.PersistentClient.return_value = mock_client

        storage = ChromaDBStorage(self.config)

        # Mock metadata with origin tracking information
        metadata = {
            "symbol_name": "test_symbol",
            "symbol_type": "function",
            "file_path": "test.py",
            "line_number": 10,
            "scope": "module",
            "parameters": "",
            "return_type": "",
            "line_count": 1,
            "lsp_kind": "12",
            # Origin tracking fields
            "definition_file": "/path/to/source.py",
            "definition_line": 5,
            "is_reference": True,
            "is_definition": False,
            "parent_class": "BaseClass",
            "import_source": "mymodule",
            "origin_signature": "source.py::5::function::test_symbol",
            "reference_count": 3,
        }

        # Test symbol reconstruction
        symbol = storage._metadata_to_symbol(metadata)

        # Verify origin tracking fields are restored
        self.assertEqual(symbol.definition_file, "/path/to/source.py")
        self.assertEqual(symbol.definition_line, 5)
        self.assertTrue(symbol.is_reference)
        self.assertFalse(symbol.is_definition)
        self.assertEqual(symbol.parent_class, "BaseClass")
        self.assertEqual(symbol.import_source, "mymodule")
        self.assertEqual(symbol.origin_signature, "source.py::5::function::test_symbol")
        self.assertEqual(symbol.reference_count, 3)

    @patch("ci.core.chromadb_storage.chromadb")
    def test_backward_compatibility_without_origin_fields(self, mock_chromadb):
        """Test symbols without origin tracking fields are handled gracefully."""
        # Mock ChromaDB client and collection
        mock_client = Mock()
        mock_collection = Mock()
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_chromadb.PersistentClient.return_value = mock_client

        storage = ChromaDBStorage(self.config)

        # Mock metadata without origin tracking fields (backward compatibility)
        metadata = {
            "symbol_name": "legacy_symbol",
            "symbol_type": "function",
            "file_path": "legacy.py",
            "line_number": 15,
            "scope": "module",
            "parameters": "",
            "return_type": "",
            "line_count": 1,
            "lsp_kind": "12"
            # No origin tracking fields
        }

        # Test symbol reconstruction works without origin fields
        symbol = storage._metadata_to_symbol(metadata)

        # Verify default values are used
        self.assertIsNone(symbol.definition_file)
        self.assertIsNone(symbol.definition_line)
        self.assertFalse(symbol.is_reference)
        self.assertTrue(symbol.is_definition)
        self.assertIsNone(symbol.parent_class)
        self.assertIsNone(symbol.import_source)
        self.assertIsNone(symbol.origin_signature)
        self.assertEqual(symbol.reference_count, 0)


if __name__ == "__main__":
    unittest.main()
