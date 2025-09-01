from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.generic import TemplateView, ListView, FormView
from django.urls import reverse_lazy
from .models import DemoRequest, Course, SchoolDemoRequest
from .forms import DemoRequestForm, SchoolDemoRequestForm

class HomeView(TemplateView):
    """Homepage with hero section and product highlights"""
    template_name = 'home/index.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['courses'] = Course.objects.all()[:4]
        context['page_title'] = 'Transform Learning Into Adventure'
        return context

class CoursesView(ListView):
    """Course offerings with detailed descriptions"""
    model = Course
    template_name = 'home/courses.html'
    context_object_name = 'courses'

class TeachersView(TemplateView):
    """AI Training for Teachers & Administrators"""
    template_name = 'home/teachers.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'AI Training for Teachers - Boost Productivity 5X'
        return context

class SchoolsView(FormView):
    """Schools demo request page with product selection"""
    template_name = 'home/schools.html'
    form_class = SchoolDemoRequestForm
    success_url = reverse_lazy('core:schools')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'School Implementation - Book Demo'
        return context
    
    def form_valid(self, form):
        try:
            # Debug: Check database connection before saving
            from django.db import connection
            db_settings = connection.settings_dict
            
            # Log connection details for debugging
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"Database connection - HOST: {db_settings.get('HOST')}, PORT: {db_settings.get('PORT')}")
            
            # Verify connection works
            try:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    cursor.fetchone()
            except Exception as conn_error:
                logger.error(f"Database connection test failed: {conn_error}")
                logger.error(f"Connection settings: HOST={db_settings.get('HOST')}, PORT={db_settings.get('PORT')}")
                raise conn_error
            
            # Save the form (this is where the original error occurred)
            school_demo = form.save()
            
            products_display = ', '.join(school_demo.get_products_display())
            messages.success(self.request, 
                f'🏫 School Demo Scheduled! Thank you {school_demo.contact_person}! '
                f'We\'ve received your request for {school_demo.school_name} regarding: {products_display}. '
                'Our team will contact you within 24 hours to schedule your personalized school demo.'
            )
            return super().form_valid(form)
        except Exception as e:
            # Enhanced error reporting
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Form save error: {str(e)}")
            logger.error(f"Error type: {type(e).__name__}")
            
            # Check what database settings are being used during the error
            try:
                from django.db import connection
                db_settings = connection.settings_dict
                logger.error(f"Database settings during error: HOST={db_settings.get('HOST')}, PORT={db_settings.get('PORT')}")
            except Exception as conn_check_error:
                logger.error(f"Could not check connection during error: {conn_check_error}")
            
            messages.error(self.request, f'Error saving your school demo request: {str(e)}')
            return self.form_invalid(form)
    
    def form_invalid(self, form):
        messages.error(self.request, 'Please check the form for errors and try again.')
        return super().form_invalid(form)


class GalleryView(TemplateView):
    """Gallery showcasing AI-based student courses and teacher training"""
    template_name = 'home/gallery.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Success Stories & Gallery'
        return context


class SchoolPresentationView(TemplateView):
    """School presentation page with embedded Gamma presentation"""
    template_name = 'home/school-presentation.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'School Presentation - AI EdTech Solution'
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
    hello@decipherworld.com
    '''
    
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [demo_request.email],
        fail_silently=False,
    )