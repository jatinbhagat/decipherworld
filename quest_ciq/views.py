"""
Views for Classroom Innovation Quest
Session-based design thinking quest flow
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from .models import QuestSession, LevelResponse, CIQSettings
from .forms import (
    JoinQuestForm,
    Level1EmpathyForm,
    Level2DefineForm,
    Level3IdeateForm,
    Level4PrototypeForm,
    Level5TestForm,
)
from .constants import LEVEL_CONFIG


class HomeView(View):
    """Landing page for CIQ"""
    template_name = 'quest_ciq/home.html'

    def get(self, request):
        # Check if CIQ is enabled
        settings = CIQSettings.get_settings()
        if not settings.enable_ciq:
            return render(request, 'quest_ciq/disabled.html')

        return render(request, self.template_name)


class JoinQuestView(View):
    """Create new quest session (no authentication)"""
    template_name = 'quest_ciq/join.html'

    def get(self, request):
        form = JoinQuestForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = JoinQuestForm(request.POST)
        if form.is_valid():
            # Create new session
            session = QuestSession.objects.create(
                student_name=form.cleaned_data['student_name']
            )

            # Store session code in session for student access
            request.session['quest_session_code'] = session.session_code

            messages.success(
                request,
                f"Welcome {session.student_name}! Your quest begins now."
            )

            # Redirect to Level 1
            return redirect('quest_ciq:level', session_code=session.session_code, level_order=1)

        return render(request, self.template_name, {'form': form})


class LevelView(View):
    """Generic level view - handles all 5 levels"""
    template_name = 'quest_ciq/level.html'

    LEVEL_FORMS = {
        1: Level1EmpathyForm,
        2: Level2DefineForm,
        3: Level3IdeateForm,
        4: Level4PrototypeForm,
        5: Level5TestForm,
    }

    def get_session(self, request, session_code):
        """Get session and validate access"""
        session = get_object_or_404(QuestSession, session_code=session_code)

        # Session-based access (no auth)
        # Store session code in Django session
        request.session['quest_session_code'] = session_code

        return session

    def check_prerequisites(self, session, level_order):
        """Check if previous level is completed"""
        if level_order == 1:
            return True

        # Check if L3 exists before allowing L4
        if level_order == 4:
            try:
                l3_response = LevelResponse.objects.get(session=session, level_order=3)
                l3_answers = l3_response.get_answers()
                ideas = l3_answers.get('ideas', [])
                if not any(i.strip() for i in ideas):
                    return False
            except LevelResponse.DoesNotExist:
                return False

        # General prerequisite check
        return LevelResponse.objects.filter(
            session=session,
            level_order=level_order - 1
        ).exists()

    def get(self, request, session_code, level_order):
        session = self.get_session(request, session_code)

        # Validate level order
        if not (1 <= level_order <= 5):
            messages.error(request, "Invalid level.")
            return redirect('quest_ciq:home')

        # Check prerequisites
        if not self.check_prerequisites(session, level_order):
            messages.warning(
                request,
                f"Complete Level {level_order - 1} first!"
            )
            return redirect(
                'quest_ciq:level',
                session_code=session_code,
                level_order=level_order - 1
            )

        # Get form class for this level
        form_class = self.LEVEL_FORMS.get(level_order)
        if not form_class:
            messages.error(request, "Level not found.")
            return redirect('quest_ciq:home')

        # Initialize form (pass session for L2 and L4)
        if level_order in [2, 4]:
            form = form_class(quest_session=session)
        else:
            form = form_class()

        # Get level config
        level_config = LEVEL_CONFIG.get(level_order, {})

        # Check if already completed
        existing_response = LevelResponse.objects.filter(
            session=session,
            level_order=level_order
        ).first()

        context = {
            'session': session,
            'level_order': level_order,
            'level_config': level_config,
            'form': form,
            'already_completed': bool(existing_response),
            'existing_response': existing_response,
        }

        return render(request, self.template_name, context)

    def post(self, request, session_code, level_order):
        session = self.get_session(request, session_code)

        # Validate level order
        if not (1 <= level_order <= 5):
            messages.error(request, "Invalid level.")
            return redirect('quest_ciq:home')

        # Check prerequisites
        if not self.check_prerequisites(session, level_order):
            messages.warning(
                request,
                f"Complete Level {level_order - 1} first!"
            )
            return redirect(
                'quest_ciq:level',
                session_code=session_code,
                level_order=level_order - 1
            )

        # Get form class
        form_class = self.LEVEL_FORMS.get(level_order)

        # Initialize form with POST data
        if level_order in [2, 4]:
            form = form_class(request.POST, request.FILES, quest_session=session)
        else:
            form = form_class(request.POST, request.FILES)

        level_config = LEVEL_CONFIG.get(level_order, {})

        if form.is_valid():
            # Get answers JSON
            answers_json = form.get_answers_json()

            # Create or update response
            response, created = LevelResponse.objects.update_or_create(
                session=session,
                level_order=level_order,
                defaults={'answers': answers_json}
            )

            # Handle file upload for L4
            if level_order == 4 and request.FILES.get('prototype_upload'):
                # File handling would go here if MEDIA is configured
                pass

            # Recalculate score
            session.calculate_score()

            # Advance to next level
            if level_order < 5:
                session.advance_to_next_level()

            # Mark as completed if level 5
            if level_order == 5:
                session.completed_at = timezone.now()
                session.save(update_fields=['completed_at'])

            # Success message
            success_msg = level_config.get('success_message', 'Level complete!')
            messages.success(request, success_msg)

            # Redirect to next level or leaderboard
            if level_order < 5:
                return redirect(
                    'quest_ciq:level',
                    session_code=session_code,
                    level_order=level_order + 1
                )
            else:
                return redirect('quest_ciq:leaderboard')

        # Form invalid - re-render with errors
        context = {
            'session': session,
            'level_order': level_order,
            'level_config': level_config,
            'form': form,
            'already_completed': False,
        }

        return render(request, self.template_name, context)


class LeaderboardView(View):
    """Public leaderboard (no authentication required)"""
    template_name = 'quest_ciq/leaderboard.html'

    def get(self, request):
        settings = CIQSettings.get_settings()

        if not settings.show_leaderboard:
            messages.info(request, "Leaderboard is currently disabled.")
            return redirect('quest_ciq:home')

        # Get top sessions by score
        top_sessions = QuestSession.objects.filter(
            completed_at__isnull=False
        ).order_by('-total_score', 'completed_at')[:50]

        context = {
            'top_sessions': top_sessions,
        }

        return render(request, self.template_name, context)


class ProgressView(View):
    """Show student's progress"""
    template_name = 'quest_ciq/progress.html'

    def get(self, request, session_code):
        session = get_object_or_404(QuestSession, session_code=session_code)

        # Get all responses
        responses = session.responses.all().order_by('level_order')

        # Calculate progress
        progress_percent = (len(responses) / 5) * 100

        context = {
            'session': session,
            'responses': responses,
            'progress_percent': progress_percent,
            'level_config': LEVEL_CONFIG,
        }

        return render(request, self.template_name, context)
