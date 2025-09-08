from django.http import HttpResponse
from django.urls import reverse
from django.template import Template, Context
from django.utils import timezone
from datetime import datetime


def simple_sitemap(request):
    """Comprehensive sitemap with all site URLs"""
    
    # Get the site domain from the request
    try:
        if request.is_secure():
            scheme = 'https'
        else:
            scheme = 'http'
        
        domain = request.get_host()
        base_url = f"{scheme}://{domain}"
    except:
        # Fallback to production domain
        base_url = "https://decipherworld.com"
    
    # Current date for recently updated pages
    current_date = timezone.now().strftime('%Y-%m-%d')
    recent_date = '2024-12-15'  # When group learning was added
    
    # Define all URLs with proper SEO priorities and update frequencies
    urls = [
        # Core pages - High priority
        ('', current_date, 'daily', '1.0'),  # homepage - highest priority
        ('/about/', recent_date, 'weekly', '0.9'),  # about page
        ('/courses/', current_date, 'daily', '0.95'),  # courses - very high priority
        ('/teachers/', current_date, 'weekly', '0.9'),  # teachers section
        ('/schools/', current_date, 'weekly', '0.85'),  # schools section
        ('/contact/', recent_date, 'monthly', '0.8'),  # contact page
        ('/gallery/', recent_date, 'monthly', '0.7'),  # gallery
        
        # Educational Games Hub - MAJOR NEW SECTION
        ('/games/', current_date, 'daily', '1.0'),  # main games hub - highest priority
        ('/games/ai-learning/', current_date, 'daily', '0.95'),  # AI learning games category
        ('/games/group-learning/', current_date, 'daily', '0.95'),  # group learning games category
        
        # Individual Game Landing Pages - HIGH-VALUE SEO CONTENT
        ('/games/ai-learning/robotic-buddy/', current_date, 'weekly', '0.9'),  # robotic buddy game
        ('/games/ai-learning/simple-game/', current_date, 'weekly', '0.85'),  # simple AI game
        ('/games/ai-learning/drag-drop-game/', current_date, 'weekly', '0.85'),  # drag-drop game
        ('/games/group-learning/monsoon-mayhem/', current_date, 'weekly', '0.9'),  # monsoon mayhem scenario
        
        # Future Game Categories - Coming Soon
        ('/games/stem-challenges/', current_date, 'monthly', '0.7'),  # STEM challenges coming soon
        ('/games/language-adventures/', current_date, 'monthly', '0.7'),  # language games coming soon
        
        # Legacy Game URLs (for backward compatibility)
        ('/buddy/', current_date, 'weekly', '0.8'),  # main buddy page (redirects to games hub)
        ('/buddy/activities/', current_date, 'weekly', '0.75'),  # activities list
        ('/buddy/simple-game/', current_date, 'weekly', '0.7'),  # simple learning game
        ('/buddy/drag-drop-game/', current_date, 'weekly', '0.7'),  # drag-drop game
        ('/buddy/create/', current_date, 'weekly', '0.7'),  # create buddy
        ('/learn/', current_date, 'daily', '0.85'),  # group learning homepage (redirects to games hub)
        ('/learn/game/1/', current_date, 'weekly', '0.8'),  # monsoon mayhem game details
        
        # Educational Content Pages
        ('/courses/climate-education/', current_date, 'weekly', '0.85'),
        ('/courses/collaborative-learning/', current_date, 'weekly', '0.85'),
        ('/courses/ai-education/', current_date, 'weekly', '0.85'),
        ('/courses/stem-games/', current_date, 'weekly', '0.8'),
        
        # Teacher Resources
        ('/teachers/resources/', current_date, 'weekly', '0.8'),
        ('/teachers/training/', current_date, 'weekly', '0.8'),
        ('/teachers/professional-development/', current_date, 'weekly', '0.75'),
        
        # School Solutions
        ('/schools/implementation/', current_date, 'weekly', '0.8'),
        ('/schools/curriculum/', current_date, 'weekly', '0.8'),
        ('/schools/pricing/', current_date, 'weekly', '0.75'),
        
        # Educational Topics - High-value SEO content
        ('/topics/climate-change-education/', current_date, 'weekly', '0.8'),
        ('/topics/collaborative-problem-solving/', current_date, 'weekly', '0.8'),
        ('/topics/role-playing-learning/', current_date, 'weekly', '0.8'),
        ('/topics/ai-in-education/', current_date, 'weekly', '0.8'),
        ('/topics/game-based-learning/', current_date, 'weekly', '0.8'),
        
        # Blog/Articles (potential for content marketing)
        ('/articles/climate-crisis-education/', current_date, 'monthly', '0.7'),
        ('/articles/collaborative-learning-benefits/', current_date, 'monthly', '0.7'),
        ('/articles/ai-tools-for-teachers/', current_date, 'monthly', '0.7'),
        
        # Landing Pages for SEO
        ('/solutions/elementary-schools/', current_date, 'weekly', '0.75'),
        ('/solutions/middle-schools/', current_date, 'weekly', '0.75'),
        ('/solutions/high-schools/', current_date, 'weekly', '0.75'),
        
        # Support and Help
        ('/help/', recent_date, 'monthly', '0.6'),
        ('/help/getting-started/', recent_date, 'monthly', '0.65'),
        ('/help/teacher-guide/', recent_date, 'monthly', '0.7'),
        
        # Legal pages (important for trust)
        ('/privacy/', recent_date, 'yearly', '0.3'),
        ('/terms/', recent_date, 'yearly', '0.3'),
        ('/accessibility/', recent_date, 'yearly', '0.3'),
    ]
    
    # XML template
    xml_template = Template("""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{% for url, lastmod, changefreq, priority in urls %}
    <url>
        <loc>{{ base_url }}{{ url }}</loc>
        <lastmod>{{ lastmod }}</lastmod>
        <changefreq>{{ changefreq }}</changefreq>
        <priority>{{ priority }}</priority>
    </url>
{% endfor %}
</urlset>""")
    
    context = Context({
        'urls': urls,
        'base_url': base_url
    })
    
    xml_content = xml_template.render(context)
    
    response = HttpResponse(xml_content, content_type='application/xml')
    return response