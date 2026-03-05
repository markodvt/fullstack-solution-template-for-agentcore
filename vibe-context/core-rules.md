# Core Development Rules

**IF YOU ARE AN AI ASSISTANT YOU MUST FOLLOW THESE RULES**

## Essential Practices

1. Always read READMEs when working in a new section (e.g., `frontend/README.md`, `infra-cdk/README.md`)
2. Follow existing design patterns and coding styles - refer to docs/ folder for domain-expert guidance
3. When searching files, always exclude noise: `| grep -v "cdk.out" | grep -v "node_modules"`
4. Test new features locally or with unit tests whenever possible
5. Run `make all` periodically - linting and tests must pass for CI/CD

## Code Quality Standards

1. Add docstrings to every function explaining purpose, input types, and outputs
2. Use explicit strong types in method signatures and return types
3. Comment non-obvious code thoroughly - assume moderate understanding
4. Fail loudly - avoid silent fallbacks to defaults
5. Prefer named parameters over positional parameters

## Documentation Priority

Documentation in `docs/` folder is authoritative - always consult it before implementing. For example, working with AgentCore Gateway? Read `docs/GATEWAY.md` first.

**ALWAYS FOLLOW THESE RULES WHEN YOU WORK IN THIS PROJECT**
