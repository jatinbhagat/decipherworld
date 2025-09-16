from django.http import HttpResponse
from django.utils import timezone


def simple_sitemap(request):
    """Enhanced sitemap with SEO-friendly URLs for Indian educational market"""
    
    scheme = 'https' if request.is_secure() else 'http'
    domain = request.get_host()
    base_url = f"{scheme}://{domain}"
    # Use Indian timezone for timestamps
    current_date = timezone.now().strftime('%Y-%m-%d')
    
    # Essential URLs with SEO priorities for Indian education
    urls = [
        # Core pages (highest priority)
        ('', '1.0', 'daily'),
        ('/courses/', '0.9', 'weekly'),
        ('/teachers/', '0.9', 'weekly'),
        ('/schools/', '0.8', 'weekly'),
        ('/contact/', '0.8', 'monthly'),
        ('/gallery/', '0.7', 'monthly'),
        
        # Games Hub (high discoverability for Indian students)
        ('/games/', '0.9', 'weekly'),
        
        # Individual Games (CBSE/ICSE focused)
        ('/games/ai-learning/', '0.8', 'weekly'),
        ('/games/cyber-security/', '0.8', 'weekly'),
        ('/games/financial-literacy/', '0.8', 'weekly'),
        
        # Team Games (Constitutional & Environmental Education)
        ('/games/constitution-basic/', '0.8', 'weekly'),
        ('/games/constitution-advanced/', '0.8', 'weekly'),
        ('/games/entrepreneurship/', '0.8', 'weekly'),
        ('/games/group-learning/', '0.7', 'weekly'),
        ('/games/group-learning/monsoon-mayhem/', '0.7', 'weekly'),
        
        # Future categories
        ('/games/stem-challenges/', '0.6', 'monthly'),
        ('/games/language-adventures/', '0.6', 'monthly'),
        
        # Cyber City Security Games
        ('/cyber-city/', '0.7', 'weekly'),
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