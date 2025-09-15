from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.generic import TemplateView, ListView, FormView
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.management import execute_from_command_line
import sys
import io
from .models import DemoRequest, Course, SchoolDemoRequest
from .forms import DemoRequestForm, SchoolDemoRequestForm

class HomeView(TemplateView):
    """Homepage with hero section and product highlights"""
    template_name = 'home/index.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['courses'] = Course.objects.all()[:4]
        return context

class CoursesView(ListView):
    """Course offerings with detailed descriptions"""
    model = Course
    template_name = 'home/courses.html'
    context_object_name = 'courses'

class TeachersView(TemplateView):
    """AI Training for Teachers & Administrators"""
    template_name = 'home/teachers.html'

class SchoolsView(FormView):
    """Schools demo request page with product selection"""
    template_name = 'home/schools.html'
    form_class = SchoolDemoRequestForm
    success_url = reverse_lazy('core:schools')
    
    def form_valid(self, form):
        try:
            school_demo = form.save()
            products_display = ', '.join(school_demo.get_products_display())
            messages.success(self.request, 
                f'🏫 School Demo Scheduled! Thank you {school_demo.contact_person}! '
                f'We\'ve received your request for {school_demo.school_name} regarding: {products_display}. '
                'Our team will contact you within 24 hours to schedule your personalized school demo.'
            )
            return super().form_valid(form)
        except Exception as e:
            messages.error(self.request, f'Error saving your school demo request: {str(e)}')
            return self.form_invalid(form)
    
    def form_invalid(self, form):
        messages.error(self.request, 'Please check the form for errors and try again.')
        return super().form_invalid(form)


class SchoolPresentationView(TemplateView):
    """School presentation page showcasing AI EdTech solution"""
    template_name = 'home/school-presentation.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'School Presentation - AI EdTech Solution'
        return context


class GalleryView(TemplateView):
    """Gallery showcasing AI-based student courses and teacher training"""
    template_name = 'home/gallery.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Success Stories & Gallery'
        return context


class ContactView(FormView):
    """Contact & Demo form"""
    template_name = 'home/contact.html'
    form_class = DemoRequestForm
    success_url = reverse_lazy('core:contact')
    
    def form_valid(self, form):
        try:
            demo_request = form.save()
            messages.success(self.request, 
                '🎉 Demo Scheduled Successfully! Thank you for choosing Decipherworld! '
                'We\'ve received your request and will contact you within 24 hours to '
                'confirm your personalized demo. Check your email for next steps.'
            )
            return super().form_valid(form)
        except Exception as e:
            messages.error(self.request, f'Error saving your request: {str(e)}')
            return self.form_invalid(form)
    
    def form_invalid(self, form):
        messages.error(self.request, 'Please check your form for errors.')
        return super().form_invalid(form)

def about(request):
    """Mission statement and company info"""
    context = {
        'mission_statement': '''
        At Decipherworld, we transform classrooms into dynamic learning ecosystems 
        where students thrive through game-based collaboration and hyper-personalized 
        AI guidance. We empower educators with intelligent tools that simplify teaching 
        while amplifying impact, creating future-ready learning communities where 
        creativity, critical thinking, and collaboration flourish naturally.
        '''
    }
    return render(request, 'home/about.html', context)

def courses(request):
    """Course offerings with detailed descriptions"""
    courses = Course.objects.filter(is_active=True)
    return render(request, 'home/courses.html', {'courses': courses})

def teachers(request):
    """For Teachers & Administrators section"""
    return render(request, 'home/teachers.html')

def contact(request):
    """Contact & Demo form"""
    if request.method == 'POST':
        form = DemoRequestForm(request.POST)
        if form.is_valid():
            demo_request = form.save()
            
            # Send welcome email
            send_onboarding_email(demo_request)
            
            messages.success(request, '''
                🎉 Demo Scheduled Successfully! Thank you for choosing Decipherworld! 
                We've received your request and will contact you within 24 hours to 
                confirm your personalized demo. Check your email for next steps.
            ''')
            return redirect('contact')
    else:
        form = DemoRequestForm()
    
    return render(request, 'home/contact.html', {'form': form})

def coming_soon(request):
    """Future features teaser"""
    return render(request, 'home/coming-soon.html')

def send_onboarding_email(demo_request):
    """Send welcome email after demo request"""
    subject = 'Welcome to Decipherworld! Your EdTech Journey Starts Now 🚀'
    
    # Use the onboarding email template content
    message = f'''
    Hi {demo_request.full_name},

    Welcome to the Decipherworld family! We're thrilled that {demo_request.school_name} 
    has joined thousands of forward-thinking institutions transforming education through 
    AI and game-based learning.

    What Happens Next:
    ✅ Demo Preparation - We'll send you a prep guide within 2 hours
    📅 Scheduled Demo - Your personalized walkthrough will be confirmed soon
    🎯 Custom Setup - We'll configure the platform specifically for your school's needs

    Ready to see your students' eyes light up with learning excitement? 
    We can't wait to show you what's possible.

    Cheers,
    The Decipherworld Team
    customerservice@decipherworld.com
    '''
    
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [demo_request.email],
        fail_silently=False,
    )

@csrf_exempt
@require_http_methods(["GET"])
def run_migrations(request):
    """Run database migrations via HTTP request"""
    try:
        # Capture stdout and stderr
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()
        
        sys.stdout = stdout_capture
        sys.stderr = stderr_capture
        
        try:
            # Run migrations
            execute_from_command_line(['manage.py', 'migrate', '--verbosity=2'])
            
            stdout_output = stdout_capture.getvalue()
            stderr_output = stderr_capture.getvalue()
            
            return JsonResponse({
                'status': 'success',
                'message': 'Migrations completed successfully',
                'stdout': stdout_output,
                'stderr': stderr_output
            })
            
        except Exception as e:
            stdout_output = stdout_capture.getvalue()
            stderr_output = stderr_capture.getvalue()
            
            return JsonResponse({
                'status': 'error',
                'message': f'Migration failed: {str(e)}',
                'stdout': stdout_output,
                'stderr': stderr_output
            }, status=500)
            
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Failed to run migrations: {str(e)}'
        }, status=500)