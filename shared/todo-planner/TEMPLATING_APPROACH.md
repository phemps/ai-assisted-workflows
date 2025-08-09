# Todo Planner Templating Approach

This document explains the sophisticated templating system used in the todo-planner for generating implementation skeletons with best practices and contextual guidance.

## Core Philosophy

The templating system follows a **"Technology-Specific, Choice-First Guidance"** approach that provides:

1. **Working Base Structure**: Every template generates functional code from day one
2. **Technology Specificity**: All templates are technology-specific with proper imports, patterns, and conventions
3. **No Generic Fallbacks**: Templates must exist for the specific technology or the build fails
4. **Optional Enhancement**: Advanced features are added only when explicitly chosen
5. **Contextual Best Practices**: Framework-specific advice appears when relevant options are selected
6. **PRD Traceability**: Generated code is linked to specific business requirements

### Critical Principle: No Generic Templates

**Templates must be technology-specific and follow vendor documentation patterns.** Generic templates that try to work across multiple technologies are prohibited because:

- Each technology has unique imports, APIs, and conventions
- Generic approaches often don't follow best practices
- Vendor-specific patterns ensure code compiles and works correctly
- Technology-specific templates can include proper error handling and optimizations

## Template Structure

### Basic Template Anatomy

```jinja2
// {{ file.path }} - [Template Description]
// Generated from PRD requirements

{% if file.options.feature_name %}
// ADVICE: Specific guidance when this feature is chosen
{% endif %}

import statements...

{% for function in functions %}
export function {{ function.name }}() {
  // TODO: {{ function.prd_references | join(', ') }} - {{ function.description }}

  {% if file.options.feature_name %}
  // Feature-specific implementation
  {% endif %}

  // Base implementation always present
}
{% endfor %}
```

## Key Template Variables

### File Context

- `{{ file.path }}` - Full file path for generated file
- `{{ file.module }}` - Module name (optional)
- `{{ file.kind }}` - Template type (api-route, component, service, etc.)
- `{{ file.options }}` - Dictionary of chosen features/options

### Function Context

- `{{ function.name }}` - Function identifier
- `{{ function.description }}` - Business purpose description
- `{{ function.prd_references }}` - Array of PRD requirement IDs
- `{{ function.signature.params }}` - Parameter definitions
- `{{ function.signature.return_type }}` - Expected return type
- `{{ function.stub_code }}` - Auto-generated function stub

### Available Options

Templates can check for these common options via `file.options.{name}`:

**Common Options:**

- `validation` - Input validation requirements
- `auth` - Authentication/authorization needs
- `caching` - Performance caching requirements
- `error_handling` - Comprehensive error management
- `logging` - Structured logging implementation

**Framework-Specific Options:**

- NextJS: `rate_limit`, `security_headers`, `seo`, `loading`
- Convex: `multi_tenant`, `pagination`, `audit_fields`, `soft_delete`
- Workers: `retry`, `dlq`, `metrics`, `queue`
- Analytics: `privacy`, `correlation`

## Template Organization

### Directory Structure

```
templates/
├── nextjs/              # Next.js specific templates
│   ├── api-route.jinja  # API route handlers with Next.js patterns
│   ├── middleware.jinja # Next.js middleware with proper imports
│   └── page.jinja       # Next.js page components
├── react-router/        # React Router templates
│   ├── component.jinja  # React Router components with hooks
│   ├── page.jinja       # React Router page components
│   ├── layout.jinja     # React Router layout with nested routing
│   └── loader.jinja     # React Router data loading functions
├── convex/              # Convex database templates
│   ├── schema.jinja     # Convex schema with validators
│   ├── auth.jinja       # Convex authentication helpers
│   ├── query.jinja      # Convex queries with indexes
│   ├── mutation.jinja   # Convex mutations with validation
│   └── action.jinja     # Convex Node.js actions
├── drizzle/             # Drizzle ORM templates
│   ├── schema.jinja     # Drizzle schema definitions
│   └── client.jinja     # Drizzle database client
├── prisma/              # Prisma ORM templates
│   ├── schema.jinja     # Prisma schema with relations
│   └── client.jinja     # Prisma client operations
├── mongoose/            # Mongoose ODM templates
│   ├── schema.jinja     # Mongoose schemas with validation
│   └── client.jinja     # Mongoose connection and operations
├── trpc/                # tRPC API templates
│   └── router.jinja     # tRPC router with procedures
├── hono/                # Hono web framework
│   └── app.jinja        # Hono application with middleware
├── elysia/              # Elysia framework templates
│   └── app.jinja        # Elysia app with validation
├── express/             # Express.js templates
│   └── router.jinja     # Express router with middleware
├── cloudflare/          # Cloudflare Workers
│   └── worker.jinja     # Worker functions with bindings
└── analytics/           # Analytics integration
    └── events.jinja     # Event tracking (vendor-agnostic patterns)
```

