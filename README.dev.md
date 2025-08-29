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
- **Database**: SQLite (`db.sqlite3`) - automatically created
- **Debug mode**: Enabled
- **Static files**: Served by Django development server
- **Email backend**: Console (emails printed to terminal)

## Environment Variables (Optional)

Copy `.env.local` to `.env` and update with your Supabase credentials if you want to test Supabase integration:

```bash
cp .env.local .env
# Edit .env with your actual Supabase credentials
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
│   │   └── production.py  # Production settings
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

When ready to deploy:
1. Set environment variables in Render.com dashboard
2. Use `decipherworld.settings.production` 
3. Connect to Supabase PostgreSQL database
4. Deploy using the configured `render.yaml`