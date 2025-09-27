from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.generic import TemplateView, ListView, FormView
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import sys
import io
from .models import DemoRequest, Course, SchoolDemoRequest, GameReview
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
        
        # Run migrations
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