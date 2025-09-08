from django.http import HttpResponse


def robots_txt(request):
    """Simple robots.txt"""
    scheme = 'https' if request.is_secure() else 'http'
    domain = request.get_host()
    
    content = f"""User-agent: *
Allow: /

Disallow: /admin/

# Sitemaps
Sitemap: {scheme}://{domain}/sitemap.xml"""
    
    return HttpResponse(content, content_type='text/plain')