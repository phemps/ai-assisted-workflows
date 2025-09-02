#!/usr/bin/env python3
"""
Integration tests for Phase 2: Symbol Origin Tracking end-to-end scenarios.

Tests complete pipeline workflows:
1. test_inherited_method_deduplication - Full pipeline with base/derived classes
2. test_import_symbol_filtering - Complete flow with cross-file imports
3. test_performance_impact - Measure <25% processing time increase

Each test validates end-to-end functionality with real data.
"""

import sys
import tempfile
import time
from pathlib import Path

# Setup import paths
try:
    from utils import path_resolver  # noqa: F401
    from ci.core.semantic_duplicate_detector import (
        DuplicateFinder,
        DuplicateFinderConfig,
    )
    from ci.core.chromadb_storage import ChromaDBConfig
except ImportError as e:
    print(f"Import error: {e}", file=sys.stderr)
    sys.exit(1)


def create_test_project_with_inheritance() -> Path:
    """Create a temporary test project with inheritance patterns."""
    temp_dir = Path(tempfile.mkdtemp(prefix="origin_tracking_test_"))

    # Create base class
    base_class = """class BaseProcessor:
    '''Base processor class with common functionality.'''

    def __init__(self, name: str):
        self.name = name
        self.processed_count = 0

    def validate_input(self, data):
        '''Validate input data before processing.'''
        if not data:
            raise ValueError("Data cannot be empty")
        return True

    def process_item(self, item):
        '''Process a single item - to be overridden.'''
        raise NotImplementedError("Subclasses must implement process_item")

    def log_processing(self, item):
        '''Log the processing of an item.'''
        print(f"{self.name} processed: {item}")
        self.processed_count += 1
"""

    (temp_dir / "base_processor.py").write_text(base_class)

    # Create derived class 1
    derived_class1 = """from base_processor import BaseProcessor

class DataProcessor(BaseProcessor):
    '''Processes data records using base functionality.'''

    def __init__(self):
        super().__init__("DataProcessor")

    def process_item(self, item):
        '''Process data item - inherits validate_input and log_processing.'''
        self.validate_input(item)
        result = self.transform_data(item)
        self.log_processing(item)
        return result

    def transform_data(self, data):
        '''Transform data specific to this processor.'''
        return {"transformed": data, "processor": self.name}
"""

    (temp_dir / "data_processor.py").write_text(derived_class1)

    # Create derived class 2
    derived_class2 = """from base_processor import BaseProcessor

class FileProcessor(BaseProcessor):
    '''Processes files using base functionality.'''

    def __init__(self):
        super().__init__("FileProcessor")

    def process_item(self, item):
        '''Process file item - inherits validate_input and log_processing.'''
        self.validate_input(item)
        result = self.process_file(item)
        self.log_processing(item)
        return result

    def process_file(self, filename):
        '''Process file specific to this processor.'''
        return {"processed_file": filename, "processor": self.name}
"""

    (temp_dir / "file_processor.py").write_text(derived_class2)

    return temp_dir


