#!/bin/bash

echo "🔍 Verifying Azure Infrastructure for Decipherworld"
echo "=================================================="

# Check if we're logged into Azure
echo "1. Checking Azure login status..."
if az account show > /dev/null 2>&1; then
    CURRENT_SUBSCRIPTION=$(az account show --query name -o tsv)
    echo "✅ Logged into Azure subscription: $CURRENT_SUBSCRIPTION"
else
    echo "❌ Not logged into Azure. Run 'az login' first."
    exit 1
fi

echo ""
echo "2. Checking Resource Group..."
RG_EXISTS=$(az group exists --name rg-decipherworld-prod)
if [ "$RG_EXISTS" = "true" ]; then
    echo "✅ Resource group 'rg-decipherworld-prod' exists"
    LOCATION=$(az group show --name rg-decipherworld-prod --query location -o tsv)
    echo "   📍 Location: $LOCATION"
else
    echo "❌ Resource group 'rg-decipherworld-prod' not found"
    exit 1
fi

echo ""
echo "3. Checking PostgreSQL Server..."
PG_SERVER=$(az postgres flexible-server show --resource-group rg-decipherworld-prod --name decipherworld-db-server-ci01 --query state -o tsv 2>/dev/null)
if [ "$PG_SERVER" = "Ready" ]; then
    echo "✅ PostgreSQL server 'decipherworld-db-server-ci01' is ready"
    
    # Get connection details
    PG_HOST=$(az postgres flexible-server show --resource-group rg-decipherworld-prod --name decipherworld-db-server-ci01 --query fullyQualifiedDomainName -o tsv)
    PG_VERSION=$(az postgres flexible-server show --resource-group rg-decipherworld-prod --name decipherworld-db-server-ci01 --query version -o tsv)
    PG_SKU=$(az postgres flexible-server show --resource-group rg-decipherworld-prod --name decipherworld-db-server-ci01 --query sku.name -o tsv)
    
    echo "   🌐 Host: $PG_HOST"
    echo "   🔢 Version: PostgreSQL $PG_VERSION"
    echo "   💻 SKU: $PG_SKU"
elif [ -z "$PG_SERVER" ]; then
    echo "❌ PostgreSQL server 'decipherworld-db-server-ci01' not found"
    exit 1
else
    echo "⚠️  PostgreSQL server state: $PG_SERVER (may still be deploying)"
fi

echo ""
echo "4. Checking Database..."
DB_EXISTS=$(az postgres flexible-server db show --resource-group rg-decipherworld-prod --server-name decipherworld-db-server-ci01 --database-name decipherworld --query name -o tsv 2>/dev/null)
if [ "$DB_EXISTS" = "decipherworld" ]; then
    echo "✅ Database 'decipherworld' exists"
else
    echo "❌ Database 'decipherworld' not found"
    exit 1
fi

echo ""
echo "5. Checking App Service Plan..."
APP_PLAN=$(az appservice plan show --resource-group rg-decipherworld-prod --name decipherworld-app-plan --query sku.name -o tsv 2>/dev/null)
if [ -n "$APP_PLAN" ]; then
    echo "✅ App Service Plan 'decipherworld-app-plan' exists"
    echo "   💻 SKU: $APP_PLAN"
    
    PLAN_OS=$(az appservice plan show --resource-group rg-decipherworld-prod --name decipherworld-app-plan --query kind -o tsv)
    echo "   🐧 OS: $PLAN_OS"
else
    echo "❌ App Service Plan 'decipherworld-app-plan' not found"
    exit 1
fi

echo ""
echo "6. Checking Web App..."
WEB_APP=$(az webapp show --resource-group rg-decipherworld-prod --name decipherworld-app --query state -o tsv 2>/dev/null)
if [ "$WEB_APP" = "Running" ]; then
    echo "✅ Web App 'decipherworld-app' is running"
    
    # Get app details
    APP_URL=$(az webapp show --resource-group rg-decipherworld-prod --name decipherworld-app --query defaultHostName -o tsv)
    RUNTIME=$(az webapp config show --resource-group rg-decipherworld-prod --name decipherworld-app --query linuxFxVersion -o tsv)
    
    echo "   🌐 Default URL: https://$APP_URL"
    echo "   🐍 Runtime: $RUNTIME"
    
elif [ -z "$WEB_APP" ]; then
    echo "❌ Web App 'decipherworld-app' not found"
    exit 1
else
    echo "⚠️  Web App state: $WEB_APP"
fi

echo ""
echo "7. Checking PostgreSQL Firewall Rules..."
FIREWALL_RULES=$(az postgres flexible-server firewall-rule list --resource-group rg-decipherworld-prod --name decipherworld-db-server-ci01 --query "length(@)" -o tsv 2>/dev/null)
if [ "$FIREWALL_RULES" -gt 0 ]; then
    echo "✅ PostgreSQL firewall has $FIREWALL_RULES rule(s)"
    az postgres flexible-server firewall-rule list --resource-group rg-decipherworld-prod --name decipherworld-db-server-ci01 --query "[].{Name:name,StartIP:startIpAddress,EndIP:endIpAddress}" -o table
else
    echo "⚠️  No firewall rules found (may need to configure for App Service access)"
fi

echo ""
echo "=================================================="
echo "🎯 INFRASTRUCTURE VERIFICATION SUMMARY"
echo "=================================================="

# Generate connection string for next steps
echo "📝 CONNECTION STRING FOR APP SERVICE:"
echo "DATABASE_URL=\"postgresql://decipheradmin:YourStrongPassword123!@$PG_HOST:5432/decipherworld?sslmode=require\""

echo ""
echo "🌐 TEST YOUR APP SERVICE:"
echo "https://$APP_URL"

echo ""
echo "✅ Infrastructure verification complete!"
echo "🎯 Ready for application deployment and configuration!"