# Supabase PostgreSQL Setup Guide

## Quick Setup Instructions

### 1. Get Your Supabase Database Credentials

1. Go to your [Supabase Dashboard](https://supabase.com/dashboard)
2. Select your project
3. Navigate to **Settings** → **Database**
4. Copy the **Connection string** (it looks like this):
   ```
   postgresql://postgres.[REF]:[PASSWORD]@[HOST].supabase.co:5432/postgres
   ```

### 2. Update Your .env File

Replace the placeholder values in your `.env` file with real Supabase credentials:

```env
# Replace this with your actual Supabase connection string
DATABASE_URL=postgresql://postgres.[your-actual-ref]:[your-actual-password]@[your-actual-host].supabase.co:5432/postgres

# Supabase API keys (from Settings → API)
SUPABASE_URL=https://[your-project-ref].supabase.co
SUPABASE_ANON_KEY=[your-actual-anon-key]
```

### 3. Run Database Migrations

After updating your `.env` file:

```bash
python manage.py migrate
python manage.py createsuperuser
```

### 4. Test the Connection

```bash
python manage.py check
python manage.py runserver
```

## Alternative: Temporary SQLite Fallback

If you want to quickly test without Supabase setup, you can temporarily revert to SQLite:

1. Comment out the PostgreSQL configuration in `decipherworld/settings/local.py`
2. Uncomment the SQLite configuration
3. Run migrations: `python manage.py migrate`

## Troubleshooting

### Error: "This string is not a valid url"
- Check that your DATABASE_URL doesn't have placeholder brackets like `[your-password]`
- Ensure all parts of the URL are filled in with actual values

### Error: "connection to server failed"
- Verify your Supabase project is active
- Check that your password is correct
- Ensure you're using the correct connection string format

### Error: "SSL connection required"
- This is normal - Supabase requires SSL connections
- The configuration already includes `sslmode=require`

## Benefits of Using Supabase PostgreSQL

✅ **Consistent Environment**: Same database engine in development and production  
✅ **PostgreSQL Features**: JSON fields, advanced queries, etc.  
✅ **Supabase Features**: Real-time subscriptions, Row Level Security  
✅ **No Migration Issues**: Schema changes work seamlessly across environments  
✅ **Team Collaboration**: Shared database for team development  

## Need Help?

If you're still having issues:
1. Check your Supabase dashboard for any service interruptions
2. Verify your project is in the correct region
3. Try using the direct database URL instead of the pooled URL
4. Contact Supabase support if the database service seems down