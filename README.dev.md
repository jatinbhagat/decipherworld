# Decipherworld - Local Development Setup

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run database migrations:**
   ```bash
   python manage.py migrate
   ```

3. **Start development server:**
   ```bash
   python dev.py
   # OR
   python manage.py runserver
   ```

4. **Access the application:**
   - Main site: http://127.0.0.1:8000/
   - Admin panel: http://127.0.0.1:8000/admin/
   - Admin login: `admin` / `admin123`

## Development Settings

- **Settings file**: `decipherworld/settings/local.py`
- **Database**: Azure PostgreSQL (production) or SQLite (local fallback)
- **Debug mode**: Enabled
- **Static files**: Served by Django development server
- **Email backend**: Console (emails printed to terminal)

## Environment Variables (Optional)

Create a `.env` file and update with your Azure PostgreSQL credentials if you want to test with production database locally:

```bash
# Create .env file with Azure database credentials
DATABASE_URL=postgresql://decipheradmin:PASSWORD@decipherworld-db-server-ci01.postgres.database.azure.com:5432/decipherworld?sslmode=require
```

## Common Django Commands

```bash
# Create migrations after model changes
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic

# Run Django shell
python manage.py shell

# Check for issues
python manage.py check
```

## Project Structure

```
decipherworld/
├── manage.py              # Django management script
├── dev.py                 # Development server script
├── decipherworld/         # Main project package
│   ├── settings/
│   │   ├── base.py        # Common settings
│   │   ├── local.py       # Local development
│   │   ├── production.py  # Production settings
│   │   └── azure.py       # Azure-specific settings
│   ├── urls.py
│   └── wsgi.py
├── core/                  # Main application
│   ├── models.py          # Course, DemoRequest models
│   ├── views.py           # Class-based views
│   ├── forms.py           # Django forms
│   ├── admin.py           # Admin interface
│   └── urls.py
├── templates/             # HTML templates
├── static/               # CSS, JS, images
└── requirements.txt      # Python dependencies
```

## Debugging Tips

1. **Enable Django Debug Toolbar** (optional):
   ```bash
   pip install django-debug-toolbar
   ```
   Then uncomment the debug toolbar lines in `local.py`

2. **View logs**: Check the console where you run the server

3. **Database issues**: Delete `db.sqlite3` and run `python manage.py migrate` to recreate

4. **Static files issues**: Run `python manage.py collectstatic`

## Testing Templates

The project includes basic templates in the `templates/` directory. You can test:
- Homepage: http://127.0.0.1:8000/
- Courses: http://127.0.0.1:8000/courses/
- Contact: http://127.0.0.1:8000/contact/

## Next Steps for Production

When ready to deploy to Azure:
1. Set environment variables in Azure App Service configuration
2. Use `decipherworld.settings.production` 
3. Ensure Azure PostgreSQL database is configured
4. Deploy using Azure App Service deployment center or GitHub Actions