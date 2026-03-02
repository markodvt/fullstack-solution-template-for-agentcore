# Deployment Guide - Task 1.7.1: Deploy CDK Stack with Metadata Changes

**Date:** Generated for deployment  
**Task:** 1.7.1 Deploy CDK stack with metadata changes  
**Status:** Ready for deployment

---

## Pre-Deployment Verification

### ✅ Code Compilation
```bash
cd infra-cdk
npm run build
```
**Status:** ✅ PASSED - No TypeScript compilation errors

### ✅ Unit Tests
```bash
cd infra-cdk
npm test
```
**Status:** ✅ PASSED - All 7 tests passed
- Metadata extraction tests: 5 passed
- CDK stack tests: 2 passed

---

## Deployment Instructions

### Step 1: Navigate to Infrastructure Directory
```bash
cd infra-cdk
```

### Step 2: Review Changes (Optional)
Before deploying, you can review what will change:
```bash
npx cdk diff
```

This will show you:
- New S3 bucket for agent source code
- New SSM parameters (tools, model, source-code-url)
- Updated Lambda permissions for S3 access
- Any other infrastructure changes

### Step 3: Deploy the Stack
```bash
npx cdk deploy --all
```

**Expected deployment time:** 5-10 minutes

**What will be deployed:**
1. **S3 Bucket:** `<stack-name>-agent-source-code`
   - Versioned, encrypted, block public access
   - Will contain agent Python source files

2. **SSM Parameters:** For each agent (umich, colorado, coder, orchestrator):
   - `/<stack>/agents/<agent-name>/tools` - JSON array of tools
   - `/<stack>/agents/<agent-name>/model` - Model ID string
   - `/<stack>/agents/<agent-name>/source-code-url` - S3 URL

3. **Lambda Permissions:** agent-discovery Lambda
   - S3 GetObject permission
   - S3 ListBucket permission

4. **S3 Deployments:** Agent source files uploaded to S3
   - `agents/umich/umich_agent.py`
   - `agents/colorado/colorado_agent.py`
   - `agents/coder/coder_agent.py`
   - `agents/orchestrator/orchestrator_agent.py`

### Step 4: Monitor Deployment
Watch the CloudFormation events in the AWS Console or in your terminal. The deployment will:
1. Create/update the S3 bucket
2. Upload agent source files to S3
3. Create SSM parameters with metadata
4. Update Lambda IAM permissions
5. Deploy any other stack changes

---

## Post-Deployment Verification

### Verification 1: S3 Bucket Created
```bash
# List S3 buckets to verify creation
aws s3 ls | grep agent-source-code

# Expected output:
# 2024-XX-XX XX:XX:XX <stack-name>-agent-source-code
```

### Verification 2: Agent Source Files Uploaded to S3
```bash
# Get your stack name from config.yaml
STACK_NAME=$(grep stack_name_base infra-cdk/config.yaml | awk '{print $2}' | tr -d '"')

# List all agent files in S3
aws s3 ls s3://${STACK_NAME}-agent-source-code/agents/ --recursive

# Expected output:
# agents/umich/umich_agent.py
# agents/colorado/colorado_agent.py
# agents/coder/coder_agent.py
# agents/orchestrator/orchestrator_agent.py
```

### Verification 3: SSM Parameters Include New Fields
```bash
# Get your stack name
STACK_NAME=$(grep stack_name_base infra-cdk/config.yaml | awk '{print $2}' | tr -d '"')

# List all agent parameters
aws ssm get-parameters-by-path --path "/${STACK_NAME}/agents" --recursive

# Verify each agent has these parameters:
# - /<stack>/agents/<agent>/tools
# - /<stack>/agents/<agent>/model
# - /<stack>/agents/<agent>/source-code-url
# - /<stack>/agents/<agent>/description (existing)
# - /<stack>/agents/<agent>/runtime-arn (existing)
# - /<stack>/agents/<agent>/status (existing)
```

**Example verification for a specific agent:**
```bash
# Check umich agent parameters
aws ssm get-parameters-by-path --path "/${STACK_NAME}/agents/umich" --recursive

# Expected parameters:
# - tools: ["http_request", "get_current_time"]
# - model: "us.anthropic.claude-sonnet-4-5-20250929-v1:0"
# - source-code-url: "s3://<bucket>/agents/umich/umich_agent.py"
```

### Verification 4: Verify SSM Parameter Content
```bash
# Check tools parameter (should be JSON array)
aws ssm get-parameter --name "/${STACK_NAME}/agents/umich/tools" --query 'Parameter.Value' --output text

# Expected: ["http_request","get_current_time"]

# Check model parameter (should be string)
aws ssm get-parameter --name "/${STACK_NAME}/agents/umich/model" --query 'Parameter.Value' --output text

# Expected: us.anthropic.claude-sonnet-4-5-20250929-v1:0

# Check source-code-url parameter (should be S3 URL)
aws ssm get-parameter --name "/${STACK_NAME}/agents/umich/source-code-url" --query 'Parameter.Value' --output text

# Expected: s3://<stack-name>-agent-source-code/agents/umich/umich_agent.py
```

### Verification 5: Verify S3 File Content
```bash
# Download a sample file to verify content integrity
aws s3 cp s3://${STACK_NAME}-agent-source-code/agents/umich/umich_agent.py /tmp/umich_agent.py

# Verify it's a valid Python file
head -20 /tmp/umich_agent.py

# Expected: Should show Python code with imports and agent definition
```

