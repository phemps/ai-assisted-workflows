# Plan Datamodel Command

**Mindset**: "Data drives design" - Strategic data model design with relationships, performance, and scalability considerations.

## Behavior
Comprehensive data model planning combining entity relationship design with performance optimization and scalability planning.

### Data Model Planning Areas
- **Entity Relationship Design**: Entity identification, relationship mapping, and normalization
- **Performance Optimization**: Query optimization, indexing strategy, and data access patterns
- **Scalability Planning**: Data partitioning, sharding, and growth accommodation
- **Data Integrity**: Constraint definition, validation rules, and consistency requirements
- **Migration Strategy**: Schema evolution, data migration, and backward compatibility
- **Integration Planning**: External system integration and data synchronization

## Planning Framework (Requirements 20% | Design 35% | Optimization 25% | Implementation 20%)

### Requirements Analysis
- **Data Requirements**: Entity identification and attribute definition
- **Relationship Mapping**: Entity relationships and cardinality specification
- **Constraint Definition**: Business rules and data validation requirements
- **Performance Requirements**: Query patterns and performance expectations

### Design Phase
- **Normalization**: Database normalization and denormalization decisions
- **Schema Design**: Table structure, column definitions, and data types
- **Index Strategy**: Primary keys, foreign keys, and performance indexes
- **Constraint Implementation**: Check constraints, unique constraints, and triggers

## Optional Flags
--c7: Use to ensure your data model follows best practices for your database type and use case (e.g., PostgreSQL normalization patterns, MongoDB schema design, time-series data modeling)
--seq: Use for complex data models - breaks down into 'identify entities and relationships', 'define constraints and validation', 'optimize for query patterns', 'plan migrations and versioning', 'design backup and recovery'

## Output Requirements
- Comprehensive data model specification with entity relationships
- Database schema with tables, columns, and constraints
- Performance optimization strategy with indexing plan
- Migration plan with implementation timeline

$ARGUMENTS