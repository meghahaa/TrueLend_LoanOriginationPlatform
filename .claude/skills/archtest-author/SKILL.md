---
name: archtest-author
description: Generates and enforces structural ArchUnit architecture tests for layering, immutability, and financial precision rules.
---

# ArchTest Author Skill

This skill provides templates and rules for generating automated structural architecture tests using ArchUnit.

## Architecture Assertions to Generate

1. **Layer Dependency Enforcer**:
   - `controllers` depend on `services`.
   - `services` depend on `domain`.
   - `domain` depends on nothing outside domain.

2. **Fixed-Point Financial Rule**:
   - Classes in `domain` or `services` holding monetary values must declare fields as `BigDecimal`.
   - No primitive `double` or `float` types allowed in domain model fields.

3. **Immutability of Policy & Schedules**:
   - Classes annotated with `@Entity` for policy or schedule must not expose setter methods for version fields.
