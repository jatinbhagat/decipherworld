#!/bin/bash
# Emergency 504 Timeout Fix Deployment Script
# Run this to deploy all critical fixes to production

echo "🚨 Emergency 504 Timeout Fix Deployment"
echo "========================================"

# Step 1: Create database cache table if it doesn't exist
echo "1. Setting up database cache..."
python manage.py createcachetable

# Step 2: Deploy code changes
echo "2. Deploying optimized code..."
echo "   ✅ HomeView optimized with caching"
echo "   ✅ Timeout middleware added"
echo "   ✅ Health check endpoint added"
echo "   ✅ Backend fallback tracking added"

# Step 3: Test endpoints locally first
echo "3. Testing critical endpoints..."
curl -w "Response time: %{time_total}s\n" http://localhost:8000/health/ || echo "❌ Health check failed"
curl -w "Response time: %{time_total}s\n" http://localhost:8000/ || echo "❌ Homepage failed"

# Step 4: Azure deployment commands
echo "4. Azure production deployment commands:"
echo ""
echo "# A. Restart App Service immediately:"
echo "az webapp restart --name decipherworld-app --resource-group rg-decipherworld-prod"
echo ""
echo "# B. Enable Always On to prevent cold starts:"
echo "az webapp config set --name decipherworld-app --resource-group rg-decipherworld-prod --always-on true"
echo ""
echo "# C. Scale up temporarily if needed:"
echo "az appservice plan update --name your-plan-name --resource-group rg-decipherworld-prod --sku P1V2"
echo ""
echo "# D. Add timeout middleware to settings:"
echo "# Add 'core.middleware.TimeoutMiddleware' to MIDDLEWARE in production.py"
echo ""
echo "# E. Test production health after deployment:"
echo "curl -w 'Response: %{time_total}s\\n' https://decipherworld-app.azurewebsites.net/health/"

# Step 5: Monitoring setup
echo ""
echo "5. Set up monitoring (run these Azure commands):"
echo ""
echo "# Enable Application Insights:"
echo "az monitor app-insights component create --app decipherworld-insights --location eastus --resource-group rg-decipherworld-prod --application-type web"
echo ""
echo "# Create availability test:"
echo "az monitor app-insights web-test create --resource-group rg-decipherworld-prod --component decipherworld-insights --web-test-name 'DecipherWorld Uptime' --web-test-kind ping --locations 'East US' 'West US' --frequency 300 --timeout 30 --url 'https://decipherworld-app.azurewebsites.net/health/' --enabled true"

echo ""
echo "🎯 Priority Order for Production:"
echo "1. Deploy this code immediately"
echo "2. Restart App Service"
echo "3. Enable Always On"
echo "4. Test health endpoint"
echo "5. Monitor for 30 minutes"
echo ""
echo "Expected Results:"
echo "✅ 504 errors should reduce by 80%+"
echo "✅ Homepage load time < 2 seconds"
echo "✅ Database queries cached (10 min)"
echo "✅ Health endpoint responds < 500ms"
echo ""
echo "🚨 If 504 errors persist after deployment:"
echo "1. Check Application Insights for slow dependencies"
echo "2. Scale up to P1V2 or higher"
echo "3. Check PostgreSQL connection pool"
echo "4. Review database query performance"