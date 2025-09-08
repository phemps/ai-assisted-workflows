#!/usr/bin/env python3

from pathlib import Path
from core.utils.tech_stack_detector import TechStackDetector


def test_file_exists_pattern_glob_match(tmp_path: Path, tech_stacks_config_path: Path):
    (tmp_path / "src").mkdir(parents=True, exist_ok=True)
    (tmp_path / "src" / "a.py").write_text("print('x')\n", encoding="utf-8")
    det = TechStackDetector.from_config(tech_stacks_config_path)
    assert det._file_exists_pattern(tmp_path, "src/*.py") is True  # type: ignore[attr-defined]


def test_exclusions_extensions_per_stack_java_and_dotnet(
    tmp_path: Path, tech_stacks_config_path: Path
):
    (tmp_path / "pom.xml").write_text("<project/>", encoding="utf-8")
    (tmp_path / "proj.csproj").write_text("<Project/>", encoding="utf-8")
    det = TechStackDetector.from_config(tech_stacks_config_path)
    excl = det.get_simple_exclusions(str(tmp_path))
    assert any(ext in excl["extensions"] for ext in [".class", ".jar"])  # Java
    assert any(ext in excl["extensions"] for ext in [".dll", ".exe"])  # .NET


def test_is_generated_or_vendor_code_copyright(
    tmp_path: Path, tech_stacks_config_path: Path
):
    f = tmp_path / "vendor.js"
    f.write_text("/* Copyright 2024 */\n", encoding="utf-8")
    det = TechStackDetector.from_config(tech_stacks_config_path)
    assert det._is_generated_or_vendor_code(str(f)) is True  # type: ignore[attr-defined]


def test_should_analyze_vendor_marker_inside_src_is_allowed(
    tmp_path: Path, tech_stacks_config_path: Path
):
    f = tmp_path / "src" / "app.js"
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text("// jquery component\n", encoding="utf-8")
    det = TechStackDetector.from_config(tech_stacks_config_path)
    assert det.should_analyze_file(str(f), str(tmp_path)) is True


def test_get_simple_exclusions_swift_kotlin_cpp(
    tmp_path: Path, tech_stacks_config_path: Path
):
    (tmp_path / "Package.swift").write_text("// swift\n", encoding="utf-8")
    (tmp_path / "build.gradle.kts").write_text("plugins{}\n", encoding="utf-8")
    (tmp_path / "CMakeLists.txt").write_text("project(X)\n", encoding="utf-8")
    det = TechStackDetector.from_config(tech_stacks_config_path)
    excl = det.get_simple_exclusions(str(tmp_path))
    # Swift
    assert any(
        d in excl["directories"] for d in [".build", "build", "DerivedData"]
    )  # swift
    # Kotlin
    assert any(
        d in excl["directories"] for d in ["build", ".gradle", ".idea"]
    )  # kotlin
    # C/C++
    assert any(
        d in excl["directories"]
        for d in ["cmake-build-debug", "cmake-build-release", "build"]
    )
