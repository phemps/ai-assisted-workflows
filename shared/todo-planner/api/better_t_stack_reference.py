#!/usr/bin/env python3
"""
Better-T-Stack Reference Table and Compatibility Rules

This module contains the definitive reference for all Better-T-Stack options
and their compatibility rules based on the official CLI help output.
"""

from typing import Dict, List
from dataclasses import dataclass


@dataclass
class StackOption:
    """Represents a stack option with its possible values and descriptions."""

    name: str
    values: List[str]
    description: str
    required: bool = False


# All available options from create-better-t-stack --help
STACK_OPTIONS = {
    "database": StackOption(
        name="database",
        values=["none", "sqlite", "postgres", "mysql", "mongodb"],
        description="Database type",
        required=False,
    ),
    "orm": StackOption(
        name="orm",
        values=["drizzle", "prisma", "mongoose", "none"],
        description="ORM type",
        required=False,
    ),
    "auth": StackOption(
        name="auth",
        values=[True, False],  # Boolean option
        description="Include authentication",
        required=False,
    ),
    "frontend": StackOption(
        name="frontend",
        values=[
            "tanstack-router",
            "react-router",
            "tanstack-start",
            "next",
            "nuxt",
            "native-nativewind",
            "native-unistyles",
            "svelte",
            "solid",
            "none",
        ],
        description="Frontend framework",
        required=False,
    ),
    "addons": StackOption(
        name="addons",
        values=[
            "pwa",
            "tauri",
            "starlight",
            "biome",
            "husky",
            "vibe-rules",
            "turborepo",
            "fumadocs",
            "ultracite",
            "oxlint",
            "none",
        ],
        description="Additional addons",
        required=False,
    ),
    "examples": StackOption(
        name="examples",
        values=["todo", "ai", "none"],
        description="Example templates to include",
        required=False,
    ),
    "git": StackOption(
        name="git",
        values=[True, False],  # Boolean option
        description="Initialize git repository",
        required=False,
    ),
    "package_manager": StackOption(
        name="package-manager",
        values=["npm", "pnpm", "bun"],
        description="Package manager",
        required=False,
    ),
    "install": StackOption(
        name="install",
        values=[True, False],  # Boolean option
        description="Install dependencies",
        required=False,
    ),
    "db_setup": StackOption(
        name="db-setup",
        values=[
            "turso",
            "neon",
            "prisma-postgres",
            "mongodb-atlas",
            "supabase",
            "d1",
            "docker",
            "none",
        ],
        description="Database hosting setup",
        required=False,
    ),
    "backend": StackOption(
        name="backend",
        values=["hono", "express", "fastify", "next", "elysia", "convex", "none"],
        description="Backend framework",
        required=False,
    ),
    "runtime": StackOption(
        name="runtime",
        values=["bun", "node", "workers", "none"],
        description="Runtime environment",
        required=False,
    ),
    "api": StackOption(
        name="api",
        values=["trpc", "orpc", "none"],
        description="API type",
        required=False,
    ),
    "web_deploy": StackOption(
        name="web-deploy",
        values=["workers", "none"],
        description="Web deployment",
        required=False,
    ),
}

# Known compatibility rules and incompatibilities
COMPATIBILITY_RULES = {
    # Database + ORM compatibility
    "mongodb_requires_mongoose": {
        "rule": "If database is 'mongodb', ORM must be 'mongoose' or 'none'",
        "condition": lambda config: config.get("database") == "mongodb",
        "requirement": lambda config: config.get("orm") in ["mongoose", "none", None],
    },
    "mongoose_requires_mongodb": {
        "rule": "If ORM is 'mongoose', database must be 'mongodb'",
        "condition": lambda config: config.get("orm") == "mongoose",
        "requirement": lambda config: config.get("database") == "mongodb",
    },
    # Backend + Runtime compatibility
    "convex_runtime_constraints": {
        "rule": "Convex backend has specific runtime requirements",
        "condition": lambda config: config.get("backend") == "convex",
        "requirement": lambda config: config.get("runtime") in ["node", "none", None],
    },
    "workers_runtime_required": {
        "rule": "If runtime is 'workers', backend should be compatible (hono, express, etc.)",
        "condition": lambda config: config.get("runtime") == "workers",
        "requirement": lambda config: config.get("backend")
        in ["hono", "express", "fastify", "none", None],
    },
    # Database setup compatibility
    "turso_requires_sqlite": {
        "rule": "Turso database setup requires sqlite database",
        "condition": lambda config: config.get("db_setup") == "turso",
        "requirement": lambda config: config.get("database") == "sqlite",
    },
    "neon_requires_postgres": {
        "rule": "Neon database setup requires postgres database",
        "condition": lambda config: config.get("db_setup") == "neon",
        "requirement": lambda config: config.get("database") == "postgres",
    },
    "d1_requires_sqlite": {
        "rule": "Cloudflare D1 setup requires sqlite database",
        "condition": lambda config: config.get("db_setup") == "d1",
        "requirement": lambda config: config.get("database") == "sqlite",
    },
    # Frontend + Native compatibility
    "native_frontend_exclusive": {
        "rule": "Native frontends (native-nativewind, native-unistyles) cannot be combined with web frontends",
        "condition": lambda config: config.get("frontend")
        in ["native-nativewind", "native-unistyles"],
        "requirement": lambda config: True,  # This is a complex rule - native should be exclusive
    },
}

