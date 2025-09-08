# DecipherWorld - AI EdTech Platform

**Transform Learning Into Adventure** - A Django-powered educational platform featuring game-based learning, AI tools for teachers, and collaborative group experiences.

🌐 **Live Site**: [decipherworld-app.azurewebsites.net](https://decipherworld-app.azurewebsites.net)

## 🎯 What We Do

DecipherWorld revolutionizes K-12 education through:

- **🎮 Game-Based Learning**: Interactive AI courses and group scenarios
- **👩‍🏫 AI Teacher Training**: 5X productivity boost with 40+ AI tools
- **🤝 Group Collaboration**: Multi-player educational scenarios
- **📚 Core Courses**: AI, Financial Literacy, Climate Change, Entrepreneurship

## 🏗️ Tech Stack

- **Backend**: Django 4.2+ with PostgreSQL
- **Frontend**: Django Templates + Tailwind CSS + DaisyUI
- **Deployment**: Azure App Service + Azure PostgreSQL
- **Static Files**: WhiteNoise

## 🚀 Quick Start

### Local Development

```bash
# Clone and setup
git clone <repo-url>
cd decipherworld
pip install -r requirements.txt

# Environment setup
cp .env.example .env  # Configure your DATABASE_URL

# Database setup
python manage.py migrate
python manage.py createsuperuser

# Run development server
python manage.py runserver
```

### Production Deployment

Uses Azure App Service with PostgreSQL. Environment variables required:
- `SECRET_KEY` - Django secret key
- `DATABASE_URL` - PostgreSQL connection string
- `DJANGO_SETTINGS_MODULE=decipherworld.settings.production`

## 📁 Project Structure

```
decipherworld/
├── decipherworld/          # Django project settings
│   ├── settings/
│   │   ├── base.py        # Base settings
│   │   └── production.py  # Production overrides
│   └── urls.py
├── core/                  # Main app (homepage, courses, contact)
├── games/                 # Games hub and landing pages  
├── robotic_buddy/         # AI learning game for kids
├── group_learning/        # Collaborative scenario platform
├── templates/             # Django templates
├── static/               # Static files (CSS, JS, images)
└── manage.py
```

## 🎮 Platform Features

### AI Learning Games
- **Robotic Buddy**: Create and train AI companions
- **Classification Games**: Interactive ML concept learning
- **Progressive Difficulty**: Age-appropriate challenges

### Group Learning Platform  
- **Role-Based Scenarios**: Climate crisis, problem-solving challenges
- **Multi-Player Sessions**: 3-4 player collaborative experiences
- **Real-Time Decision Making**: Collective outcome generation
- **Learning Analytics**: Post-session reflection and assessment

### Teacher AI Training
- **40+ AI Tools**: MagicSchool.ai, Eduaide.ai, Khanmigo, etc.
- **Hands-On Workshops**: Real classroom scenario training
- **5X Productivity**: Streamlined lesson planning and assessment

## 🔧 Development

### Settings Configuration
- **Local**: Uses `decipherworld.settings.base` (SQLite fallback)
- **Production**: Uses `decipherworld.settings.production` (PostgreSQL)

### Database Management
```bash
python manage.py makemigrations
python manage.py migrate
```

### Static Files
```bash
python manage.py collectstatic
```

## 📊 Monitoring & SEO

- **Sitemap**: Auto-generated at `/sitemap.xml`
- **Robots.txt**: SEO-optimized at `/robots.txt`
- **Performance**: WhiteNoise static file optimization
- **Analytics**: Built-in Django logging

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📝 License

Educational use license - Transforming learning through technology.

---

**Built with ❤️ by the DecipherWorld Team** | Making Education Engaging & Effective ⚡