from django.http import HttpResponse
from django.utils import timezone


def simple_sitemap(request):
    """Enhanced sitemap with SEO best practices for DecipherWorld educational platform"""
    
    scheme = 'https' if request.is_secure() else 'http'
    domain = request.get_host()
    base_url = f"{scheme}://{domain}"
    # Use timezone-aware timestamp
    current_date = timezone.now().strftime('%Y-%m-%d')
    
    # CORE EDUCATIONAL PAGES (Highest Priority - 0.9-1.0)
    urls = [
        ('', '1.0', 'weekly'),  # Homepage - realistic update frequency
        ('/courses/', '0.9', 'weekly'),  # Primary educational content
        ('/teachers/', '0.9', 'weekly'),  # AI teacher training - high value
        ('/about/', '0.8', 'monthly'),
        ('/schools/', '0.8', 'monthly'),
        ('/contact/', '0.8', 'monthly'),
        ('/school-presentation/', '0.7', 'monthly'),
        ('/gallery/', '0.7', 'monthly'),
        
        # GAMES HUB & MAIN CATEGORIES (High Priority - 0.8-0.9)
        ('/games/', '0.9', 'weekly'),  # Main games portal
        
        # INDIVIDUAL GAME CATEGORIES (High-Medium Priority - 0.8)
        ('/games/ai-learning/', '0.8', 'monthly'),  # CBSE/ICSE AI curriculum
        ('/games/cyber-security/', '0.8', 'monthly'),  # Digital literacy
        ('/games/financial-literacy/', '0.8', 'monthly'),  # Life skills
        ('/games/constitution-basic/', '0.8', 'monthly'),  # Civics education
        ('/games/constitution-advanced/', '0.8', 'monthly'),
        ('/games/entrepreneurship/', '0.8', 'monthly'),
        ('/games/group-learning/', '0.8', 'monthly'),  # Collaborative learning
        
        # SPECIFIC GAME EXPERIENCES (Medium Priority - 0.7)
        ('/games/ai-learning/robotic-buddy/', '0.7', 'monthly'),
        ('/games/ai-learning/simple-game/', '0.7', 'monthly'),
        ('/games/ai-learning/drag-drop-game/', '0.7', 'monthly'),
        ('/games/group-learning/monsoon-mayhem/', '0.7', 'monthly'),
        
        # FUTURE CATEGORIES (Lower Priority - 0.6)
        ('/games/stem-challenges/', '0.6', 'monthly'),
        ('/games/language-adventures/', '0.6', 'monthly'),
        
        # CYBER CITY SECURITY GAMES (Medium Priority - 0.7-0.8)
        ('/cyber-city/', '0.8', 'monthly'),
        
        # AI LEARNING GAME PAGES - Robotic Buddy (Medium Priority - 0.6-0.7)
        ('/buddy/', '0.7', 'monthly'),
        ('/buddy/activities/', '0.6', 'monthly'),
        ('/buddy/create-buddy/', '0.6', 'monthly'),
        ('/buddy/my-buddy/', '0.5', 'monthly'),
        ('/buddy/classification-game/', '0.6', 'monthly'),
        ('/buddy/simple-game/', '0.6', 'monthly'),
        ('/buddy/drag-drop-game/', '0.6', 'monthly'),
        ('/buddy/emotion-game/', '0.6', 'monthly'),
        ('/buddy/testing-phase/', '0.5', 'monthly'),
        ('/buddy/learning-explanation/', '0.5', 'monthly'),
        ('/buddy/buddy-stats/', '0.4', 'yearly'),
        ('/buddy/achievements/', '0.4', 'yearly'),
        
        # GROUP LEARNING PLATFORM (Medium Priority - 0.7-0.8)
        ('/learn/', '0.8', 'monthly'),  # Main group learning hub
        ('/learn/constitution/start/', '0.7', 'monthly'),
        
        # CLIMATE CRISIS INDIA GAME (Medium-High Priority - 0.7-0.8)
        # Recently fixed and deployed - important for environmental education
        ('/learn/climate/', '0.8', 'monthly'),  # Climate game homepage
        ('/learn/climate/create/', '0.7', 'monthly'),  # Session creation
    ]
    
    # DYNAMIC GROUP LEARNING GAMES (Medium Priority - 0.6-0.7)
    # Include all active games including Climate Crisis games
    try:
        from group_learning.models import Game
        games = Game.objects.filter(is_active=True)
        for game in games:
            game_url = f'/learn/game/{game.id}/'
            # Use actual update time if available for better SEO
            game_date = game.updated_at.strftime('%Y-%m-%d') if hasattr(game, 'updated_at') else current_date
            
            # Higher priority for climate/environmental education games
            if any(keyword in game.name.lower() for keyword in ['climate', 'environment', 'crisis', 'monsoon']):
                priority = '0.7'  # Environmental education is important
            else:
                priority = '0.6'  # Other educational games
                
            urls.append((game_url, priority, 'monthly'))
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