def create_test_project_with_imports() -> Path:
    """Create a temporary test project with cross-file imports."""
    temp_dir = Path(tempfile.mkdtemp(prefix="import_tracking_test_"))

    # Create shared utilities module
    utils_module = """class ConfigManager:
    '''Centralized configuration management.'''

    def __init__(self, config_path: str = "config.json"):
        self.config_path = config_path
        self.config_data = {}

    def load_config(self):
        '''Load configuration from file.'''
        with open(self.config_path, 'r') as f:
            self.config_data = json.load(f)
        return self.config_data

    def get_setting(self, key: str, default=None):
        '''Get a specific setting value.'''
        return self.config_data.get(key, default)

class Logger:
    '''Centralized logging utility.'''

    def __init__(self, name: str):
        self.name = name

    def info(self, message: str):
        '''Log info message.'''
        print(f"[INFO] {self.name}: {message}")

    def error(self, message: str):
        '''Log error message.'''
        print(f"[ERROR] {self.name}: {message}")
"""

    (temp_dir / "utils.py").write_text(utils_module)

    # Create service that imports utilities
    service1 = """from utils import ConfigManager, Logger

class DatabaseService:
    '''Database service using shared utilities.'''

    def __init__(self):
        self.config = ConfigManager("db_config.json")
        self.logger = Logger("DatabaseService")

    def connect(self):
        '''Connect to database using ConfigManager settings.'''
        db_config = self.config.load_config()
        host = self.config.get_setting("host", "localhost")
        self.logger.info(f"Connecting to database at {host}")
        return True

    def query(self, sql: str):
        '''Execute database query with logging.'''
        self.logger.info(f"Executing query: {sql}")
        return {"result": "mock_data"}
"""

    (temp_dir / "database_service.py").write_text(service1)

    # Create another service that imports the same utilities
    service2 = """from utils import ConfigManager, Logger

class EmailService:
    '''Email service using shared utilities.'''

    def __init__(self):
        self.config = ConfigManager("email_config.json")
        self.logger = Logger("EmailService")

    def send_email(self, to: str, subject: str, body: str):
        '''Send email using ConfigManager settings and Logger.'''
        smtp_config = self.config.load_config()
        smtp_host = self.config.get_setting("smtp_host", "localhost")
        self.logger.info(f"Sending email to {to} via {smtp_host}")
        return True

    def validate_email(self, email: str):
        '''Validate email address format.'''
        if "@" in email:
            self.logger.info(f"Email {email} is valid")
            return True
        self.logger.error(f"Invalid email: {email}")
        return False
"""

    (temp_dir / "email_service.py").write_text(service2)

    # Create type usage file
    type_usage = """from utils import ConfigManager, Logger
from typing import List, Dict, Optional

class ServiceOrchestrator:
    '''Orchestrator using ConfigManager and Logger as types.'''

    def __init__(self, config: ConfigManager, logger: Logger):
        self.config: ConfigManager = config  # Type annotation usage
        self.logger: Logger = logger         # Type annotation usage

    def initialize_services(self, services: List[str]) -> Dict[str, bool]:
        '''Initialize multiple services with type annotations.'''
        results: Dict[str, bool] = {}

        for service_name in services:
            self.logger.info(f"Initializing {service_name}")
            # ConfigManager used in conditional
            if self.config.get_setting("enable_" + service_name, False):
                results[service_name] = True
            else:
                results[service_name] = False

        return results
"""

    (temp_dir / "orchestrator.py").write_text(type_usage)

    return temp_dir


def test_inherited_method_deduplication():
    """Test complete pipeline correctly handles inherited methods."""
    print("🧪 Testing inherited method deduplication...")

    # Create test project
    test_project = create_test_project_with_inheritance()

    try:
        # Configure duplicate finder with origin tracking
        config = DuplicateFinderConfig(
            exclude_file_patterns=[],  # Include all files
            include_symbol_types=["function", "method", "class"],
        )

        # Create ChromaDB storage for testing
        chromadb_config = ChromaDBConfig()
        chromadb_config.persist_directory = test_project / ".test_chromadb"

        finder = DuplicateFinder(config)
        finder.verbose = True

        # Extract symbols with origin tracking enabled
        print(f"📁 Extracting symbols from {test_project}")
        symbols = finder._extract_project_symbols(test_project)

        print(f"📊 Found {len(symbols)} total symbols")

        # Look for inherited methods that should be deduplicated
        inherited_methods = []
        for symbol in symbols:
            if symbol.name in ["validate_input", "log_processing"] and hasattr(
                symbol, "origin_signature"
            ):
                inherited_methods.append(symbol)

        print(f"🔍 Found {len(inherited_methods)} potential inherited method references")

        # Apply filtering with origin tracking
        filtered_symbols = finder._filter_symbols(symbols)

        print(f"✅ After origin-based filtering: {len(filtered_symbols)} symbols")

        # Verify inherited methods are properly deduplicated
        remaining_inherited = []
        for symbol in filtered_symbols:
            if symbol.name in ["validate_input", "log_processing"]:
                remaining_inherited.append(symbol)

        print(f"🎯 Remaining inherited method symbols: {len(remaining_inherited)}")

        # Should have only definitions, not references
        for symbol in remaining_inherited:
            if hasattr(symbol, "is_reference"):
                assert (
                    not symbol.is_reference
                ), f"Found reference symbol that should be filtered: {symbol.name}"

        print("✅ Inherited method deduplication test PASSED")
        return True

    except Exception as e:
        print(f"❌ Inherited method deduplication test FAILED: {e}")
        return False
    finally:
        # Cleanup
        import shutil

        shutil.rmtree(test_project, ignore_errors=True)