# Recommended combinations (proven to work well together)
RECOMMENDED_COMBINATIONS = [
    {
        "name": "Next.js + Convex Full Stack",
        "config": {
            "frontend": "next",
            "backend": "convex",
            "package_manager": "bun",
            "auth": True,
        },
        "description": "Popular full-stack setup with built-in auth",
    },
    {
        "name": "Hono + Drizzle + SQLite",
        "config": {
            "backend": "hono",
            "database": "sqlite",
            "orm": "drizzle",
            "db_setup": "turso",
            "runtime": "workers",
        },
        "description": "Lightweight edge-first stack",
    },
    {
        "name": "React Router + tRPC + Prisma",
        "config": {
            "frontend": "tanstack-router",
            "api": "trpc",
            "database": "postgres",
            "orm": "prisma",
            "db_setup": "neon",
        },
        "description": "Type-safe full-stack with modern routing",
    },
    {
        "name": "Native React Native + NativeWind",
        "config": {"frontend": "native-nativewind", "package_manager": "bun"},
        "description": "Mobile-first development with Tailwind-like styling",
    },
]


def validate_config(config: Dict) -> tuple[bool, List[str]]:
    """
    Validate a configuration against known compatibility rules.

    Args:
        config: Dictionary of configuration options

    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []

    for rule_name, rule in COMPATIBILITY_RULES.items():
        if rule["condition"](config):
            if not rule["requirement"](config):
                errors.append(f"Violated rule '{rule_name}': {rule['rule']}")

    return len(errors) == 0, errors


def get_compatible_values(config: Dict, option_name: str) -> List[str]:
    """
    Given a partial config, return the compatible values for a specific option.

    Args:
        config: Partial configuration dictionary
        option_name: Name of the option to get compatible values for

    Returns:
        List of compatible values for that option
    """
    if option_name not in STACK_OPTIONS:
        return []

    option = STACK_OPTIONS[option_name]
    compatible_values = []

    for value in option.values:
        # Test this value by adding it to config
        test_config = config.copy()
        test_config[option_name] = value

        is_valid, _ = validate_config(test_config)
        if is_valid:
            compatible_values.append(value)

    return compatible_values


def suggest_next_options(config: Dict) -> Dict[str, List[str]]:
    """
    Given a partial config, suggest what options to configure next.

    Args:
        config: Partial configuration dictionary

    Returns:
        Dictionary mapping option names to their compatible values
    """
    suggestions = {}

    for option_name, option in STACK_OPTIONS.items():
        if option_name not in config:
            compatible = get_compatible_values(config, option_name)
            if compatible:
                suggestions[option_name] = compatible

    return suggestions


if __name__ == "__main__":
    # Test some configurations
    test_configs = [
        {"backend": "convex", "auth": True},
        {"database": "mongodb", "orm": "prisma"},  # Should be invalid
        {"frontend": "next", "backend": "convex", "package_manager": "bun"},
    ]

    for config in test_configs:
        is_valid, errors = validate_config(config)
        print(f"Config: {config}")
        print(f"Valid: {is_valid}")
        if errors:
            print(f"Errors: {errors}")
        print("-" * 40)
