# Decipherworld - AI EdTech Platform

**Transform Learning Into Adventure** - An AI-powered educational technology platform that revolutionizes K-12 education through game-based learning, personalized AI guidance, and innovative teaching tools.

🌐 **Live Site**: [decipherworld.com](https://decipherworld.com)  
🚀 **Azure Deployment**: [decipherworld-app.azurewebsites.net](https://decipherworld-app.azurewebsites.net)

## 🎯 About Decipherworld

Decipherworld transforms traditional classrooms into dynamic learning ecosystems where students thrive through:

- **🎮 Game-Based Learning**: Interactive courses that make education engaging and fun
- **🤖 AI-Powered Personalization**: Hyper-personalized learning paths adapted to each student
- **⚡ 5X Teacher Productivity**: AI tools that simplify teaching while amplifying impact
- **🚀 Future-Ready Skills**: Preparing students for tomorrow's challenges

### 🏫 Our Courses
- **Entrepreneurship Course**: Building young business minds
- **AI Course for Students**: Introduction to artificial intelligence
- **Financial Literacy**: Essential money management skills
- **Climate Change**: Understanding our environmental future
- **AI Training for Teachers**: Empowering educators with AI tools

## 🏗️ Architecture & Tech Stack

### **Frontend**
- **Framework**: Django Templates with Server-Side Rendering
- **Styling**: Tailwind CSS + DaisyUI components
- **JavaScript**: Vanilla JS for interactive features
- **Design**: Mobile-first responsive design

### **Backend**
- **Framework**: Django 4.2+ (Python)
- **Architecture**: Class-based views (CBV) with clean separation
- **Authentication**: Django's built-in auth system
- **API**: Django ORM for all database operations

### **Database**
- **Production**: Azure Database for PostgreSQL (Flexible Server)
- **Local Development**: PostgreSQL or SQLite fallback
- **ORM**: Django ORM with optimized queries

### **Infrastructure (Microsoft Azure)**
- **Hosting**: Azure App Service (Linux, Python 3.11)
- **Database**: Azure PostgreSQL Flexible Server
- **SSL/Domain**: Custom domain with SSL certificates
- **Static Files**: WhiteNoise for static file serving
- **Monitoring**: Azure Application Insights

## 🚀 Deployment Status

### **Production Environment**
- ✅ **Azure App Service**: `decipherworld-app` (Running)
- ✅ **PostgreSQL Server**: `decipherworld-db-server-ci01` (Ready)
- ✅ **Custom Domain**: `decipherworld.com` (SSL Enabled)
- ✅ **Database**: 4+ School Demo Requests, Active Users
- ✅ **Admin Panel**: Django Admin with custom interfaces

### **Key Features Live**
- ✅ **Homepage**: Hero section with product highlights
- ✅ **School Presentation**: Interactive Gamma presentation (fullscreen)
- ✅ **Demo Booking**: School demo request system
- ✅ **Contact Forms**: Lead generation and inquiry handling
- ✅ **Admin Dashboard**: Complete admin interface for managing requests
- ✅ **Mobile Responsive**: Optimized for all devices

## 🛠️ Local Development Setup

### **Prerequisites**
- Python 3.11+
- PostgreSQL (optional - can use SQLite)
- Git

### **Quick Start**

1. **Clone and install**:
   ```bash
   git clone <repository-url>
   cd decipherworld
   pip install -r requirements.txt
   ```

2. **Database setup**:
   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   ```

3. **Run development server**:
   ```bash
   python manage.py runserver
   ```

4. **Access application**:
   - Main site: http://127.0.0.1:8000/
   - Admin: http://127.0.0.1:8000/admin/

### **Environment Configuration**

Create `.env` file for local development:
```bash
# Optional: Use production Azure PostgreSQL locally
DATABASE_URL=postgresql://decipheradmin:PASSWORD@decipherworld-db-server-ci01.postgres.database.azure.com:5432/decipherworld?sslmode=require

# Development settings
DEBUG=True
SECRET_KEY=your-dev-secret-key
```

## 📊 Project Structure

```
decipherworld/
├── 📄 manage.py                    # Django management
├── 📁 decipherworld/               # Main project
│   ├── 📁 settings/
│   │   ├── 📄 base.py             # Common settings
│   │   ├── 📄 local.py            # Development
│   │   ├── 📄 production.py       # Production
│   │   └── 📄 azure.py            # Azure-specific
│   ├── 📄 urls.py                 # URL routing
│   └── 📄 wsgi.py                 # WSGI config
├── 📁 core/                       # Main application
│   ├── 📄 models.py               # Data models
│   ├── 📄 views.py                # Business logic
│   ├── 📄 forms.py                # Form handling
│   ├── 📄 admin.py                # Admin interface
│   └── 📄 urls.py                 # App URLs
├── 📁 templates/                  # HTML templates
│   ├── 📄 base.html
│   └── 📁 home/                   # Page templates
├── 📁 static/                     # CSS, JS, images
├── 📁 staticfiles/                # Collected static files
├── 📄 requirements.txt            # Dependencies
├── 📄 CLAUDE.md                   # Development guide
└── 📄 verify_azure.sh             # Infrastructure check
```

## 🎯 Key Pages & Features

### **Public Pages**
- **Homepage** (`/`) - Hero section, product highlights, CTAs
- **School Presentation** (`/schools/presentation/`) - Interactive presentation with fullscreen
- **School Demo** (`/schools/`) - Demo booking for educational institutions  
- **Teachers** (`/teachers/`) - AI training for educators
- **Contact** (`/contact/`) - General inquiries and demo requests

### **Admin Features**
- **School Demo Management** - View, filter, search school requests
- **Lead Tracking** - Mark schools as contacted, view inquiry details
- **Product Interest Analysis** - See which courses are most popular
- **User Management** - Django's built-in user system

## 📈 Business Metrics

### **Current Data** (as of deployment)
- **School Demo Requests**: 4 active inquiries
- **Demo Requests**: 1 general inquiry  
- **Courses Available**: 5 comprehensive programs
- **Target Audience**: K-12 schools, teachers, administrators

### **Popular Features**
1. School presentation with interactive slides
2. Multi-product demo booking system
3. Teacher productivity tools showcase
4. Mobile-responsive design for all stakeholders

## 🔧 Management Commands

```bash
# Database operations
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser

# Data management
python manage.py shell
python manage.py dbshell

# Static files
python manage.py collectstatic

# Health checks
python manage.py check
python manage.py check --deploy
```

## 🌐 Production URLs

- **Main Site**: https://decipherworld.com
- **Azure App**: https://decipherworld-app.azurewebsites.net
- **Admin Panel**: https://decipherworld.com/admin/

## 🚀 Future Enhancements

- [ ] Course catalog with detailed curriculum
- [ ] Student dashboard and progress tracking
- [ ] Teacher portal with AI tools
- [ ] Payment integration for course subscriptions
- [ ] Advanced analytics and reporting
- [ ] Mobile app development
- [ ] AI chatbot for instant support

## 📞 Support & Contact

- **Business Inquiries**: hello@decipherworld.com  
- **Technical Support**: Available through admin panel
- **Demo Requests**: Use the school demo booking system

## 📝 License & Contributing

This is a proprietary educational technology platform. For partnership or collaboration inquiries, please contact us through the official channels.

---

**Empowering Education: AI & Future-Ready Skills for K-12** 🎓✨