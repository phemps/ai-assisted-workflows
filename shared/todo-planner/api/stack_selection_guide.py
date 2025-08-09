#!/usr/bin/env python3
"""
Stack Selection Guide for LLMs

This module provides guidance functions that LLMs can use during the
stack selection phase to make informed choices based on requirements.
"""

from .better_t_stack_reference import (
    STACK_OPTIONS,
    RECOMMENDED_COMBINATIONS,
    validate_config,
)


def get_stack_selection_prompt(requirements_summary: str = "") -> str:
    """
    Generate a comprehensive prompt for LLMs to use during stack selection.

    Args:
        requirements_summary: Brief summary of project requirements

    Returns:
        Formatted prompt with all stack options and compatibility rules
    """

    prompt = f"""
# Better-T-Stack Selection Guide

## Project Requirements Summary
{requirements_summary or "No specific requirements provided"}

## Available Stack Options

"""

    # Add all available options
    for option_name, option in STACK_OPTIONS.items():
        prompt += f"### {option.name}\n"
        prompt += f"**Description**: {option.description}\n"
        prompt += f"**Values**: {', '.join(str(v) for v in option.values)}\n"
        prompt += f"**Required**: {'Yes' if option.required else 'No'}\n\n"

    prompt += """
## Recommended Combinations

These are proven stack combinations that work well together:

"""

    for combo in RECOMMENDED_COMBINATIONS:
        prompt += f"### {combo['name']}\n"
        prompt += f"**Description**: {combo['description']}\n"
        prompt += "**Configuration**:\n"
        for key, value in combo["config"].items():
            prompt += f"  - {key}: {value}\n"
        prompt += "\n"

    prompt += """
## Selection Guidelines

1. **Start with the frontend framework** based on the project type:
   - `next`: Full-stack React with SSR/SSG
   - `tanstack-router`: Modern React SPA with type-safe routing
   - `react-router`: Traditional React SPA
   - `native-nativewind`: Mobile app with Tailwind-like styling
   - `svelte`: Lightweight alternative to React

2. **Choose backend based on complexity**:
   - `convex`: Real-time database with built-in auth (great for rapid prototyping)
   - `hono`: Lightweight, edge-compatible API framework
   - `next`: Use Next.js API routes for full-stack React apps
   - `express`: Traditional Node.js backend
   - `fastify`: High-performance Node.js backend

3. **Database selection**:
   - `sqlite`: Simple, file-based (good with Turso for production)
   - `postgres`: Full-featured SQL (use with Neon or Supabase)
   - `mongodb`: NoSQL document database (requires Mongoose ORM)

4. **ORM/Database layer**:
   - `drizzle`: Type-safe SQL ORM with great performance
   - `prisma`: Feature-rich ORM with excellent dev experience
   - `mongoose`: Required for MongoDB

5. **Authentication**:
   - Set `auth: true` if you need user authentication
   - Convex has built-in auth, but can work with external providers too

6. **Package Manager**:
   - `bun`: Fastest, modern choice
   - `pnpm`: Fast with good monorepo support
   - `npm`: Universal compatibility

## Compatibility Checking

When making selections, use this validation function:

```python
from better_t_stack_reference import validate_config

config = {
    "frontend": "next",
    "backend": "convex",
    "auth": True
}

is_valid, errors = validate_config(config)
if not is_valid:
    print("Issues:", errors)
```

## Pro Tips

1. **For rapid prototyping**: `next` + `convex` + `auth: true`
2. **For edge deployment**: `hono` + `drizzle` + `sqlite` + `runtime: workers`
3. **For complex business apps**: `tanstack-router` + `trpc` + `prisma` + `postgres`
4. **For mobile apps**: `native-nativewind` (don't combine with web frontends)

"""

    return prompt


def suggest_stack_for_requirements(requirements: dict) -> dict:
    """
    Suggest a stack configuration based on project requirements.

    Args:
        requirements: Dictionary with keys like 'project_type', 'complexity',
                     'real_time', 'mobile', 'auth_needed', etc.

    Returns:
        Suggested configuration dictionary
    """

    config = {}

    # Frontend selection
    if requirements.get("mobile"):
        config["frontend"] = "native-nativewind"
    elif requirements.get("project_type") == "spa":
        config["frontend"] = (
            "tanstack-router" if requirements.get("complex_routing") else "react-router"
        )
    elif requirements.get("ssr_needed") or requirements.get("seo_important"):
        config["frontend"] = "next"
    elif requirements.get("lightweight"):
        config["frontend"] = "svelte"
    else:
        config["frontend"] = "next"  # Safe default

    # Backend selection
    if requirements.get("real_time") or requirements.get("rapid_prototype"):
        config["backend"] = "convex"
    elif requirements.get("edge_deployment"):
        config["backend"] = "hono"
    elif config.get("frontend") == "next" and not requirements.get("separate_backend"):
        config["backend"] = "next"  # Use Next.js full-stack
    elif requirements.get("high_performance"):
        config["backend"] = "fastify"
    else:
        config["backend"] = "express"  # Safe default

    # Database selection
    if requirements.get("nosql") or requirements.get("document_based"):
        config["database"] = "mongodb"
        config["orm"] = "mongoose"
    elif requirements.get("simple") or requirements.get("edge_deployment"):
        config["database"] = "sqlite"
        config["orm"] = "drizzle"
        config["db_setup"] = "turso"
    else:
        config["database"] = "postgres"
        config["orm"] = "prisma"
        config["db_setup"] = "neon"

    # Other options
    if requirements.get("auth_needed"):
        config["auth"] = True

    if requirements.get("type_safe_apis"):
        config["api"] = "trpc"

    config["package_manager"] = "bun"  # Modern default

    # Validate the suggested config
    is_valid, errors = validate_config(config)
    if not is_valid:
        print(f"⚠️  Suggested config has issues: {errors}")
        # Try to fix common issues
        if "mongodb" in str(errors) and config.get("orm") != "mongoose":
            config["orm"] = "mongoose"

    return config


if __name__ == "__main__":
    # Example usage
    print("=== Stack Selection Guide ===")
    print(
        get_stack_selection_prompt("Building a real-time collaboration app with auth")
    )

    print("\n=== Suggestion Example ===")
    requirements = {
        "project_type": "spa",
        "real_time": True,
        "auth_needed": True,
        "rapid_prototype": True,
    }

    suggested = suggest_stack_for_requirements(requirements)
    print(f"Suggested config: {suggested}")

    is_valid, errors = validate_config(suggested)
    print(f"Valid: {is_valid}")
    if errors:
        print(f"Errors: {errors}")