### Verification 6: Check CloudWatch Logs for Deployment Errors
```bash
# Get the agent-discovery Lambda function name
LAMBDA_NAME=$(aws lambda list-functions --query "Functions[?contains(FunctionName, 'agent-discovery')].FunctionName" --output text)

# Check recent logs
aws logs tail /aws/lambda/${LAMBDA_NAME} --since 10m

# Look for any ERROR or WARNING messages related to S3 or metadata
```

### Verification 7: Test Agent Discovery API
```bash
# Get your API Gateway URL
API_URL=$(aws cloudformation describe-stacks --stack-name ${STACK_NAME}-BackendStack --query "Stacks[0].Outputs[?OutputKey=='ApiUrl'].OutputValue" --output text)

# Get a valid JWT token (you'll need to authenticate first)
# This depends on your Cognito setup - you may need to use the frontend to get a token

# Test the API (replace <JWT_TOKEN> with your actual token)
curl -H "Authorization: Bearer <JWT_TOKEN>" ${API_URL}/agents | jq

# Expected response should include for each agent:
# - name
# - description
# - model (NEW)
# - tools (NEW - array)
# - sourceCode (NEW - full Python source)
# - sourceCodeUrl (NEW - presigned S3 URL)
# - runtimeArn
# - status
```

---

## Success Criteria Checklist

Use this checklist to verify successful deployment:

- [ ] **S3 Bucket Created:** Bucket `<stack-name>-agent-source-code` exists
- [ ] **Agent Files Uploaded:** All 4 agent files are in S3 under `agents/` prefix
- [ ] **SSM Parameters Created:** Each agent has `/tools`, `/model`, and `/source-code-url` parameters
- [ ] **Tools Parameter Valid:** Contains JSON array of tool names
- [ ] **Model Parameter Valid:** Contains model ID string
- [ ] **Source Code URL Valid:** Contains S3 URL in format `s3://bucket/agents/name/name_agent.py`
- [ ] **S3 File Content Valid:** Downloaded file contains valid Python code
- [ ] **No CloudWatch Errors:** No ERROR messages in agent-discovery Lambda logs
- [ ] **API Returns New Fields:** `/api/agents` endpoint returns `tools`, `model`, `sourceCode`, `sourceCodeUrl`
- [ ] **Presigned URLs Work:** `sourceCodeUrl` is accessible (returns 200)

---

## Troubleshooting

### Issue: S3 Bucket Not Created
**Symptoms:** `aws s3 ls` doesn't show the bucket

**Solutions:**
1. Check CloudFormation stack events for errors
2. Verify IAM permissions for S3 bucket creation
3. Check if bucket name conflicts with existing bucket

### Issue: Agent Files Not Uploaded
**Symptoms:** S3 bucket is empty or missing files

**Solutions:**
1. Check CDK deployment logs for S3 deployment errors
2. Verify agent files exist in `patterns/*/agents/` directories
3. Re-run deployment: `npx cdk deploy --all`

### Issue: SSM Parameters Missing
**Symptoms:** `get-parameters-by-path` returns fewer parameters than expected

**Solutions:**
1. Check CloudFormation stack events for SSM errors
2. Verify metadata extraction succeeded (check CDK logs)
3. Check if agent files are readable during deployment

### Issue: API Doesn't Return New Fields
**Symptoms:** `/api/agents` response missing `tools`, `model`, or `sourceCode`

**Solutions:**
1. Verify Lambda has S3 permissions (check IAM role)
2. Check Lambda CloudWatch logs for S3 access errors
3. Verify SSM parameters exist and are readable
4. Test Lambda directly with a test event

### Issue: Presigned URLs Don't Work
**Symptoms:** `sourceCodeUrl` returns 403 or 404

**Solutions:**
1. Verify Lambda has `s3:GetObject` permission
2. Check if S3 bucket policy blocks access
3. Verify file exists in S3 at the specified path
4. Check presigned URL expiration (1 hour default)

---

## Rollback Instructions

If deployment fails or causes issues:

```bash
# Rollback to previous version
cd infra-cdk
npx cdk deploy --all --rollback

# Or destroy and redeploy
npx cdk destroy --all
npx cdk deploy --all
```

**Note:** Destroying the stack will delete all data including the S3 bucket and SSM parameters.

---

## Next Steps

After successful deployment and verification:

1. **Mark Task Complete:** Update task 1.7.1 status to completed
2. **Proceed to Task 1.7.2:** Test agent discovery API with new fields
3. **Update Frontend:** Ensure frontend can display new metadata fields
4. **User Acceptance:** Have users verify enhanced agent metadata in UI

---

## Requirements Validated

This deployment satisfies the following requirements:

- **Requirement 1.4:** Agent metadata extraction from source code
- **Requirement 1.5:** Tools list extraction and storage
- **Requirement 1.6:** Model ID extraction and storage
- **Requirement 3.4:** Tools list display in UI (backend support)
- **Requirement 3.5:** Model specification display (backend support)
- **Requirement 3.6:** Source code storage and retrieval

---

## Additional Resources

- **Implementation Guide:** `.kiro/dev-history/enhanced-agent-ui/implementation-guide.md`
- **CDK README:** `infra-cdk/README.md`
- **AWS CDK Documentation:** https://docs.aws.amazon.com/cdk/
- **AWS S3 Documentation:** https://docs.aws.amazon.com/s3/
- **AWS SSM Documentation:** https://docs.aws.amazon.com/systems-manager/

---

**Ready for deployment!** Follow the steps above and verify each checkpoint.
