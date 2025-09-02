# Azure Setup Commands for Decipherworld Migration

## Prerequisites
1. Install Azure CLI: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli
2. Login to Azure: `az login`
3. Select your subscription: `az account set --subscription "Your Subscription Name"`

## Step 3A: Create Resource Group
```bash
# Create resource group in East US (you can change region if preferred)
az group create \
    --name rg-decipherworld-prod \
    --location eastus \
    --tags project=decipherworld environment=production
```

## Step 3B: Create Azure PostgreSQL Database
```bash
# Create PostgreSQL server
az postgres flexible-server create \
    --resource-group rg-decipherworld-prod \
    --name decipherworld-db-server \
    --location eastus \
    --admin-user decipheradmin \
    --admin-password "YourStrongPassword123!" \
    --sku-name Standard_B1ms \
    --tier Burstable \
    --compute-tier Burstable \
    --storage-size 32 \
    --version 13 \
    --public-access 0.0.0.0 \
    --tags project=decipherworld environment=production

# Create database
az postgres flexible-server db create \
    --resource-group rg-decipherworld-prod \
    --server-name decipherworld-db-server \
    --database-name decipherworld
```

## Step 3C: Create App Service Plan and Web App
```bash
# Create App Service Plan (Linux, Python)
az appservice plan create \
    --resource-group rg-decipherworld-prod \
    --name decipherworld-app-plan \
    --location eastus \
    --sku B1 \
    --is-linux \
    --tags project=decipherworld environment=production

# Create Web App
az webapp create \
    --resource-group rg-decipherworld-prod \
    --plan decipherworld-app-plan \
    --name decipherworld-app \
    --runtime "PYTHON:3.11" \
    --tags project=decipherworld environment=production
```

## Step 3D: Configure Custom Domain (Optional - for later)
```bash
# Add custom domain (after DNS is configured)
az webapp config hostname add \
    --webapp-name decipherworld-app \
    --resource-group rg-decipherworld-prod \
    --hostname decipherworld.com

# Enable HTTPS
az webapp config ssl bind \
    --resource-group rg-decipherworld-prod \
    --name decipherworld-app \
    --certificate-thumbprint [THUMBPRINT] \
    --ssl-type SNI
```

## Important Information After Creation:

### Database Connection Details:
- **Server**: `decipherworld-db-server.postgres.database.azure.com`
- **Database**: `decipherworld`
- **Username**: `decipheradmin`
- **Password**: `YourStrongPassword123!` (change this!)
- **Port**: `5432`
- **SSL Mode**: `require`

### App Service Details:
- **App Name**: `decipherworld-app`
- **URL**: `https://decipherworld-app.azurewebsites.net`
- **Deployment**: GitHub Actions or local Git

### Connection String Format:
```
DATABASE_URL="postgresql://decipheradmin:YourStrongPassword123!@decipherworld-db-server.postgres.database.azure.com:5432/decipherworld?sslmode=require"
```

## Security Notes:
1. **Change the database password** to something strong and unique
2. **Restrict database firewall** to only App Service IP after deployment
3. **Use Azure Key Vault** for secrets in production
4. **Enable Application Insights** for monitoring

## Cost Estimate:
- **PostgreSQL Flexible Server (B1ms)**: ~$12-15/month
- **App Service Plan (B1)**: ~$13-15/month  
- **Total**: ~$25-30/month

Run these commands in your terminal to create the Azure infrastructure!