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

@csrf_exempt
@require_http_methods(["GET"])
def populate_cyber_challenges(request):
    """Populate Cyber City security challenges"""
    try:
        from cyber_city.models import SecurityChallenge
        
        # Check if challenges already exist
        if SecurityChallenge.objects.exists():
            return JsonResponse({
                'status': 'info',
                'message': 'Challenges already exist',
                'count': SecurityChallenge.objects.count()
            })
        
        # Create the 5 challenges
        challenges = [
            {
                'challenge_number': 1,
                'title': 'The Simple Password Trap',
                'question': 'Alex uses "password123" for everything. What\'s the BIGGEST risk?',
                'option_a': 'Easy to remember',
                'option_b': 'Hackers can guess it easily',
                'option_c': 'It has numbers',
                'option_d': 'It\'s too long',
                'correct_answer': 'B',
                'explanation': 'Simple passwords like "password123" are incredibly easy for hackers to guess or crack using automated tools. They\'re among the first passwords hackers try!',
                'tessa_tip': '💡 Pro tip: Think of passwords like house keys - you wouldn\'t use a toy key for your home! Use unique, complex passwords for each account.'
            },
            {
                'challenge_number': 2,
                'title': 'The Reused Password Problem',
                'question': 'Maya uses "Soccer2023!" for her email, social media, and banking. What should she do?',
                'option_a': 'Keep using it - it\'s strong',
                'option_b': 'Change it to "Soccer2024!"',
                'option_c': 'Use different passwords for each account',
                'option_d': 'Add more numbers',
                'correct_answer': 'C',
                'explanation': 'Using the same password everywhere is like having one key for your house, car, and office. If someone gets it, they access everything! Each account needs its own unique password.',
                'tessa_tip': '🔐 Smart move: Use a password manager to create and store unique passwords for every account. It\'s like having a super-secure keychain!'
            },
            {
                'challenge_number': 3,
                'title': 'The Public Wi-Fi Danger',
                'question': 'Sam wants to check his bank account on café Wi-Fi. What\'s the safest approach?',
                'option_a': 'Go ahead - the café looks trustworthy',
                'option_b': 'Wait until he\'s on a secure, private network',
                'option_c': 'Use the Wi-Fi but log out quickly',
                'option_d': 'Ask the café owner if it\'s safe',
                'correct_answer': 'B',
                'explanation': 'Public Wi-Fi is like shouting your secrets in a crowded room - anyone can listen! Banking and sensitive activities should only happen on secure, private networks.',
                'tessa_tip': '📱 Safety first: Use your phone\'s hotspot or wait for secure Wi-Fi. Your financial safety is worth the wait!'
            },
            {
                'challenge_number': 4,
                'title': 'The Suspicious Email Challenge',
                'question': 'Emma gets an email: "Your account expires in 24 hours! Click here to verify!" What should she do?',
                'option_a': 'Click the link immediately',
                'option_b': 'Forward it to friends as a warning',
                'option_c': 'Go directly to the official website instead',
                'option_d': 'Reply asking for more info',
                'correct_answer': 'C',
                'explanation': 'This is a classic phishing attempt! Urgent emails with suspicious links are red flags. Always visit the official website directly instead of clicking email links.',
                'tessa_tip': '🎣 Phishing alert: When in doubt, don\'t click! Go directly to the official website or call the company to verify any urgent requests.'
            },
            {
                'challenge_number': 5,
                'title': 'The Update Alert',
                'question': 'Jake\'s computer shows: "Critical security update available." What should he do?',
                'option_a': 'Ignore it - updates are annoying',
                'option_b': 'Install it immediately',
                'option_c': 'Wait a few months to see if others have problems',
                'option_d': 'Only update if something breaks',
                'correct_answer': 'B',
                'explanation': 'Security updates are like fixing holes in your armor! They patch vulnerabilities that hackers could exploit. Installing them quickly keeps you protected.',
                'tessa_tip': '🛡️ Update power: Enable automatic updates when possible. Think of them as your digital immune system getting stronger!'
            }
        ]
        
        created_count = 0
        for challenge_data in challenges:
            challenge, created = SecurityChallenge.objects.get_or_create(
                challenge_number=challenge_data['challenge_number'],
                defaults=challenge_data
            )
            if created:
                created_count += 1
        
        return JsonResponse({
            'status': 'success',
            'message': f'Successfully populated {created_count} challenges',
            'total_challenges': SecurityChallenge.objects.count()
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Failed to populate challenges: {str(e)}'
        }, status=500)