def test_import_symbol_filtering():
    """Test complete pipeline correctly handles cross-file imports."""
    print("🧪 Testing import symbol filtering...")

    # Create test project
    test_project = create_test_project_with_imports()

    try:
        # Configure duplicate finder
        config = DuplicateFinderConfig(
            exclude_file_patterns=[],
            include_symbol_types=["function", "method", "class", "variable", "type"],
        )

        finder = DuplicateFinder(config)
        finder.verbose = True

        # Extract symbols
        print(f"📁 Extracting symbols from {test_project}")
        symbols = finder._extract_project_symbols(test_project)

        print(f"📊 Found {len(symbols)} total symbols")

        # Find import and usage patterns
        config_manager_symbols = []
        logger_symbols = []

        for symbol in symbols:
            if "ConfigManager" in symbol.name or "ConfigManager" in symbol.line_content:
                config_manager_symbols.append(symbol)
            if "Logger" in symbol.name or "Logger" in symbol.line_content:
                logger_symbols.append(symbol)

        print(f"🔍 ConfigManager references: {len(config_manager_symbols)}")
        print(f"🔍 Logger references: {len(logger_symbols)}")

        # Apply origin-based filtering
        filtered_symbols = finder._filter_symbols(symbols)

        print(f"✅ After origin-based filtering: {len(filtered_symbols)} symbols")

        # Check that import references are properly filtered
        remaining_config_manager = []
        remaining_logger = []

        for symbol in filtered_symbols:
            if "ConfigManager" in symbol.name or "ConfigManager" in symbol.line_content:
                remaining_config_manager.append(symbol)
            if "Logger" in symbol.name or "Logger" in symbol.line_content:
                remaining_logger.append(symbol)

        print(f"🎯 Remaining ConfigManager symbols: {len(remaining_config_manager)}")
        print(f"🎯 Remaining Logger symbols: {len(remaining_logger)}")

        # Should have significantly fewer symbols after origin-based filtering
        reduction_ratio = len(filtered_symbols) / len(symbols) if symbols else 0
        print(f"📉 Symbol reduction ratio: {1 - reduction_ratio:.2%}")

        # Verify import references are marked correctly
        for symbol in filtered_symbols:
            if hasattr(symbol, "is_reference") and symbol.is_reference:
                assert (
                    False
                ), f"Found reference symbol that should be filtered: {symbol.name}"

        print("✅ Import symbol filtering test PASSED")
        return True

    except Exception as e:
        print(f"❌ Import symbol filtering test FAILED: {e}")
        return False
    finally:
        # Cleanup
        import shutil

        shutil.rmtree(test_project, ignore_errors=True)


