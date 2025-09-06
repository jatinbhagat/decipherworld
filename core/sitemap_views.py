from django.http import HttpResponse
from django.urls import reverse
from django.template import Template, Context


def simple_sitemap(request):
    """Simple sitemap that doesn't require sites framework"""
    
    # Get the site domain from the request
    try:
        if request.is_secure():
            scheme = 'https'
        else:
            scheme = 'http'
        
        domain = request.get_host()
        base_url = f"{scheme}://{domain}"
    except:
        # Fallback to hardcoded domain
        base_url = "https://decipherworld.com"
    
    # Define all URLs
    urls = [
        # Core pages
        ('', '2024-12-01', 'weekly', '1.0'),  # home
        ('/about/', '2024-12-01', 'monthly', '0.8'),
        ('/courses/', '2024-12-01', 'weekly', '0.9'),
        ('/teachers/', '2024-12-01', 'weekly', '0.9'),
        ('/schools/', '2024-12-01', 'weekly', '0.9'),
        ('/gallery/', '2024-12-01', 'monthly', '0.7'),
        ('/contact/', '2024-12-01', 'monthly', '0.8'),
        
        # AI Learning Games
        ('/buddy/', '2024-12-01', 'weekly', '0.9'),
        ('/buddy/activities/', '2024-12-01', 'weekly', '0.8'),
        ('/buddy/simple-game/', '2024-12-01', 'weekly', '0.8'),
        ('/buddy/drag-drop-game/', '2024-12-01', 'weekly', '0.8'),
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