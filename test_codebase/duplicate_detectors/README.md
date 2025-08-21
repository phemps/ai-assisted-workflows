# Duplicate Detection Test Fixtures

This directory contains permanent test fixtures for the continuous improvement system's duplicate detection capabilities.

## Purpose

These files serve as a **real-world example** of code duplication that was discovered during development:

- `language_detector.py` (143 lines) - Simple language detection utility
- `tech_stack_detector.py` (599 lines) - Comprehensive tech stack detection

## The Duplication

Both files contain overlapping functionality for detecting programming languages from file extensions. The `LanguageDetector` provides a simple mapping from file extensions to language names, while `TechStackDetector` contains more sophisticated tech stack detection with language information embedded in its `primary_languages` fields.

## Test Case Usage

These files are used to:

1. **Test similarity thresholds** - Find the threshold where semantic duplicate detection identifies the overlap
2. **Validate CI system** - Ensure the continuous improvement workflow can detect and process real duplications
3. **Permanent regression testing** - Keep these files to ensure future changes don't break duplicate detection

## Detection Expectations

The semantic duplicate detector should identify similarities between:
- Language mapping patterns
- File extension handling logic
- Language name normalization

## Do Not Remove

These files are **permanent test fixtures** and should not be cleaned up or removed. They serve as a controlled test case for the duplicate detection system.

## History

Created during the implementation of incremental language detection as an example of how development can introduce duplication even while trying to eliminate it - a perfect "dogfooding" scenario for the CI system.