from django.http import HttpResponse
from django.views.decorators.http import require_GET

@require_GET
def robots_txt(request):
    lines = [
        "User-agent: *",
        "Allow: /",
        "",
        "# Important pages for crawling",
        "Allow: /courses/",
        "Allow: /teachers/",
        "Allow: /schools/",
        "Allow: /gallery/",
        "Allow: /contact/",
        "",
        "# Static files and admin", 
        "Disallow: /admin/",
        "Disallow: /static/admin/",
        "Allow: /static/",
        "",
        "# Sitemap location",
        f"Sitemap: {request.build_absolute_uri('/sitemap.xml')}",
        "",
        "# Crawl-delay for respectful crawling",
        "Crawl-delay: 1"
    ]
    return HttpResponse('\n'.join(lines), content_type='text/plain')