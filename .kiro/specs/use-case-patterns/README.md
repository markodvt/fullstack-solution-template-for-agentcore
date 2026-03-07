# Use Case Patterns

## Status
Concept stage - spec not yet written

## Purpose

This feature will provide reusable templates and patterns for common business use cases, enabling teams to quickly deploy domain-specific agent configurations without building from scratch.

## Concept

While FAST Agent Gallery provides the infrastructure for multi-agent systems, teams still need to configure agents, tools, and workflows for their specific use cases. Use Case Patterns will provide pre-built templates that include:

- **Agent configurations**: Pre-defined agent personalities, system prompts, and capabilities
- **Tool bundles**: Curated sets of tools relevant to the use case
- **Sample data**: Synthetic or example data for testing
- **Deployment configs**: Ready-to-use CDK configurations
- **Documentation**: Best practices and customization guides

## Example Use Cases

### Customer Support Pattern
- Ticket classification agent
- Response generation agent
- Knowledge base search tools
- Sentiment analysis tools
- Escalation routing logic

### Document Processing Pattern
- PDF extraction agent
- Form filling agent
- Data validation agent
- Multi-document synthesis agent
- OCR and text extraction tools

### Data Analysis Pattern
- SQL query generation agent
- Visualization agent
- Statistical analysis tools
- Report generation tools
- Data quality checking

### Code Review Pattern
- PR analysis agent
- Security scanning agent
- Code quality agent
- Suggestion generation tools
- Git integration tools

## Benefits

1. **Faster Time-to-Value**: Deploy a working use case in minutes instead of days
2. **Best Practices Built-In**: Leverage proven patterns instead of trial-and-error
3. **Customization Starting Point**: Easier to modify a working example than start from scratch
4. **Learning Resource**: Teams can study patterns to understand effective agent design
5. **Consistency**: Standardized approaches across teams and use cases

## Technical Approach

Patterns will be organized as:

```
patterns/
├── use-case-customer-support/
│   ├── agents/
│   │   ├── classifier/
│   │   ├── responder/
│   │   └── escalation/
│   ├── tools/
│   ├── sample-data/
│   ├── config.yaml
│   └── README.md
├── use-case-document-processing/
│   └── ...
└── use-case-data-analysis/
    └── ...
```

Each pattern will include:
- Complete agent implementations
- Tool definitions
- Sample data for testing
- Configuration file
- Documentation with customization guide

## Integration with Existing Features

- Leverages the multi-agent orchestration pattern (Epic 1)
- Uses the same CDK deployment infrastructure
- Appears in the agent gallery UI
- Benefits from observability and memory features
- Can be extended with additional tools from the tool ecosystem

## Next Steps

1. Identify 3-5 high-value use cases to prioritize
2. Create detailed requirements document
3. Design pattern structure and configuration format
4. Implement first pattern as reference
5. Document pattern creation guide for community contributions

## Related Specs

- [Multi-Agent Orchestration Pattern](../multi-agent-orchestration-pattern/) - Foundation for use case patterns
- [Lending Use Case](../lending/) - Domain-specific example (mortgage applications)
- [Connect Admin](../connect-admin/) - Alternative channel for use case access

## Questions to Resolve

1. Should patterns be selectable at deployment time via config, or deployed as separate stacks?
2. How do we version patterns as they evolve?
3. Should patterns support "mixins" (e.g., add observability tools to any pattern)?
4. How do we handle pattern dependencies (e.g., requires Neptune, requires specific AWS services)?
5. Should we support pattern composition (combine multiple patterns)?
