from django.http import HttpResponse
from django.utils import timezone


def simple_sitemap(request):
    """Simple sitemap with essential URLs"""
    
    scheme = 'https' if request.is_secure() else 'http'
    domain = request.get_host()
    base_url = f"{scheme}://{domain}"
    current_date = timezone.now().strftime('%Y-%m-%d')
    
    # Essential URLs only
    urls = [
        # Core pages
        ('', '1.0', 'daily'),
        ('/courses/', '0.9', 'weekly'),
        ('/teachers/', '0.9', 'weekly'),
        ('/schools/', '0.8', 'weekly'),
        ('/contact/', '0.7', 'monthly'),
        
        # Games
        ('/games/', '0.9', 'weekly'),
        ('/games/ai-learning/', '0.8', 'weekly'),
        ('/games/group-learning/', '0.8', 'weekly'),
        ('/games/buddy/', '0.7', 'weekly'),
        ('/learn/', '0.8', 'weekly'),
        
        # Other pages
        ('/gallery/', '0.6', 'monthly'),
    ]
    
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