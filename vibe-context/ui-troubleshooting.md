# UI Troubleshooting Best Practices

**IF YOU ARE AN AI ASSISTANT YOU MUST FOLLOW THESE RULES**

1. **Always check browser console logs first** when troubleshooting UI issues. Browser console errors often reveal the root cause immediately (CORS errors, API failures, authentication issues, etc.) and can save significant debugging time.

2. **Check browser network tab** to see actual API requests and responses. This shows:
   - Which APIs are being called
   - What status codes are returned (404, 424, 500, etc.)
   - Request/response headers (CORS, authentication)
   - Request/response payloads

3. **Ask the user to share console errors** if they report UI issues. Don't spend time guessing - the browser console usually tells you exactly what's wrong.

4. **Common UI error patterns to look for**:
   - CORS errors → Check API Gateway CORS configuration and Lambda CORS headers
   - 401/403 errors → Authentication/authorization issues
   - 404 errors → API endpoint not found or incorrect URL
   - 424 errors → Backend runtime startup failures (check CloudWatch logs)
   - Network errors → API Gateway or backend service issues

5. **Debugging workflow for UI issues**:
   - Step 1: Check browser console for errors
   - Step 2: Check browser network tab for failed requests
   - Step 3: Check backend logs (CloudWatch, Lambda logs)
   - Step 4: Verify configuration files (aws-exports.json, environment variables)
   - Step 5: Check infrastructure deployment status

6. **Don't assume the UI code is wrong** - often UI issues are caused by:
   - Backend API failures
   - Missing or incorrect configuration
   - Infrastructure deployment issues
   - Authentication/authorization problems

**ALWAYS FOLLOW THESE RULES WHEN TROUBLESHOOTING UI ISSUES**
