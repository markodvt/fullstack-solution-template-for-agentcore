---
inclusion: fileMatch
fileMatchPattern: 'frontend/'
---

# UI Troubleshooting Best Practices

**IF YOU ARE AN AI ASSISTANT YOU MUST FOLLOW THESE RULES**

## Debugging Workflow

### Step 1: Check Browser Console Logs First

Browser console errors reveal the root cause immediately:
- CORS errors
- API failures
- Authentication issues
- JavaScript errors
- Network failures

**Always ask the user to share console errors** if they report UI issues. Don't guess - the console tells you exactly what's wrong.

### Step 2: Check Browser Network Tab

The Network tab shows:
- Which APIs are being called
- Status codes (404, 424, 500, etc.)
- Request/response headers (CORS, authentication)
- Request/response payloads
- Timing information

### Step 3: Check Backend Logs

If API calls are failing:
- Check CloudWatch logs for Lambda functions
- Look for runtime errors or exceptions
- Verify environment variables are set
- Check IAM permissions

### Step 4: Verify Configuration

Check configuration files:
- `frontend/public/aws-exports.json` - API endpoints, Cognito config
- Environment variables
- CDK deployment outputs

### Step 5: Check Infrastructure

Verify deployment status:
- API Gateway routes are deployed
- Lambda functions are deployed and healthy
- Cognito user pool is configured
- SSM parameters are set correctly

---

## Common UI Error Patterns

### CORS Errors

**Symptoms:**
```
Access to fetch at 'https://api.example.com' from origin 'http://localhost:3000' 
has been blocked by CORS policy
```

**Causes:**
- Lambda missing CORS headers in response
- API Gateway CORS not configured
- OPTIONS method not configured

**Solutions:**
- Ensure Lambda returns CORS headers in ALL responses (success and error)
- Configure API Gateway CORS settings
- Add OPTIONS method to API Gateway routes

### 401/403 Errors

**Symptoms:**
- "Unauthorized" or "Forbidden" errors
- User redirected to login page
- API calls rejected

**Causes:**
- JWT token expired or invalid
- Cognito authorizer misconfigured
- User lacks required permissions

**Solutions:**
- Verify JWT token is included in request headers
- Check Cognito authorizer configuration
- Ensure user has proper IAM/Cognito permissions
- Check token expiration and refresh logic

### 404 Errors

**Symptoms:**
- "Not Found" errors
- API endpoint returns 404

**Causes:**
- API Gateway route not deployed
- Incorrect endpoint URL in aws-exports.json
- SSM parameter name doesn't follow convention

**Solutions:**
- Verify API Gateway route exists and is deployed
- Check endpoint URL in aws-exports.json
- Ensure SSM parameter follows naming convention: `/fast/${deploymentName}/api/{api-name}-endpoint`

### 424 Errors

**Symptoms:**
- "Failed Dependency" errors
- Backend service unavailable

**Causes:**
- Lambda runtime startup failure
- Missing dependencies
- Configuration errors
- IAM permission issues

**Solutions:**
- Check Lambda CloudWatch logs for startup errors
- Verify Lambda has required permissions
- Check environment variables are set correctly
- Ensure dependencies are installed in Lambda layer/package

### Network Errors

**Symptoms:**
- "Network request failed"
- "Failed to fetch"
- Timeout errors

**Causes:**
- API Gateway or backend service down
- Network connectivity issues
- Request timeout

**Solutions:**
- Check API Gateway status
- Verify backend services are running
- Check CloudWatch logs for errors
- Increase timeout if needed

---

## Best Practices

### ✅ DO:
- Check browser console first
- Use browser network tab to inspect requests
- Ask users to share console errors
- Verify configuration before assuming code issues
- Check backend logs for API failures
- Test with browser dev tools open

### ❌ DON'T:
- Assume the UI code is wrong (often it's backend/config)
- Skip checking console errors
- Ignore network tab information
- Guess at the problem without data
- Make changes without understanding root cause

---

## Debugging Checklist

When troubleshooting UI issues, check in this order:

1. ☐ Browser console errors
2. ☐ Browser network tab (failed requests)
3. ☐ Backend CloudWatch logs
4. ☐ Configuration files (aws-exports.json)
5. ☐ Infrastructure deployment status
6. ☐ API Gateway routes and CORS
7. ☐ Lambda function health and permissions
8. ☐ Cognito configuration

**Most UI issues are caused by backend/config problems, not frontend code.**

**ALWAYS FOLLOW THESE RULES WHEN TROUBLESHOOTING UI ISSUES**
