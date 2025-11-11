"""
Views for Classroom Innovation Quest
Session-based design thinking quest flow
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.contrib.auth.mixins import UserPassesTestMixin
from .models import (
    QuestSession, LevelResponse, CIQSettings,
    Quest, ClassRoom, Team, TeacherTeamScore
)
from .forms import (
    JoinQuestForm,
    Level1EmpathyForm,
    Level2DefineForm,
    Level3IdeateForm,
    Level4PrototypeForm,
    Level5TestForm,
)
from .constants import LEVEL_CONFIG
from .services.scoring import get_team_aggregated_responses, get_team_scores, calculate_weighted_score


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

        # Level 5 is presentation-only (no form)
        if level_order == 5:
            # Mark as completed if not already
            if not session.completed_at:
                session.completed_at = timezone.now()
                session.save(update_fields=['completed_at'])

            # Recalculate final score
            from .services.scoring import calculate_student_score
            session.total_score = calculate_student_score(session)
            session.save(update_fields=['total_score'])

            level_config = LEVEL_CONFIG.get(level_order, {})

            context = {
                'session': session,
                'level_order': level_order,
                'level_config': level_config,
                'form': None,  # No form for Level 5
                'already_completed': True,
            }

            return render(request, self.template_name, context)

        # Get form class for other levels
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

        # Level 5 is read-only, no POST allowed
        if level_order == 5:
            messages.info(request, "Level 5 is presentation-only, no submission needed.")
            return redirect('quest_ciq:level', session_code=session_code, level_order=5)

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
            form = form_class(quest_session=session, data=request.POST, files=request.FILES)
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

        # Get view type from query param (default: participants)
        view_type = request.GET.get('view', 'participants')

        if view_type == 'teams':
            # Get all teams with at least one completed session
            teams_data = []
            teams = Team.objects.filter(
                sessions__completed_at__isnull=False
            ).distinct()

            for team in teams:
                if not team.classroom:
                    continue

                # Get team scores
                scores = get_team_scores(team, team.classroom)

                teams_data.append({
                    'team': team,
                    'classroom': team.classroom,
                    'member_count': scores['members_count'],
                    'avg_student_score': scores['avg_student_score'],
                    'teacher_score': scores['teacher_score'],
                    'final_score': scores['avg_final_score'],
                    'awaiting_teacher': scores['awaiting_teacher'],
                })

            # Sort by final score descending
            teams_data.sort(key=lambda x: x['final_score'], reverse=True)

            context = {
                'view_type': 'teams',
                'teams_data': teams_data[:50],  # Top 50
            }
        else:
            # Participants view (existing logic with weighted scores)
            from .services.scoring import get_final_score

            sessions = QuestSession.objects.filter(
                completed_at__isnull=False
            ).select_related('team', 'classroom').order_by('-created_at')[:100]

            participants_data = []
            for session in sessions:
                score_data = get_final_score(session)
                participants_data.append({
                    'session': session,
                    'student_score': score_data['student_score'],
                    'teacher_score': score_data['teacher_score'],
                    'final_score': score_data['final_score'],
                    'awaiting_teacher': score_data['awaiting_teacher'],
                })

            # Sort by final score descending
            participants_data.sort(key=lambda x: x['final_score'], reverse=True)

            context = {
                'view_type': 'participants',
                'participants_data': participants_data[:50],  # Top 50
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


class PublicPresentationView(View):
    """Public read-only team presentation page"""
    template_name = 'quest_ciq/present_public.html'

    def get(self, request, slug, class_code, team_slug):
        # Get quest, classroom, and team
        quest = get_object_or_404(Quest, slug=slug, is_active=True)
        classroom = get_object_or_404(ClassRoom, class_code=class_code, quest=quest)
        team = get_object_or_404(Team, slug=team_slug, classroom=classroom)

        # Get aggregated responses from team members
        aggregated_responses = get_team_aggregated_responses(team, classroom)

        # Get team scores
        team_scores = get_team_scores(team, classroom)

        # Build presentation URL for sharing
        presentation_url = request.build_absolute_uri()

        context = {
            'quest': quest,
            'classroom': classroom,
            'team': team,
            'aggregated_responses': aggregated_responses,
            'team_scores': team_scores,
            'presentation_url': presentation_url,
        }

        return render(request, self.template_name, context)


class TeacherGradeView(View):
    """Teacher grading page for teams in a classroom"""
    template_name = 'quest_ciq/teacher_grade.html'

    def _check_teacher_access(self, request, classroom):
        """Check if user has teacher access (staff or valid teacher_key)"""
        # Check if user is staff
        if request.user.is_authenticated and request.user.is_staff:
            return True

        # Check if teacher_key is provided in session or GET param
        teacher_key = request.session.get('teacher_key') or request.GET.get('key')
        if teacher_key and classroom.teacher_key and teacher_key == classroom.teacher_key:
            # Save key in session for future requests
            request.session['teacher_key'] = teacher_key
            return True

        return False

    def get(self, request, class_code):
        classroom = get_object_or_404(ClassRoom, class_code=class_code, is_active=True)

        # Check access
        if not self._check_teacher_access(request, classroom):
            messages.error(request, "Access denied. Staff login or valid teacher key required.")
            return redirect('quest_ciq:home')

        quest = classroom.quest
        teams = classroom.teams.all().order_by('name')

        # Prepare team data with scores
        teams_data = []
        for team in teams:
            # Check if team has any sessions
            sessions = team.sessions.filter(classroom=classroom)
            if not sessions.exists():
                continue

            # Get existing teacher score if any
            try:
                teacher_score_obj = TeacherTeamScore.objects.get(
                    team=team,
                    classroom=classroom,
                    quest=quest
                )
                teacher_score = teacher_score_obj.score
                teacher_comment = teacher_score_obj.comment or ''
            except TeacherTeamScore.DoesNotExist:
                teacher_score = None
                teacher_comment = ''

            # Get team scores
            scores = get_team_scores(team, classroom)

            # Build presentation URL
            presentation_url = request.build_absolute_uri(
                f'/quest/quest/{quest.slug}/present/{class_code}/{team.slug}/'
            )

            teams_data.append({
                'team': team,
                'member_count': scores['members_count'],
                'avg_student_score': scores['avg_student_score'],
                'teacher_score': teacher_score,
                'teacher_comment': teacher_comment,
                'final_score': scores['avg_final_score'],
                'presentation_url': presentation_url,
            })

        context = {
            'classroom': classroom,
            'quest': quest,
            'teams_data': teams_data,
        }

        return render(request, self.template_name, context)

    def post(self, request, class_code):
        classroom = get_object_or_404(ClassRoom, class_code=class_code, is_active=True)

        # Check access
        if not self._check_teacher_access(request, classroom):
            messages.error(request, "Access denied. Staff login or valid teacher key required.")
            return redirect('quest_ciq:home')

        quest = classroom.quest
        team_id = request.POST.get('team_id')
        score = request.POST.get('score')
        comment = request.POST.get('comment', '')

        if not team_id or not score:
            messages.error(request, "Team and score are required.")
            return redirect('quest_ciq:teacher_grade', class_code=class_code)

        try:
            team = Team.objects.get(pk=team_id, classroom=classroom)
            score_int = int(score)

            if not (0 <= score_int <= 100):
                messages.error(request, "Score must be between 0 and 100.")
                return redirect('quest_ciq:teacher_grade', class_code=class_code)

            # Create or update teacher score
            teacher_score_obj, created = TeacherTeamScore.objects.update_or_create(
                team=team,
                classroom=classroom,
                quest=quest,
                defaults={
                    'score': score_int,
                    'comment': comment,
                    'graded_by': request.user if request.user.is_authenticated else None,
                }
            )

            # Recalculate weighted scores for all team members
            sessions = team.sessions.filter(classroom=classroom)
            for session in sessions:
                from .services.scoring import calculate_student_score
                student_score = calculate_student_score(session)
                weighted = calculate_weighted_score(student_score, score_int)
                session.total_score = weighted
                session.save(update_fields=['total_score'])

            action = "updated" if not created else "saved"
            messages.success(request, f"Score {action} for {team.name}! Weighted scores recalculated for all members.")

        except (Team.DoesNotExist, ValueError) as e:
            messages.error(request, f"Error saving score: {str(e)}")

        return redirect('quest_ciq:teacher_grade', class_code=class_code)
