from django.http import HttpResponse
from django.utils import timezone


def simple_sitemap(request):
    """Enhanced sitemap with SEO-friendly URLs and dynamic content"""
    
    scheme = 'https' if request.is_secure() else 'http'
    domain = request.get_host()
    base_url = f"{scheme}://{domain}"
    current_date = timezone.now().strftime('%Y-%m-%d')
    
    # Essential URLs with SEO priorities
    urls = [
        # Core pages (highest priority)
        ('', '1.0', 'daily'),
        ('/courses/', '0.9', 'weekly'),
        ('/teachers/', '0.9', 'weekly'),
        ('/schools/', '0.8', 'weekly'),
        ('/contact/', '0.8', 'monthly'),
        ('/gallery/', '0.7', 'monthly'),
        
        # Games (high discoverability)
        ('/games/', '0.9', 'weekly'),
        ('/games/ai-learning/', '0.8', 'weekly'),  
        ('/games/group-learning/', '0.8', 'weekly'),
        ('/games/stem-challenges/', '0.7', 'weekly'),
        ('/games/language-adventures/', '0.7', 'weekly'),
        
        # Robotic Buddy pages
        ('/buddy/', '0.8', 'weekly'),
        ('/buddy/create/', '0.7', 'weekly'),
        ('/buddy/activities/', '0.7', 'weekly'),
        ('/buddy/simple-game/', '0.6', 'monthly'),
        ('/buddy/classification-game/', '0.6', 'monthly'),
        ('/buddy/drag-drop-game/', '0.6', 'monthly'),
        ('/buddy/emotion-game/', '0.6', 'monthly'),
        
        # Group Learning
        ('/learn/', '0.8', 'weekly'),
    ]
    
    # Add dynamic Group Learning game pages
    try:
        from group_learning.models import Game
        games = Game.objects.filter(is_active=True)
        for game in games:
            game_url = f'/learn/game/{game.id}/'
            game_date = game.updated_at.strftime('%Y-%m-%d') if hasattr(game, 'updated_at') else current_date
            urls.append((game_url, '0.7', 'weekly'))
    except Exception:
        # Continue without dynamic URLs if there's an error (e.g., in testing)
        pass
    
    # Generate XML
    xml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'''
    
    for url, priority, changefreq in urls:
        xml_content += f'''
    <url>
        <loc>{base_url}{url}</loc>
        <lastmod>{current_date}</lastmod>
        <changefreq>{changefreq}</changefreq>
        <priority>{priority}</priority>
    </url>'''
    
    xml_content += '\n</urlset>'
    
    return HttpResponse(xml_content, content_type='application/xml')