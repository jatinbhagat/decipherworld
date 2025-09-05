# SEO Configuration for Decipherworld
from django.conf import settings

# Default SEO settings
DEFAULT_SEO = {
    'site_name': 'Decipherworld',
    'default_title': 'Decipherworld - Transform Learning Into Adventure',
    'default_description': 'Transform learning into adventure with Decipherworld\'s game-based education platform. AI-powered tools for teachers, engaging learning for students.',
    'default_keywords': 'education, game-based learning, AI teaching tools, student engagement, EdTech',
    'default_og_image': '/static/images/decipherworld-logo.png',
    'twitter_handle': '@decipherworld',
}

# Page-specific SEO configurations
PAGE_SEO = {
    'home': {
        'title': 'Decipherworld - AI EdTech Platform | Game-Based Learning & Teacher Training',
        'description': 'Transform education with Decipherworld\'s AI-powered platform. 500+ schools trust our game-based courses in AI, Financial Literacy, Entrepreneurship & Climate Change. 5X teacher productivity boost.',
        'keywords': 'AI education platform, game-based learning, teacher training, AI courses, financial literacy, entrepreneurship education, climate change courses, EdTech platform, school AI implementation',
        'og_title': 'Decipherworld - Leading AI EdTech Platform for Schools',
    },
    'teachers': {
        'title': 'AI Training for Teachers - Boost Productivity 5X | Decipherworld',
        'description': 'Professional AI training for teachers and educators. Master 40+ AI tools, boost productivity 5X, and transform your classroom with hands-on workshops designed for real teaching scenarios.',
        'keywords': 'AI training for teachers, teacher professional development, AI tools for education, MagicSchool.ai, Eduaide.ai, Khanmigo, EdTech training, teacher productivity, AI in classroom',
        'og_title': 'AI Training for Teachers - Transform Your Classroom with AI Tools',
    },
    'courses': {
        'title': 'AI, Financial Literacy & Climate Change Courses for Students | Decipherworld',
        'description': 'Signature 21st-century skill courses for students: AI for All, Financial Literacy, Entrepreneurship, and Climate Change. Game-based learning with real-world applications and interactive challenges.',
        'keywords': 'AI courses for students, financial literacy education, entrepreneurship courses, climate change education, 21st century skills, game-based learning, student courses',
        'og_title': 'AI & Life Skills Courses for Students - Game-Based Learning',
    },
    'contact': {
        'title': 'Book Your Free Demo - Get Started with AI EdTech | Decipherworld',
        'description': 'Book a free demo of Decipherworld\'s AI EdTech platform. Get personalized walkthrough of our game-based courses and teacher training programs. Contact our education experts today.',
        'keywords': 'book demo, free demo, contact Decipherworld, AI EdTech demo, education platform demo, teacher training demo, school demo booking',
        'og_title': 'Book Free Demo - Decipherworld AI Education Platform',
    },
}

def get_seo_data(page_key=None):
    """Get SEO data for a specific page or default"""
    if page_key and page_key in PAGE_SEO:
        return {**DEFAULT_SEO, **PAGE_SEO[page_key]}
    return DEFAULT_SEO