"""
Middleware for handling timeouts and performance monitoring
"""
import time
import logging
from django.http import HttpResponse
from django.utils.deprecation import MiddlewareMixin
from django.core.cache import cache

logger = logging.getLogger(__name__)

class TimeoutMiddleware(MiddlewareMixin):
    """Monitor request duration and log slow requests"""
    
    def process_request(self, request):
        request.start_time = time.time()
        return None
    
    def process_response(self, request, response):
        if hasattr(request, 'start_time'):
            duration = time.time() - request.start_time
            
            # Log slow requests
            if duration > 5:  # More than 5 seconds
                logger.warning(f"SLOW REQUEST: {request.path} took {duration:.2f}s - IP: {self.get_client_ip(request)}")
            
            # Add response time header for monitoring
            response['X-Response-Time'] = f"{duration:.3f}"
            
            # Cache frequently accessed pages
            if request.method == 'GET' and duration < 1 and response.status_code == 200:
                if request.path in ['/', '/games/', '/teachers/']:
                    cache_key = f"page_cache_{request.path}"
                    cache.set(cache_key, True, 300)  # 5 minutes
        
        return response
    
    def process_exception(self, request, exception):
        if hasattr(request, 'start_time'):
            duration = time.time() - request.start_time
            logger.error(f"REQUEST EXCEPTION: {request.path} failed after {duration:.2f}s - {str(exception)}")
        return None
    
    def get_client_ip(self, request):
        """Get client IP for logging"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
            if ':' in ip and not ip.startswith('['):
                ip = ip.split(':')[0]
        else:
            ip = request.META.get('REMOTE_ADDR', 'unknown')
        return ip

class HealthCheckMiddleware(MiddlewareMixin):
    """Quick health check responses to avoid timeouts"""
    
    def process_request(self, request):
        # Fast response for health checks
        if request.path in ['/health/', '/api/health/']:
            return None  # Let it proceed normally but prioritize
        
        # Block suspicious requests that might cause timeouts
        user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
        if any(bot in user_agent for bot in ['spider', 'crawler', 'bot']) and len(request.GET) > 10:
            logger.warning(f"Blocked complex bot request: {request.path} - {user_agent}")
            return HttpResponse("Too Many Parameters", status=400)
        
        return None