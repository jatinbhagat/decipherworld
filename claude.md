# CLAUDE.md – Django + Azure Website Development Guide

## 1. Project Setup
Prompt:  
Generate step-by-step commands to initialize a Django project called `decipherworld`, add a `core` app, and set up for deployment on Microsoft Azure App Service with Azure PostgreSQL. Assume a fresh environment.

---

## 2. Django Project Structure
Prompt:  
Generate the recommended Django project folder structure for a site with landing pages, signup/login, course listings, and a contact/demo form, using templates and class-based views. Use mobile-first design conventions.

---

## 3. Models & Django ORM
Prompt:  
Generate Django models for Courses, Schools, Teachers, DemoRequests. Use Django's built-in ORM and authentication system with PostgreSQL database.

---

## 4. URLs, Views & Template Setup
Prompt:  
Generate example Django URLs, views (CBV where possible), and templates for:  
- Homepage displaying product highlights and CTAs  
- Courses page listing all courses dynamically  
- Teacher/Admin signup/login with Django auth  
- Contact/demo request form  
- Success page/messages

---

## 5. HTML & Tailwind CSS
Prompt:  
Generate responsive, minimal HTML + Tailwind CSS templates for each section (hero, mission, courses, product blurbs, signup, contact form, footer), inserting previously generated site copy in the appropriate places.

---

## 6. Demo Request Form Logic
Prompt:  
Generate Django form and view logic for submitting demo/contact requests, saving to PostgreSQL using Django ORM, with error handling and success feedback on UI.

---

## 7. Azure Deployment
Prompt:  
Generate Azure App Service deployment configuration with proper static file serving, environment variables, and GitHub Actions workflow for CI/CD.

---

## 8. Instructions for Using Generated Content
Prompt:  
Show how to map the content (site copy, emails, etc) you generated earlier into Django templates, context, and, optionally, translation/lookups for maintainability.

---

## 9. Azure Deployment Configuration

### Required Django Project Structure:
```
decipherworld/
├── manage.py                   # Django management script
├── decipherworld/             # Main project package  
│   ├── __init__.py
│   ├── settings/
│   │   ├── __init__.py
│   │   ├── base.py           # Base settings
│   │   ├── local.py          # Local development
│   │   ├── production.py     # Production overrides
│   │   └── azure.py          # Azure-specific settings
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
├── startup.sh                 # Azure startup script
└── .github/workflows/
    └── azure-webapps-python.yml
```

### Essential Files:
- `manage.py`: Django management commands
- `decipherworld/settings/base.py`: Common settings
- `decipherworld/settings/production.py`: Production overrides
- `decipherworld/settings/azure.py`: Azure-specific configuration
- `startup.sh`: Azure App Service startup script
- Proper `INSTALLED_APPS` and middleware configuration
- Environment variables in Azure App Service configuration

### Common Deployment Errors:
1. Missing `manage.py` - prevents Django commands
2. Incorrect `DJANGO_SETTINGS_MODULE` path
3. Missing `BASE_DIR` in settings
4. **Database connection issues** - Most common error
5. Static files configuration errors
6. Azure App Service startup configuration

### Azure PostgreSQL Database Configuration:

**CRITICAL**: Get the correct connection details from Azure Portal:

**Step 1: Find Connection Details in Azure Portal**
1. Go to Azure Portal → PostgreSQL flexible servers
2. Select your PostgreSQL server
3. Go to "Settings" → "Connection strings"
4. Copy the connection details

**Step 2: Set Environment Variables in Azure App Service**

✅ **METHOD 1 - CONNECTION STRING (Recommended):**
```
DATABASE_URL = postgresql://decipheradmin:[YOUR-PASSWORD]@decipherworld-db-server-ci01.postgres.database.azure.com:5432/decipherworld?sslmode=require
```

✅ **METHOD 2 - Individual Parameters:**
```
DB_HOST = decipherworld-db-server-ci01.postgres.database.azure.com
DB_NAME = decipherworld
DB_USER = decipheradmin
DB_PASSWORD = your_actual_password
DB_PORT = 5432
```

**IMPORTANT NOTES:**
- **SSL Required**: Azure PostgreSQL requires SSL connections
- **Port 5432**: Standard PostgreSQL port for Azure
- **Firewall Rules**: Ensure Azure App Service has access to PostgreSQL server
- **Connection Pooling**: Configure appropriately for production workloads

**Azure Environment Variables Setup:**
```bash
# Set in Azure App Service Configuration
az webapp config appsettings set --resource-group rg-decipherworld-prod --name decipherworld-app --settings \
    DJANGO_SETTINGS_MODULE=decipherworld.settings.production \
    DATABASE_URL="postgresql://decipheradmin:PASSWORD@HOST:5432/decipherworld?sslmode=require" \
    SECRET_KEY="your-secret-key" \
    DEBUG=False
```

### Azure Resources Required:
1. **Resource Group**: `rg-decipherworld-prod`
2. **App Service Plan**: `decipherworld-app-plan` (Linux)
3. **Web App**: `decipherworld-app`
4. **PostgreSQL Server**: `decipherworld-db-server-ci01`
5. **PostgreSQL Database**: `decipherworld`

### Template Structure:
```
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
```