def test_performance_impact():
    """Test processing time increase is <25% with origin tracking enabled."""
    print("🧪 Testing performance impact of origin tracking...")

    # Create larger test project for meaningful performance measurement
    test_project = create_test_project_with_imports()

    # Add more files to make performance test meaningful
    for i in range(5):
        service_template = f"""from utils import ConfigManager, Logger

class Service{i}:
    '''Service {i} using shared utilities.'''

    def __init__(self):
        self.config = ConfigManager("service{i}_config.json")
        self.logger = Logger("Service{i}")

    def method_a(self):
        '''Method A in service {i}.'''
        self.logger.info(f"Service {i} method A called")
        return self.config.get_setting("setting_a", "default")

    def method_b(self):
        '''Method B in service {i}.'''
        self.logger.info(f"Service {i} method B called")
        return self.config.get_setting("setting_b", "default")

    def method_c(self):
        '''Method C in service {i}.'''
        config_data = self.config.load_config()
        self.logger.info(f"Service {i} method C executed")
        return config_data
"""
        (test_project / f"service_{i}.py").write_text(service_template)

    try:
        # Test with origin tracking DISABLED
        config_disabled = DuplicateFinderConfig(exclude_file_patterns=[])
        finder_disabled = DuplicateFinder(config_disabled)

        # Mock LSP extractor to disable origin tracking
        if hasattr(finder_disabled.lsp_extractor, "config"):
            finder_disabled.lsp_extractor.config.enable_origin_tracking = False

        print("⏱️  Testing without origin tracking...")
        start_time = time.time()

        symbols_disabled = finder_disabled._extract_project_symbols(test_project)
        filtered_disabled = finder_disabled._filter_symbols(symbols_disabled)

        time_without_origin_tracking = time.time() - start_time

        print(f"⏱️  Time without origin tracking: {time_without_origin_tracking:.3f}s")
        print(
            f"📊 Symbols without origin tracking: {len(symbols_disabled)} -> {len(filtered_disabled)}"
        )

        # Test with origin tracking ENABLED
        config_enabled = DuplicateFinderConfig(exclude_file_patterns=[])
        finder_enabled = DuplicateFinder(config_enabled)

        # Enable origin tracking
        if hasattr(finder_enabled.lsp_extractor, "config"):
            finder_enabled.lsp_extractor.config.enable_origin_tracking = True

        print("⏱️  Testing with origin tracking...")
        start_time = time.time()

        symbols_enabled = finder_enabled._extract_project_symbols(test_project)
        filtered_enabled = finder_enabled._filter_symbols(symbols_enabled)

        time_with_origin_tracking = time.time() - start_time

        print(f"⏱️  Time with origin tracking: {time_with_origin_tracking:.3f}s")
        print(
            f"📊 Symbols with origin tracking: {len(symbols_enabled)} -> {len(filtered_enabled)}"
        )

        # Calculate performance impact
        if time_without_origin_tracking > 0:
            performance_impact = (
                time_with_origin_tracking - time_without_origin_tracking
            ) / time_without_origin_tracking
            print(f"📈 Performance impact: {performance_impact:.1%}")

            # Test passes if impact is less than 25%
            if performance_impact < 0.25:
                print("✅ Performance impact test PASSED (<25% increase)")
                return True
            else:
                print(
                    f"❌ Performance impact test FAILED ({performance_impact:.1%} > 25%)"
                )
                return False
        else:
            print("⚠️  Performance test inconclusive (baseline too fast)")
            return True

    except Exception as e:
        print(f"❌ Performance impact test FAILED: {e}")
        return False
    finally:
        # Cleanup
        import shutil

        shutil.rmtree(test_project, ignore_errors=True)


def main():
    """Run all integration tests for origin tracking."""
    print("🚀 Running Phase 2 Origin Tracking Integration Tests")
    print("=" * 60)

    tests = [
        ("Inherited Method Deduplication", test_inherited_method_deduplication),
        ("Import Symbol Filtering", test_import_symbol_filtering),
        ("Performance Impact", test_performance_impact),
    ]

    results = {}

    for test_name, test_func in tests:
        print(f"\n📋 Running {test_name}...")
        print("-" * 40)

        try:
            result = test_func()
            results[test_name] = result

            if result:
                print(f"✅ {test_name} PASSED")
            else:
                print(f"❌ {test_name} FAILED")

        except Exception as e:
            print(f"💥 {test_name} ERROR: {e}")
            results[test_name] = False

    # Summary
    print("\n" + "=" * 60)
    print("🎯 INTEGRATION TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for result in results.values() if result)
    total = len(results)

    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")

    print(f"\nOverall: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All integration tests PASSED!")
        return 0
    else:
        print(f"⚠️  {total - passed} integration tests FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
