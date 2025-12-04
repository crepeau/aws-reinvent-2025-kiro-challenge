---
inclusion: fileMatch
fileMatchPattern: '**/*{aws,cdk,infrastructure,deploy}*'
---

# AWS Credentials Management

## Important Reminder

When running AWS CLI commands or CDK operations, credentials may not persist across new terminal sessions.

**Before executing AWS commands:**
1. Check if AWS credentials are needed for the operation
2. If credentials are required, prompt the user to provide them or confirm they're set
3. Suggest the user runs AWS commands in their existing terminal if credentials are already configured there

## Common AWS Operations Requiring Credentials

- `aws` CLI commands
- `cdk deploy`, `cdk synth`, `cdk diff`
- Any infrastructure deployment or AWS API calls

## Recommended Approach

Instead of running AWS commands directly, provide the command and ask the user to run it in their terminal where credentials are already configured, OR prompt them to set credentials first.