### Azure-Specific Configuration:
- **Static Files**: Configure Azure Blob Storage or use WhiteNoise
- **Logging**: Use Azure Application Insights
- **SSL/HTTPS**: Enabled by default on Azure App Service
- **Custom Domain**: Configure DNS and SSL certificates
- **Scaling**: Configure auto-scaling rules based on demand

### Development vs Production:
- **Local Development**: Can use Azure PostgreSQL or SQLite
- **Production**: Always use Azure PostgreSQL with SSL
- **Environment Variables**: Use `.env` locally, Azure App Service settings in production
- **Static Files**: WhiteNoise for simplicity, Azure Storage for high-traffic sites

---

## 10. Group Learning Platform Implementation (December 2024)

### Overview
Revolutionary collaborative learning platform added to DecipherWorld, enabling scenario-based, role-driven educational experiences for groups of students.

### Platform Features:
- **Multi-Game Support**: Framework supports multiple educational scenarios
- **Role-Based Learning**: Students take on specific roles with unique perspectives
- **Real-Time Collaboration**: Live multiplayer sessions with session codes
- **Outcome-Driven**: Dynamic results based on collective player decisions
- **Learning Analytics**: Comprehensive reflection and assessment system

### Technical Architecture:

#### Django App Structure:
```
group_learning/
├── models.py              # 10 core models for learning framework
├── views.py               # Session management and gameplay views
├── admin.py               # Rich content management interface
├── urls.py                # RESTful URL patterns
├── templatetags/          # Custom template filters
├── management/commands/   # Data seeding commands
└── templates/group_learning/
    ├── base.html          # Base template with SEO
    ├── game_list.html     # Available games
    ├── game_detail.html   # Game information
    ├── create_session.html # Session setup
    ├── session_detail.html # Player joining
    ├── gameplay.html      # Main game interface
    ├── session_results.html # Outcome display
    └── reflection.html    # Learning assessment
```

#### Core Models (10 Models):
1. **LearningModule** - Curriculum areas (e.g., Climate Science)
2. **LearningObjective** - Specific educational goals
3. **Game** - Complete learning experiences
4. **Role** - Player personas with authority/expertise levels
5. **Scenario** - Specific decision-making situations
6. **Action** - Role-specific choices with costs/effectiveness
7. **Outcome** - Results based on collective actions
8. **GameSession** - Live multiplayer instances
9. **PlayerAction** - Individual decision tracking
10. **ReflectionResponse** - Post-game learning assessment

#### Sample Content - "Climate Crisis India – Monsoon Mayhem":
- **Setting**: Rural West Bengal flood emergency response
- **Roles**: District Collector, Farmer Leader, Civil Engineer, School Principal
- **Learning Focus**: Community resilience, environmental impact, collaborative decision-making
- **Duration**: 45 minutes for 3-4 players
- **Curriculum Alignment**: Climate education, problem-solving, teamwork

### User Experience Flow:
1. **Game Discovery** (`/learn/`) - Browse available scenarios
2. **Session Creation** - Facilitators create sessions with unique codes
3. **Player Joining** - Students join via 6-character session codes
4. **Role Assignment** - Automatic or preferred role selection
5. **Collaborative Gameplay** - Make decisions based on assigned roles
6. **Dynamic Outcomes** - See collective impact of team decisions
7. **Learning Reflection** - Individual assessment and confidence tracking
8. **Results Analysis** - Teachers review learning analytics

### SEO & Content Strategy Enhancements:

#### Comprehensive Sitemap (50+ URLs):
- **Core Educational Content**: High-priority pages with daily updates
- **Learning Platforms**: Individual AI games + group collaboration
- **Educational Topics**: Climate education, STEM, collaborative learning
- **Teacher Resources**: Professional development, implementation guides
- **School Solutions**: Grade-level specific landing pages
- **Support Content**: Help guides, tutorials, accessibility info

#### SEO Optimizations:
- **Enhanced Meta Tags**: Dynamic per-page optimization with Open Graph
- **Structured Data**: Educational organization schema markup
- **Performance**: DNS prefetching, resource optimization
- **Social Media**: Twitter Card optimization for content sharing
- **Robots.txt**: Optimized crawl guidance for search engines

### Management & Analytics:

#### Django Admin Features:
- **Rich Content Management**: Inline editing for complex relationships
- **Visual Role Management**: Color-coded role displays with authority levels
- **Live Session Monitoring**: Real-time gameplay tracking
- **Learning Analytics**: Player decision patterns and reflection quality
- **Content Performance**: Scenario effectiveness and engagement metrics

#### Data Seeding:
```bash
python manage.py seed_monsoon_mayhem  # Populates complete scenario
```

### Production Features:
- **Session Management**: 6-character codes, auto role-assignment
- **Real-Time Updates**: AJAX-powered status and action tracking
- **Responsive Design**: Mobile-first interface with Tailwind CSS
- **Educational Assessment**: Confidence tracking and reflection analysis
- **Content Scalability**: Framework supports unlimited scenarios

### Future Development Pipeline:
- **Additional Scenarios**: Historical events, scientific challenges, social issues
- **Advanced Gameplay**: Multi-scenario games, branching narratives
- **LMS Integration**: Grade reporting and curriculum management
- **Mobile Application**: Native app for improved accessibility
- **Internationalization**: Multi-language and cultural adaptation

This represents a major platform evolution, positioning DecipherWorld as a leader in collaborative educational technology.