**Note**: No `common/` directory exists. All templates are technology-specific.

### Template Selection Logic

1. **Technology-Specific Only**: `{stack}/{file_kind}.jinja`
2. **No Fallbacks**: If no technology-specific template exists, the build fails with clear error
3. **Explicit Error Messages**: Missing templates produce actionable error messages

**Example Selection Process:**

```
Stack: "nextjs-app-router"
File Kind: "api-route"

Search Order:
1. templates/nextjs/api-route.jinja ✅ (Found - use this)
2. templates/app-router/api-route.jinja (Not found)
3. No fallbacks attempted
4. Generate code using nextjs/api-route.jinja
```

**If no template found:**

```
❌ Error: No template found for api-route in nextjs-app-router
   Searched: nextjs, app-router
   Required: Create templates/nextjs/api-route.jinja or templates/app-router/api-route.jinja
```

## Template Implementation Patterns

### 1. Conditional Guidance Blocks

Use `{% if file.options.{feature} %}` to include feature-specific advice:

```jinja2
{% if file.options.validation %}
// ADVICE: Implement input validation for all request data
// - Use schema validation libraries (Zod, Joi, etc.)
// - Validate at the boundary, trust internal data
// - Return meaningful error messages
{% endif %}
```

### 2. PRD Integration

Always link generated code to business requirements:

```jinja2
export async function {{ function.name }}() {
  // TODO: {{ function.prd_references | join(', ') }} - {{ function.description }}

  // Implementation here...
}
```

### 3. Best Practice Enforcement

Include framework-specific patterns as base structure:

```jinja2
// Next.js API Route Pattern
export async function {{ function.name }}(request: NextRequest) {
  try {
    // Main business logic
    const result = await processRequest(data);
    return NextResponse.json(result);
  } catch (error) {
    console.error('API Error:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}
```

### 4. Progressive Enhancement

Build from simple to complex based on chosen options:

```jinja2
// Base authentication check (always present)
const user = await getCurrentUser(ctx);

{% if file.options.multi_tenant %}
// Enhanced: Tenant isolation (when chosen)
const tenant = await getCurrentTenant(ctx);
if (resource.tenantId !== tenant._id) {
  throw new Error("Access denied");
}
{% endif %}

{% if file.options.permissions %}
// Enhanced: Permission checking (when chosen)
if (!await hasPermission(user, "read:documents")) {
  throw new Error("Insufficient permissions");
}
{% endif %}
```

## Advanced Template Features

### 1. Runtime-Aware Templates

Some templates adapt to different runtime requirements:

```jinja2
{% if needs_node_runtime %}
"use node";
{% endif %}
// {{ file.path }}

{% if needs_node_runtime %}
import fs from "node:fs/promises";
import crypto from "node:crypto";
{% endif %}
```

### 2. Multi-Framework Support

Templates can generate different imports/patterns based on detected stack:

```jinja2
{% if stack_profile == "nextjs-app-router" %}
import { NextRequest, NextResponse } from 'next/server';
{% elif stack_profile == "hono" %}
import { Hono } from 'hono';
{% endif %}
```

### 3. Security Pattern Integration

Templates automatically include security best practices:

```jinja2
// Convex Query with mandatory tenant filtering
export const {{ function.name }} = query({
  handler: async (ctx, args) => {
    const tenant = await getCurrentTenant(ctx);

    return await ctx.db
      .query("documents")
      .withIndex("by_tenant", (q) => q.eq("tenantId", tenant._id))
      .take(50);
  },
});
```

## Quality Assurance

### Template Validation

Before creating templates, verify:

1. **Technology Specificity**: Templates must use technology-specific imports, APIs, and patterns
2. **Vendor Documentation**: Follow official documentation and best practices for the technology
3. **No Generic Code**: Avoid generic approaches that work across multiple technologies
4. **Required Sections**: Include PRD TODO comments for traceability
5. **Framework Conventions**: Use proper naming, structure, and error handling for the technology
6. **Option Consistency**: Use consistent option names across templates
7. **Compilation Validation**: Generated code must compile and follow linting rules

### Technology-Specific Examples

**❌ Generic (Prohibited):**

```jinja2
// Generic database operation
export function getData(id) {
  return database.find(id); // Generic - doesn't specify which DB client
}
```

**✅ Technology-Specific (Required):**

**Drizzle Template:**

