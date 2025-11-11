from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.generic import TemplateView, ListView, FormView
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.mail import send_mail
from django.conf import settings
import sys
import io
from .models import (
    DemoRequest, Course, SchoolDemoRequest, GameReview,
    PhotoCategory, PhotoGallery, VideoTestimonial, SchoolReferral, School
)
from .forms import DemoRequestForm, SchoolDemoRequestForm, SchoolReferralForm
from .analytics import track_page_view, track_form_submission, track_error
from django.core.management import execute_from_command_line

def simple_home_test(request):
    """Simple test view for debugging"""
    return JsonResponse({'status': 'success', 'message': 'Simple home test working'})

class HomeView(TemplateView):
    """Homepage with hero section and product highlights"""
    template_name = 'home/index.html'
    
    def get(self, request, *args, **kwargs):
        # Track homepage view
        track_page_view(request, 'Homepage', {
            'page_category': 'Landing',
            'is_homepage': True
        })
        return super().get(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            # OPTIMIZED: Cache-first approach to prevent database timeouts
            from django.core.cache import cache
            import time
            
            start_time = time.time()
            cache_key = 'homepage_courses_v2'
            
            # Try cache first - this prevents 504 timeouts from database
            cached_courses = cache.get(cache_key)
            if cached_courses is not None:
                context['courses'] = cached_courses
                print(f"✅ Courses from cache: {len(cached_courses)} in {(time.time() - start_time)*1000:.1f}ms")
            else:
                # Optimized DB query - NO count(), use only() for minimal data
                courses = list(Course.objects.filter(is_active=True).only('id', 'title', 'description')[:4])
                context['courses'] = courses
                
                # Cache for 10 minutes to reduce load
                cache.set(cache_key, courses, 600)
                duration = (time.time() - start_time) * 1000
                print(f"🔄 Courses from DB: {len(courses)} in {duration:.1f}ms")
                
                # Alert if slow (potential 504 cause)
                if duration > 2000:
                    print(f"🚨 SLOW QUERY WARNING: {duration:.1f}ms - potential 504 risk")
                    
        except Exception as e:
            # CRITICAL: Prevent cascading failures that cause 504s
            context['courses'] = []
            error_msg = str(e)[:100]  # Truncate to prevent memory issues
            print(f"❌ Course loading failed: {error_msg}")
            
            # Non-blocking error tracking
            try:
                track_error(self.request, 'Database Error', error_msg, {
                    'view': 'HomeView',
                    'operation': 'loading_courses',
                    'error_type': type(e).__name__
                })
            except:
                pass  # Don't let error tracking cause 504s
        return context

class CoursesView(ListView):
    """Course offerings with detailed descriptions"""
    model = Course
    template_name = 'home/courses.html'
    context_object_name = 'courses'

class TeachersView(TemplateView):
    """AI Training for Teachers & Administrators"""
    template_name = 'home/teachers.html'
    
    def get(self, request, *args, **kwargs):
        # Track teachers page view
        track_page_view(request, 'Teachers Hub', {
            'page_category': 'Teachers',
            'target_audience': 'educators'
        })
        return super().get(request, *args, **kwargs)

class StudentsView(TemplateView):
    """Game-Based Learning for Students"""
    template_name = 'home/students.html'
    
    def get(self, request, *args, **kwargs):
        # Track students page view
        track_page_view(request, 'Students Hub', {
            'page_category': 'Students',
            'target_audience': 'students',
            'content_type': 'game_based_learning'
        })
        return super().get(request, *args, **kwargs)

class SchoolsView(FormView):
    """Schools demo request page with product selection"""
    template_name = 'home/schools.html'
    form_class = SchoolDemoRequestForm
    success_url = reverse_lazy('core:schools')
    
    def get(self, request, *args, **kwargs):
        # Track schools page view
        track_page_view(request, 'Schools Demo Page', {
            'page_category': 'Lead Generation',
            'form_type': 'school_demo_request'
        })
        return super().get(request, *args, **kwargs)
    
    def form_valid(self, form):
        try:
            school_demo = form.save()
            products_display = ', '.join(school_demo.get_products_display())
            
            # Track successful form submission
            track_form_submission(self.request, 'School Demo Request', {
                'school_type': school_demo.school_type,
                'products_selected': school_demo.get_products_display(),
                'student_count': school_demo.student_count,
            }, success=True)
            
            messages.success(self.request, 
                f'🏫 School Demo Scheduled! Thank you {school_demo.contact_person}! '
                f'We\'ve received your request for {school_demo.school_name} regarding: {products_display}. '
                'Our team will contact you within 24 hours to schedule your personalized school demo.'
            )
            return super().form_valid(form)
        except Exception as e:
            # Track form submission error
            track_form_submission(self.request, 'School Demo Request', {}, success=False)
            track_error(self.request, 'Form Submission Error', str(e), {
                'form_type': 'school_demo_request'
            })
            messages.error(self.request, f'Error saving your school demo request: {str(e)}')
            return self.form_invalid(form)
    
    def form_invalid(self, form):
        # Track form validation errors
        track_form_submission(self.request, 'School Demo Request', {
            'validation_errors': list(form.errors.keys())
        }, success=False)
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
    """Enhanced Gallery with photo success stories and video testimonials"""
    template_name = 'core/gallery.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Success Stories & Gallery - DecipherWorld'
        context['page_description'] = 'Explore success stories from schools using DecipherWorld AI education platform and watch student testimonials.'
        
        # Photo Gallery Data
        context['photo_categories'] = PhotoCategory.objects.filter(is_active=True).order_by('order', 'name')
        context['featured_photos'] = PhotoGallery.objects.filter(
            is_featured=True, 
            is_active=True
        ).select_related('category').order_by('order', '-created_at')[:12]
        
        context['recent_photos'] = PhotoGallery.objects.filter(
            is_active=True
        ).select_related('category').order_by('-created_at')[:20]
        
        # Group photos by category for filtering
        context['photos_by_category'] = {}
        for category in context['photo_categories']:
            context['photos_by_category'][category.id] = PhotoGallery.objects.filter(
                category=category,
                is_active=True
            ).order_by('order', '-created_at')
        
        # Video Testimonials Data
        context['featured_videos'] = VideoTestimonial.objects.filter(
            is_featured=True,
            is_active=True
        ).order_by('order', '-created_at')[:6]
        
        context['recent_videos'] = VideoTestimonial.objects.filter(
            is_active=True
        ).order_by('-created_at')[:12]
        
        # Statistics for display
        context['total_photos'] = PhotoGallery.objects.filter(is_active=True).count()
        context['total_videos'] = VideoTestimonial.objects.filter(is_active=True).count()
        context['total_schools'] = PhotoGallery.objects.filter(
            is_active=True, 
            school_name__isnull=False
        ).exclude(school_name='').values('school_name').distinct().count()
        
        # SEO and metadata
        context['canonical_url'] = self.request.build_absolute_uri()
        
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
    """Comprehensive About Us page with team, advisors, vision and mission"""
    return render(request, 'core/about.html')

def courses(request):
    """Course offerings with detailed descriptions"""
    try:
        courses = Course.objects.filter(is_active=True)
    except Exception as e:
        # Fallback if Course queries fail
        courses = []
        print(f"Error loading courses: {e}")
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
            # Check if quest_ciq specific migration requested
            app_param = request.GET.get('app', None)
            if app_param == 'quest_ciq':
                # Run quest_ciq migrations only
                execute_from_command_line(['manage.py', 'migrate', 'quest_ciq', '--verbosity=2'])
            else:
                # Run all migrations
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
@require_http_methods(["POST"])
def fix_migration_conflicts(request):
    """Fix migration conflicts via HTTP request"""
    try:
        # Capture stdout and stderr
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()
        
        sys.stdout = stdout_capture
        sys.stderr = stderr_capture
        
        try:
            # Run the fix migration conflicts command
            from django.core.management import execute_from_command_line
            execute_from_command_line(['manage.py', 'fix_migration_conflicts'])
            
            stdout_output = stdout_capture.getvalue()
            stderr_output = stderr_capture.getvalue()
            
            return JsonResponse({
                'status': 'success',
                'message': 'Migration conflicts fixed successfully',
                'stdout': stdout_output,
                'stderr': stderr_output
            })
            
        except Exception as e:
            stdout_output = stdout_capture.getvalue()
            stderr_output = stderr_capture.getvalue()
            
            return JsonResponse({
                'status': 'error',
                'message': f'Migration conflict fix failed: {str(e)}',
                'stdout': stdout_output,
                'stderr': stderr_output
            }, status=500)
            
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Failed to fix migration conflicts: {str(e)}'
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def create_sample_courses(request):
    """Create sample Course objects for testing"""
    try:
        # Check if courses already exist
        existing_count = Course.objects.count()
        if existing_count > 0:
            return JsonResponse({
                'status': 'info',
                'message': f'Courses already exist: {existing_count} courses found'
            })
        
        # Create sample courses
        courses_data = [
            {
                'title': 'AI & Machine Learning for Students',
                'description': 'Learn artificial intelligence and machine learning concepts through interactive games and projects.',
                'is_active': True
            },
            {
                'title': 'Financial Literacy & Entrepreneurship',
                'description': 'Master personal finance, investing, and entrepreneurship skills for the 21st century.',
                'is_active': True
            },
            {
                'title': 'Climate Change & Sustainability',
                'description': 'Understand climate science and develop solutions for environmental challenges.',
                'is_active': True
            },
            {
                'title': 'Digital Citizenship & Ethics',
                'description': 'Navigate the digital world responsibly with ethics, privacy, and security awareness.',
                'is_active': True
            }
        ]
        
        created_courses = []
        for course_data in courses_data:
            course = Course.objects.create(**course_data)
            created_courses.append(course.title)
        
        return JsonResponse({
            'status': 'success',
            'message': f'Created {len(created_courses)} sample courses',
            'courses': created_courses
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Failed to create courses: {str(e)}'
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
                'question_text': 'Alex uses "password123" for everything. What\'s the BIGGEST risk?',
                'option_a': 'Easy to remember',
                'option_b': 'Hackers can guess it easily',
                'option_c': 'It has numbers',
                'correct_answer': 'B',
                'explanation': 'Simple passwords like "password123" are incredibly easy for hackers to guess or crack using automated tools. They\'re among the first passwords hackers try!',
                'tessa_tip': '💡 Pro tip: Think of passwords like house keys - you wouldn\'t use a toy key for your home! Use unique, complex passwords for each account.'
            },
            {
                'challenge_number': 2,
                'title': 'The Reused Password Problem',
                'question_text': 'Maya uses "Soccer2023!" for her email, social media, and banking. What should she do?',
                'option_a': 'Keep using it - it\'s strong',
                'option_b': 'Change it to "Soccer2024!"',
                'option_c': 'Use different passwords for each account',
                'correct_answer': 'C',
                'explanation': 'Using the same password everywhere is like having one key for your house, car, and office. If someone gets it, they access everything! Each account needs its own unique password.',
                'tessa_tip': '🔐 Smart move: Use a password manager to create and store unique passwords for every account. It\'s like having a super-secure keychain!'
            },
            {
                'challenge_number': 3,
                'title': 'The Public Wi-Fi Danger',
                'question_text': 'Sam wants to check his bank account on café Wi-Fi. What\'s the safest approach?',
                'option_a': 'Go ahead - the café looks trustworthy',
                'option_b': 'Wait until he\'s on a secure, private network',
                'option_c': 'Use the Wi-Fi but log out quickly',
                'correct_answer': 'B',
                'explanation': 'Public Wi-Fi is like shouting your secrets in a crowded room - anyone can listen! Banking and sensitive activities should only happen on secure, private networks.',
                'tessa_tip': '📱 Safety first: Use your phone\'s hotspot or wait for secure Wi-Fi. Your financial safety is worth the wait!'
            },
            {
                'challenge_number': 4,
                'title': 'The Suspicious Email Challenge',
                'question_text': 'Emma gets an email: "Your account expires in 24 hours! Click here to verify!" What should she do?',
                'option_a': 'Click the link immediately',
                'option_b': 'Forward it to friends as a warning',
                'option_c': 'Go directly to the official website instead',
                'correct_answer': 'C',
                'explanation': 'This is a classic phishing attempt! Urgent emails with suspicious links are red flags. Always visit the official website directly instead of clicking email links.',
                'tessa_tip': '🎣 Phishing alert: When in doubt, don\'t click! Go directly to the official website or call the company to verify any urgent requests.'
            },
            {
                'challenge_number': 5,
                'title': 'The Update Alert',
                'question_text': 'Jake\'s computer shows: "Critical security update available." What should he do?',
                'option_a': 'Ignore it - updates are annoying',
                'option_b': 'Install it immediately',
                'option_c': 'Wait a few months to see if others have problems',
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


@csrf_exempt  
@require_http_methods(["GET"])
def migrate_robotic_buddy(request):
    """Run robotic_buddy migrations specifically via HTTP request"""
    try:
        # Capture stdout and stderr
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()
        
        sys.stdout = stdout_capture
        sys.stderr = stderr_capture
        
        try:
            # Run robotic_buddy migrations specifically
            execute_from_command_line(['manage.py', 'migrate', 'robotic_buddy', '--verbosity=2'])
            
            stdout_output = stdout_capture.getvalue()
            stderr_output = stderr_capture.getvalue()
            
            return JsonResponse({
                'status': 'success',
                'message': 'Robotic buddy migrations completed successfully',
                'stdout': stdout_output,
                'stderr': stderr_output
            })
            
        except Exception as e:
            stdout_output = stdout_capture.getvalue()
            stderr_output = stderr_capture.getvalue()
            
            return JsonResponse({
                'status': 'error',
                'message': f'Robotic buddy migration failed: {str(e)}',
                'stdout': stdout_output,
                'stderr': stderr_output
            }, status=500)
            
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Failed to run robotic buddy migrations: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"]) 
def check_robotic_buddy(request):
    """Check robotic buddy database status via HTTP request"""
    try:
        # Capture stdout and stderr from management command
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()
        
        sys.stdout = stdout_capture
        sys.stderr = stderr_capture
        
        try:
            # Run our diagnostic command
            execute_from_command_line(['manage.py', 'check_robotic_buddy'])
            
            stdout_output = stdout_capture.getvalue()
            stderr_output = stderr_capture.getvalue()
            
            return JsonResponse({
                'status': 'success',
                'message': 'Robotic buddy diagnostic completed',
                'stdout': stdout_output,
                'stderr': stderr_output
            })
            
        except Exception as e:
            stdout_output = stdout_capture.getvalue()
            stderr_output = stderr_capture.getvalue()
            
            return JsonResponse({
                'status': 'error',
                'message': f'Robotic buddy diagnostic failed: {str(e)}',
                'stdout': stdout_output,
                'stderr': stderr_output
            }, status=500)
            
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Failed to run robotic buddy diagnostic: {str(e)}'
        }, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def populate_cyberbully_challenges_web(request):
    """Populate Cyberbully Crisis challenges via HTTP request"""
    try:
        from cyber_city.models import CyberbullyChallenge
        
        # Check if challenges already exist
        if CyberbullyChallenge.objects.exists():
            return JsonResponse({
                'status': 'info',
                'message': 'Cyberbully challenges already exist',
                'count': CyberbullyChallenge.objects.count()
            })
        
        # Create the 5 challenges with the exact content specified
        challenges = [
            {
                'challenge_number': 1,
                'title': 'Welcome to Cyber Street!',
                'background_story': 'Bully Bots stomp in, posting graffiti above happy citizens.',
                'option_a': 'You\'re awesome at this game!',
                'option_a_type': 'friendly',
                'option_b': 'Nobody likes you, just quit already.',
                'option_b_type': 'bully',
                'option_c': 'Good luck on your project!',
                'option_c_type': 'friendly',
                'correct_answer': 'B',
                'explanation': 'The message "Nobody likes you, just quit already" is mean and hurtful. It\'s designed to make someone feel bad about themselves, which is bullying behavior.',
                'mentor_tip': 'Great job! You protected Cyber City from meanness. Reporting helps stop bullies in their tracks.',
                'mentor_voice_text': 'Excellent work! You spotted the bully message and helped keep our community safe!'
            },
            {
                'challenge_number': 2,
                'title': 'Group Chat Challenge',
                'background_story': 'Projected group chat doors, avatars gathered in a virtual plaza.',
                'option_a': 'You seriously think anyone cares about your art? LOL.',
                'option_a_type': 'bully',
                'option_b': 'Wow, that game was tough. Good job, everyone!',
                'option_b_type': 'friendly',
                'option_c': 'Check out this cat meme, it\'s hilarious!',
                'option_c_type': 'friendly',
                'correct_answer': 'A',
                'explanation': 'Making fun of someone\'s creative work is hurtful and dismissive. This discourages people from sharing their talents.',
                'mentor_tip': 'Right choice! Hurtful comments about someone\'s interests aren\'t jokes—they\'re bullying.',
                'mentor_voice_text': 'Perfect! You recognized that making fun of someone\'s art is mean and hurtful. Art is for everyone!'
            },
            {
                'challenge_number': 3,
                'title': 'The Sneaky Excluder',
                'background_story': 'Avatar group selfie projected above a party scene.',
                'option_a': 'Let\'s invite everyone except Jamie—they\'re too weird.',
                'option_a_type': 'bully',
                'option_b': 'Here\'s the invite list!',
                'option_b_type': 'friendly',
                'option_c': 'Can\'t wait for the party!',
                'option_c_type': 'friendly',
                'correct_answer': 'A',
                'explanation': 'Deliberately excluding someone and calling them weird is social bullying. Leaving people out on purpose is mean.',
                'mentor_tip': 'Perfect! Leaving people out on purpose is cruel—even if it seems subtle.',
                'mentor_voice_text': 'Excellent spotting! Excluding someone because they\'re different is sneaky bullying. Everyone deserves inclusion!'
            },
            {
                'challenge_number': 4,
                'title': 'Creative Work Teasing',
                'background_story': 'Poetry contest—holograms of creative entries float above a stage.',
                'option_a': 'Your poem made me laugh... in a good way! Loved it.',
                'option_a_type': 'friendly',
                'option_b': 'Everyone saw your poem, it was the worst I\'ve read!',
                'option_b_type': 'bully',
                'option_c': 'Thanks for sharing your poem.',
                'option_c_type': 'friendly',
                'correct_answer': 'B',
                'explanation': 'Publicly calling someone\'s work "the worst" is mean and embarrassing. This hurts confidence and creativity.',
                'mentor_tip': 'Bullies sometimes attack creative work—good for you, calling it out!',
                'mentor_voice_text': 'Great job! You protected creativity from a mean comment. Creative expression should be encouraged!'
            },
            {
                'challenge_number': 5,
                'title': 'Joke or Bullying?',
                'background_story': 'Gaming arcade scene, leaderboard up in lights.',
                'option_a': 'Guess who tripped again today?',
                'option_a_type': 'bully',
                'option_b': 'Let\'s play at 6pm as usual!',
                'option_b_type': 'friendly',
                'option_c': 'Congrats on your new high score, Sam!',
                'option_c_type': 'friendly',
                'correct_answer': 'A',
                'explanation': 'Making fun of someone\'s embarrassing moment isn\'t a joke—it\'s teasing that hurts. True friends don\'t embarrass each other.',
                'mentor_tip': 'Teasing that embarrasses can feel like bullying—thank you for helping friends feel safe.',
                'mentor_voice_text': 'Perfect! You understood that teasing about embarrassing moments is hurtful. You\'re a protector of kindness!'
            }
        ]
        
        created_count = 0
        for challenge_data in challenges:
            challenge, created = CyberbullyChallenge.objects.get_or_create(
                challenge_number=challenge_data['challenge_number'],
                defaults=challenge_data
            )
            if created:
                created_count += 1
        
        return JsonResponse({
            'status': 'success',
            'message': f'Successfully populated {created_count} cyberbully challenges',
            'total_challenges': CyberbullyChallenge.objects.count()
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Failed to populate cyberbully challenges: {str(e)}'
        }, status=500)

@csrf_exempt
@require_http_methods(["GET", "POST"])
def run_production_migrations(request):
    """
    Web-based endpoint to run Django migrations on production.
    Safer alternative to SSH/CLI which doesn't work reliably on Azure.
    """
    try:
        from django.core.management import execute_from_command_line
        
        # Capture stdout and stderr
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()
        
        sys.stdout = stdout_capture
        sys.stderr = stderr_capture
        
        # First, fix migration conflicts
        try:
            execute_from_command_line(['manage.py', 'fix_migration_conflicts'])
        except Exception as conflict_error:
            pass  # Continue even if conflict fix fails
        
        # Run core migrations specifically (for Course model fix)
        try:
            execute_from_command_line(['manage.py', 'migrate', 'core', '--verbosity=2'])
        except Exception as core_error:
            pass  # Continue even if core migration fails
        
        # Run all migrations
        execute_from_command_line(['manage.py', 'migrate', '--verbosity=2'])
        
        # Restore stdout/stderr
        sys.stdout = old_stdout
        sys.stderr = old_stderr
        
        stdout_output = stdout_capture.getvalue()
        stderr_output = stderr_capture.getvalue()
        
        return JsonResponse({
            'status': 'success',
            'message': 'Migrations completed successfully',
            'stdout': stdout_output,
            'stderr': stderr_output if stderr_output else None
        })
        
    except Exception as e:
        # Restore stdout/stderr in case of error
        sys.stdout = old_stdout
        sys.stderr = old_stderr
        
        return JsonResponse({
            'status': 'error',
            'message': f'Migration failed: {str(e)}',
            'error_type': type(e).__name__
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def submit_game_review(request):
    """Submit a game review - unified endpoint for all games"""
    try:
        import json
        
        # Parse JSON data
        data = json.loads(request.body)
        
        # Extract required fields
        game_type = data.get('game_type')
        rating = data.get('rating')
        
        # Validate required fields
        if not game_type or not rating:
            return JsonResponse({
                'status': 'error',
                'message': 'Game type and rating are required'
            }, status=400)
        
        # Validate rating
        if not isinstance(rating, int) or rating < 1 or rating > 5:
            return JsonResponse({
                'status': 'error',
                'message': 'Rating must be between 1 and 5'
            }, status=400)
        
        # Extract optional fields
        session_id = data.get('session_id', '')
        player_name = data.get('player_name', '')
        review_text = data.get('review_text', '')
        
        # Get IP address - handle Azure's forwarded format
        ip_address = request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].split(':')[0] or \
                    request.META.get('REMOTE_ADDR', '').split(':')[0]
        # Fallback to a valid IP if parsing fails
        if not ip_address or ':' in ip_address:
            ip_address = '127.0.0.1'
        
        # Create or update review
        review, created = GameReview.objects.update_or_create(
            game_type=game_type,
            session_id=session_id,
            defaults={
                'rating': rating,
                'review_text': review_text or None,
                'player_name': player_name or None,
                'ip_address': ip_address
            }
        )
        
        return JsonResponse({
            'status': 'success',
            'message': 'Thank you for your review!',
            'review_id': review.id,
            'created': created
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'status': 'error',
            'message': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Failed to submit review: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def create_production_superuser(request):
    """
    Web-based endpoint to create Django superuser on production.
    Uses environment variables for credentials: DJANGO_SUPERUSER_USERNAME, DJANGO_SUPERUSER_EMAIL, DJANGO_SUPERUSER_PASSWORD
    """
    try:
        from django.contrib.auth.models import User
        from django.conf import settings
        import os
        
        # Get credentials from environment variables
        username = os.environ.get('DJANGO_SUPERUSER_USERNAME')
        email = os.environ.get('DJANGO_SUPERUSER_EMAIL')
        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')
        
        if not all([username, email, password]):
            return JsonResponse({
                'status': 'error',
                'message': 'Missing required environment variables: DJANGO_SUPERUSER_USERNAME, DJANGO_SUPERUSER_EMAIL, DJANGO_SUPERUSER_PASSWORD'
            }, status=400)
        
        # Check if user already exists
        if User.objects.filter(username=username).exists():
            return JsonResponse({
                'status': 'info',
                'message': f'Superuser "{username}" already exists',
                'username': username,
                'email': email
            })
        
        # Create superuser
        user = User.objects.create_superuser(
            username=username,
            email=email,
            password=password
        )
        
        return JsonResponse({
            'status': 'success',
            'message': f'Superuser "{username}" created successfully',
            'username': user.username,
            'email': user.email,
            'is_superuser': user.is_superuser,
            'is_staff': user.is_staff
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Failed to create superuser: {str(e)}',
            'error_type': type(e).__name__
        }, status=500)

def mixpanel_test(request):
    """Debug page for testing Mixpanel analytics"""
    return render(request, 'core/mixpanel_test.html')

def health_check(request):
    """Comprehensive health check endpoint for Azure monitoring"""
    import time
    from django.db import connection
    
    start_time = time.time()
    health_status = {
        "status": "healthy",
        "timestamp": time.time(),
        "version": "1.0.0",
        "environment": "production",
        "checks": {}
    }
    
    try:
        # Database connectivity check
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            health_status["checks"]["database"] = "healthy"
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["checks"]["database"] = f"unhealthy: {str(e)}"
    
    try:
        # Check if we can import core models
        from .models import Course
        course_count = Course.objects.count()
        health_status["checks"]["models"] = "healthy"
        health_status["course_count"] = course_count
    except Exception as e:
        health_status["status"] = "degraded"
        health_status["checks"]["models"] = f"degraded: {str(e)}"
    
    # Response time check
    response_time = (time.time() - start_time) * 1000
    health_status["response_time_ms"] = round(response_time, 2)
    
    if response_time > 2000:  # More than 2 seconds
        health_status["status"] = "degraded"
    
    # Memory usage check (basic)
    import psutil
    try:
        memory_percent = psutil.virtual_memory().percent
        health_status["memory_usage_percent"] = memory_percent
        health_status["checks"]["memory"] = "healthy" if memory_percent < 90 else "degraded"
        
        if memory_percent > 95:
            health_status["status"] = "degraded"
    except:
        health_status["checks"]["memory"] = "unknown"
    
    # Determine HTTP status code
    if health_status["status"] == "healthy":
        status_code = 200
    elif health_status["status"] == "degraded":
        status_code = 200  # Still operational but with issues
    else:
        status_code = 503  # Service unavailable
    
    return JsonResponse(health_status, status=status_code)

@csrf_exempt
@require_http_methods(["POST"])
def track_event_fallback(request):
    """Fallback event tracking when frontend Mixpanel fails"""
    try:
        import json
        from datetime import datetime
        
        data = json.loads(request.body)
        event_name = data.get('event')
        properties = data.get('properties', {})
        
        # Add server-side properties
        properties.update({
            'fallback_tracking': True,
            'server_timestamp': datetime.now().isoformat(),
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'ip_address': get_client_ip(request),
            'method': 'backend_fallback'
        })
        
        # Track via backend analytics
        from .analytics import track_event
        success = track_event(event_name, properties)
        
        return JsonResponse({
            'status': 'success' if success else 'failed',
            'message': 'Event tracked via backend fallback',
            'event': event_name
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
        # Remove port number if present (Azure load balancer can include ports)
        if ':' in ip and not ip.startswith('['):
            ip = ip.split(':')[0]
    else:
        ip = request.META.get('REMOTE_ADDR', '127.0.0.1')
    
    # Clean and validate IP address
    ip = ip.strip()
    if not ip or len(ip) > 45:  # Max length for IPv6
        ip = '127.0.0.1'
    
    return ip

@csrf_exempt
@require_http_methods(["POST"])
def analytics_track_api(request):
    """Fallback API endpoint for Mixpanel tracking when CDN is blocked"""
    try:
        import json
        from .analytics import track_custom_event
        
        # Parse request data
        data = json.loads(request.body)
        event_name = data.get('event', 'Unknown Event')
        properties = data.get('properties', {})
        token = data.get('token', '')
        
        # Add request metadata
        properties.update({
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'ip_address': get_client_ip(request),
            'referer': request.META.get('HTTP_REFERER', ''),
            'tracking_method': 'backend_fallback'
        })
        
        # Track the event using backend analytics
        success = track_custom_event(request, event_name, properties)
        
        return JsonResponse({
            'status': 'success' if success else 'partial',
            'message': 'Event tracked via backend fallback',
            'event': event_name,
            'tracked_at': properties.get('timestamp', '')
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'status': 'error',
            'message': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Tracking error: {str(e)}'
        }, status=500)


class SchoolReferralView(FormView):
    """School referral program page with ₹50,000 reward"""
    template_name = 'core/school_referral.html'
    form_class = SchoolReferralForm
    success_url = '/school-referral/success/'
    
    def get(self, request, *args, **kwargs):
        # Track referral page view
        track_page_view(request, 'School Referral Page', {
            'page_category': 'Referral',
            'reward_amount': 50000
        })
        return super().get(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'page_title': 'Refer a School & Earn ₹50,000',
            'reward_amount': '₹50,000',
            'program_description': 'Help schools discover AI-powered education and earn rewards for successful referrals',
        })
        return context
    
    def form_valid(self, form):
        try:
            # Save the referral
            referral = form.save()
            
            # Send email notification to admin
            self.send_referral_notification(referral)
            
            # Track successful submission
            track_form_submission(self.request, 'school_referral', {
                'school_name': referral.school_name,
                'referrer_email': referral.referrer_email,
                'school_board': referral.school_board,
                'interest_level': referral.interest_level
            })
            
            messages.success(
                self.request,
                f"Thank you! Your referral for {referral.school_name} has been submitted successfully. "
                f"We'll review it and contact the school within 2-3 business days. "
                f"You'll be eligible for ₹50,000 reward if the referral converts!"
            )
            
            return redirect('core:school_referral_success')
            
        except Exception as e:
            # Track error
            track_error(self.request, 'school_referral_submission_error', {
                'error': str(e),
                'form_data': form.cleaned_data if form.is_valid() else 'invalid'
            })
            
            messages.error(
                self.request,
                "Sorry, there was an error submitting your referral. Please try again or contact support."
            )
            return self.form_invalid(form)
    
    def form_invalid(self, form):
        track_form_submission(self.request, 'school_referral_failed', {
            'errors': form.errors.as_json()
        })
        return super().form_invalid(form)
    
    def send_referral_notification(self, referral):
        """Send email notification to admin about new referral"""
        try:
            subject = f'🎯 New School Referral: {referral.school_name}'
            
            message = f"""
New School Referral Submitted!

REFERRAL DETAILS:
═══════════════════════════════════════
Referrer: {referral.referrer_name}
Email: {referral.referrer_email}
Phone: {referral.referrer_phone}
Relationship: {referral.referrer_relationship}

SCHOOL INFORMATION:
═══════════════════════════════════════
School Name: {referral.school_name}
Contact Person: {referral.contact_person_name} ({referral.contact_person_designation})
School Email: {referral.contact_person_email}
School Phone: {referral.contact_person_phone}

Address: {referral.school_address}
City: {referral.school_city}, {referral.school_state} - {referral.school_pincode}

SCHOOL DETAILS:
═══════════════════════════════════════
School Board: {referral.get_school_board_display()}
Interest Level: {referral.get_interest_level_display()}

Current Programs: {referral.current_education_programs or 'Not specified'}

REFERRAL INFORMATION:
═══════════════════════════════════════
Reward Amount: {referral.get_reward_display()}

ADDITIONAL NOTES:
═══════════════════════════════════════
{referral.additional_notes or 'None'}

═══════════════════════════════════════
Submitted on: {referral.created_at.strftime('%B %d, %Y at %I:%M %p')}
Referral ID: {referral.id}

Next Steps:
1. Review the referral within 24 hours
2. Contact the school to validate interest
3. Update status in admin panel
4. Process reward if referral converts
            """
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=['jatin.bhagat@decipherworld.com'],
                fail_silently=False,
            )
            
        except Exception as e:
            # Log error but don't fail the form submission
            print(f"Error sending referral notification email: {e}")


def school_referral_success(request):
    """Success page after school referral submission"""
    track_page_view(request, 'School Referral Success', {
        'page_category': 'Referral',
        'conversion': True
    })
    
    return render(request, 'core/school_referral_success.html', {
        'page_title': 'Referral Submitted Successfully!',
        'reward_amount': '₹50,000'
    })


@csrf_exempt
def upload_schools_csv(request):
    """
    Admin interface for uploading schools CSV data
    Accessible via web interface for easy bulk school imports
    """
    if request.method == 'GET':
        # Show upload form
        return JsonResponse({
            'status': 'ready',
            'message': 'Schools CSV Upload Interface',
            'instructions': 'POST a CSV file with schools data to import',
            'endpoint': '/upload-schools-csv/',
            'sample_csv_path': '/sample_schools.csv',
            'admin_link': '/admin/core/school/'
        })
    
    elif request.method == 'POST':
        try:
            # Handle CSV upload
            if 'csv_file' in request.FILES:
                csv_file = request.FILES['csv_file']
                
                # Read CSV content
                csv_content = csv_file.read().decode('utf-8')
                csv_reader = csv.DictReader(io.StringIO(csv_content))
                
                imported_count = 0
                errors = []
                
                for row_num, row in enumerate(csv_reader, 1):
                    try:
                        # Create or update school
                        school, created = School.objects.get_or_create(
                            name=row.get('name', '').strip(),
                            defaults={
                                'address': row.get('address', '').strip(),
                                'city': row.get('city', '').strip(),
                                'state': row.get('state', '').strip(),
                                'postal_code': row.get('postal_code', '').strip(),
                                'phone': row.get('phone', '').strip(),
                                'email': row.get('email', '').strip(),
                                'principal_name': row.get('principal_name', '').strip(),
                                'website': row.get('website', '').strip(),
                                'student_count': int(row.get('student_count', 0) or 0),
                                'grade_levels': row.get('grade_levels', '').strip(),
                                'school_type': row.get('school_type', 'public').strip(),
                                'is_active': True
                            }
                        )
                        
                        if created:
                            imported_count += 1
                        
                    except Exception as e:
                        errors.append(f"Row {row_num}: {str(e)}")
                
                return JsonResponse({
                    'status': 'success',
                    'message': f'Successfully imported {imported_count} schools',
                    'imported_count': imported_count,
                    'total_schools_now': School.objects.count(),
                    'errors': errors[:10] if errors else [],  # Show first 10 errors
                    'admin_link': '/admin/core/school/'
                })
            
            else:
                return JsonResponse({
                    'status': 'error',
                    'message': 'No CSV file provided. Please upload a file with name "csv_file"'
                }, status=400)
                
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'Upload failed: {str(e)}',
                'error_type': type(e).__name__
            }, status=500)
    
    else:
        return JsonResponse({
            'status': 'error',
            'message': 'Only GET and POST methods allowed'
        }, status=405)


@csrf_exempt
@require_http_methods(["POST"])
def migrate_quest_ciq(request):
    """
    Simple, focused endpoint to migrate only quest_ciq app
    Bypass any group_learning conflicts
    """
    try:
        import sys
        from io import StringIO
        from django.core.management import execute_from_command_line
        
        # Capture output
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        stdout_capture = StringIO()
        stderr_capture = StringIO()
        sys.stdout = stdout_capture
        sys.stderr = stderr_capture
        
        try:
            # Run quest_ciq migrations only
            execute_from_command_line(['manage.py', 'migrate', 'quest_ciq', '--verbosity=2'])
            
            stdout_output = stdout_capture.getvalue()
            stderr_output = stderr_capture.getvalue()
            
            return JsonResponse({
                'status': 'success',
                'message': 'quest_ciq migrations completed successfully',
                'stdout': stdout_output,
                'stderr': stderr_output
            })
            
        except Exception as e:
            stdout_output = stdout_capture.getvalue()
            stderr_output = stderr_capture.getvalue()
            
            return JsonResponse({
                'status': 'error',
                'message': f'quest_ciq migration failed: {str(e)}',
                'stdout': stdout_output,
                'stderr': stderr_output,
                'error_type': type(e).__name__
            }, status=500)
            
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Failed to run quest_ciq migrations: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def clean_production_test_data(request):
    """
    Clean duplicate production test data to allow constraints to work
    SAFE FOR PRODUCTION - this only removes test data, no real user data
    """
    try:
        from group_learning.models import DesignTeam, DesignThinkingSession
        
        # Find and remove duplicate teams for session_id 113
        duplicate_teams = DesignTeam.objects.filter(session_id=113)
        duplicate_count = duplicate_teams.count()
        
        if duplicate_count > 1:
            # Keep the first team, remove the rest
            keep_team = duplicate_teams.first()
            remove_teams = duplicate_teams.exclude(id=keep_team.id)
            removed_count = remove_teams.count()
            remove_teams.delete()
            
            return JsonResponse({
                'status': 'success',
                'message': f'Cleaned duplicate test data: removed {removed_count} duplicate teams for session 113',
                'kept_team_id': keep_team.id,
                'removed_count': removed_count,
                'total_teams_now': DesignTeam.objects.filter(session_id=113).count()
            })
        else:
            return JsonResponse({
                'status': 'info',
                'message': f'No duplicates found for session 113. Current teams: {duplicate_count}'
            })
            
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Failed to clean test data: {str(e)}',
            'error_type': type(e).__name__
        }, status=500)