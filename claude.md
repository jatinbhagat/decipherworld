# claude_code.md – Prompts for Django + Supabase Website Code Generation

## 1. Project Setup
Prompt:  
Generate step-by-step commands to initialize a Django project called `decipherworld`, add a `core` app, set up for deployment on Render.com, and connect with Supabase for authentication and data (PostgreSQL). Assume a fresh environment.

---

## 2. Django Project Structure
Prompt:  
Generate the recommended Django project folder structure for a site with landing pages, signup/login, course listings, and a contact/demo form, using templates and class-based views. Use mobile-first design conventions.

---

## 3. Models & Supabase Integration
Prompt:  
Generate Django models for Courses, Schools, Teachers, DemoRequests. Show how to integrate with Supabase for authentication and CRUD, using `supabase-py` or recommended approach.

---

## 4. URLs, Views & Template Setup
Prompt:  
Generate example Django URLs, views (CBV where possible), and templates for:  
- Homepage displaying product highlights and CTAs  
- Courses page listing all courses dynamically  
- Teacher/Admin signup/login with Supabase auth  
- Contact/demo request form  
- Success page/messages

---

## 5. HTML & Tailwind CSS
Prompt:  
Generate responsive, minimal HTML + Tailwind CSS templates for each section (hero, mission, courses, product blurbs, signup, contact form, footer), inserting previously generated site copy in the appropriate places.

---

## 6. Demo Request Form Logic
Prompt:  
Generate Django form and view logic for submitting demo/contact requests, saving to Supabase, with error handling and success feedback on UI.

---

## 7. Deployment
Prompt:  
Generate a production-ready `render.yaml` (or Render.com config), suitable for Django, including static file serving, environment vars, and Github autodeploy.

---

## 8. Instructions for Using Generated Content
Prompt:  
Show how to map the content (site copy, emails, etc) you generated earlier into Django templates, context, and, optionally, translation/lookups for maintainability.

---

## 9. Deployment Troubleshooting
Common Render.com deployment issues and fixes:

### Required Django Project Structure:
```
decipherworld/
├── manage.py                   # Django management script
├── decipherworld/             # Main project package  
│   ├── __init__.py
│   ├── settings/
│   │   ├── __init__.py
│   │   ├── base.py           # Base settings
│   │   └── production.py     # Production overrides
│   ├── urls.py
│   └── wsgi.py
├── core/                      # Main app
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── forms.py
│   ├── models.py
│   ├── views.py
│   └── urls.py
├── templates/
├── static/
├── requirements.txt
└── render.yaml
```

### Essential Files:
- `manage.py`: Django management commands
- `decipherworld/settings/base.py`: Common settings
- `decipherworld/settings/production.py`: Production overrides
- Proper `INSTALLED_APPS` and middleware configuration
- Environment variables in Render dashboard

### Common Deployment Errors:
1. Missing `manage.py` - prevents Django commands
2. Incorrect `DJANGO_SETTINGS_MODULE` path
3. Missing `BASE_DIR` in settings
4. **Database connection issues** - Most common error
5. Static files configuration errors

### Supabase Database Configuration:

**CRITICAL**: Get the correct connection details from Supabase Dashboard:

**Step 1: Find Connection Details in Supabase**
1. Go to Supabase Dashboard → Settings → Database
2. Look for "Connection parameters" section
3. Copy the exact values shown

**Step 2: Set Environment Variables in Render**

✅ **METHOD 1 - Individual Parameters:**
```
DB_HOST = aws-0-us-east-1.pooler.supabase.com
DB_NAME = postgres
DB_USER = postgres.tpgymvjnrmugrjfjwtbb  
DB_PASSWORD = your_actual_password
DB_PORT = 5432
```

✅ **METHOD 2 - Connection String (Alternative):**
```
DATABASE_URL = postgresql://postgres.tpgymvjnrmugrjfjwtbb:password@aws-0-us-east-1.pooler.supabase.com:5432/postgres?sslmode=require
```

❌ **COMMON MISTAKES:**
- Using `db.xxx.supabase.co` (wrong host format)
- Including `https://` in host
- Wrong user format (missing project ID)

**Your actual values will be different!** The host format is usually:
- `aws-0-[region].pooler.supabase.com` 
- `[region]-[pool].pooler.supabase.com`

decipherworld/
├── templates/
│   ├── base.html
│   ├── home/
│   │   ├── index.html          # Hero section + homepage content
│   │   ├── about.html          # Mission statement
│   │   ├── courses.html        # Course offerings grid
│   │   ├── teachers.html       # For Teachers & Administrators
│   │   ├── contact.html        # Contact & Demo form
│   │   └── coming-soon.html    # Future feature teaser
│   ├── includes/
│   │   ├── header.html
│   │   ├── footer.html
│   │   └── nav.html
│   └── emails/
│       └── onboarding.html     # Welcome email template