```jinja2
// Drizzle-specific database operation
import { eq } from 'drizzle-orm';
import { db } from './drizzle';
import { users } from './schema';

export async function getUser(id: string) {
  const [user] = await db.select().from(users).where(eq(users.id, id)).limit(1);
  return user;
}
```

**Prisma Template:**

```jinja2
// Prisma-specific database operation
import { PrismaClient } from '@prisma/client';
const prisma = new PrismaClient();

export async function getUser(id: string) {
  return await prisma.user.findUnique({ where: { id } });
}
```

### Testing Templates

Templates should generate code that:

1. **Compiles Successfully**: Passes TypeScript/linting checks
2. **Follows Conventions**: Matches project code style
3. **Implements Security**: Includes auth/validation patterns
4. **Provides Guidance**: ADVICE comments help developers
5. **Links to Requirements**: TODO comments reference PRD sections

## Example: Complete Template Implementation

Here's a complete example showing all patterns:

```jinja2
// {{ file.path }} - Next.js API Route
// Generated from PRD requirements
{% if file.options.validation %}
// ADVICE: Implement input validation for all request data
// - Use schema validation libraries (Zod, Joi, etc.)
// - Validate at API boundaries, trust internal data
{% endif %}
{% if file.options.auth %}
// ADVICE: Add authentication middleware to protect this endpoint
// - Verify JWT tokens or session cookies
// - Check user permissions for this resource
{% endif %}

import { NextRequest, NextResponse } from 'next/server';
{% if file.options.validation %}
import { z } from 'zod';
{% endif %}

{% if file.options.validation %}
const requestSchema = z.object({
  name: z.string().min(1),
  description: z.string().optional(),
});
{% endif %}

{% for function in functions %}
{% if function.name in ['GET', 'POST', 'PUT', 'DELETE'] %}
export async function {{ function.name }}(request: NextRequest) {
  try {
    // TODO: {{ function.prd_references | join(', ') }} - {{ function.description }}

    {% if file.options.auth %}
    // Verify authentication
    const session = await getServerSession(request);
    if (!session?.user) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }
    {% endif %}

    {% if file.options.validation and function.name in ['POST', 'PUT'] %}
    // Validate request data
    const body = await request.json();
    const validatedData = requestSchema.parse(body);
    {% endif %}

    // Main business logic
    const result = await processRequest(
      {% if file.options.validation and function.name in ['POST', 'PUT'] %}validatedData{% else %}request{% endif %}
      {% if file.options.auth %}, session.user{% endif %}
    );

    return NextResponse.json(result);
  } catch (error) {
    console.error('API Error:', error);

    {% if file.options.validation %}
    if (error instanceof z.ZodError) {
      return NextResponse.json({ error: 'Invalid input', details: error.errors }, { status: 400 });
    }
    {% endif %}

    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}
{% endif %}
{% endfor %}

// Helper functions
async function processRequest(
  {% if file.options.validation %}data: z.infer<typeof requestSchema>{% else %}request: NextRequest{% endif %}
  {% if file.options.auth %}{% if file.options.validation %}, {% endif %}user: User{% endif %}
) {
  // TODO: Implement main business logic
  throw new Error("Business logic not implemented");
}
```

## Future Extensions

The templating system can be extended by:

1. **Adding New Stacks**: Create new `{stack}/` directories with technology-specific templates
2. **New Template Types**: Add new `{kind}.jinja` files following vendor documentation
3. **Enhanced Options**: Define new `file.options` for technology-specific patterns
4. **Integration Patterns**: Create vendor-specific templates (not generic integrations)

### Guidelines for New Templates

When adding new technology templates:

1. **Research First**: Study the official documentation and best practices
2. **Technology-Specific**: Use proper imports, APIs, and patterns for that technology
3. **No Abstractions**: Don't create generic abstractions that hide technology details
4. **Test Generated Code**: Ensure templates produce code that compiles and follows conventions
5. **Follow Conventions**: Match the technology's naming, structure, and error handling patterns

### Example: Adding New Technology Support

To add support for a new technology (e.g., SvelteKit):

1. **Create directory**: `templates/sveltekit/`
2. **Research patterns**: Study SvelteKit documentation for routing, data loading, etc.
3. **Create specific templates**:
   - `page.jinja` - SvelteKit page components with `+page.svelte` patterns
   - `layout.jinja` - SvelteKit layout with `+layout.svelte` patterns
   - `server.jinja` - SvelteKit server routes with `+page.server.ts` patterns
4. **Use SvelteKit APIs**: Import from `'$app/stores'`, `'$app/navigation'`, etc.
5. **Follow SvelteKit conventions**: Use proper TypeScript, store patterns, etc.

This approach ensures generated code follows technology-specific best practices and works correctly from day one.
