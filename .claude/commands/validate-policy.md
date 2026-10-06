# Validate Policy Command

Execute policy validation checks across all JSON policy configuration files in the project.

```bash
python3 scripts/run_agent.py --task validate-policy
```

## Description
This command invokes the `policy-validator-agent` to verify schema compliance, numeric threshold bounds, and version immutability across all policy files.
