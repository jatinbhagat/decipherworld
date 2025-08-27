from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from .models import DemoRequest, Course
from .forms import DemoRequestForm

def home(request):
    """Homepage with hero section and product highlights"""
    courses = Course.objects.filter(is_active=True)[:4]
    context = {
        'courses': courses,
        'page_title': 'Transform Learning Into Adventure'
    }
    return render(request, 'home/index.html', context)

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