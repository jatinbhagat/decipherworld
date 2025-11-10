from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, TemplateView
from django.urls import reverse
from django.utils import timezone
from django.db.models import Sum, Count, Q
import secrets

from .models import Quest, QuestLevel, Participant, QuestSession, LevelResponse, Leaderboard
from .forms import JoinQuestForm, LevelResponseForm, QuestCreationForm, QuestLevelForm
from .feature_flags import CIQFeatureMixin, require_ciq_enabled
from .services.scoring import calculate_level_score, update_leaderboard


@require_ciq_enabled
def home_view(request):
    """Home page listing all active quests"""
    context = {
        'active_quests': Quest.objects.filter(is_active=True).prefetch_related('levels'),
        'page_title': 'Quest CIQ - Curiosity Intelligence Quest'
    }
    return render(request, 'quest_ciq/home.html', context)


@require_ciq_enabled
def join_quest_view(request, quest_slug):
    """Join a quest and create participant session"""
    quest = get_object_or_404(Quest, slug=quest_slug, is_active=True)

    if request.method == 'POST':
        form = JoinQuestForm(request.POST)
        if form.is_valid():
            participant = form.save(commit=False)
            participant.join_code = secrets.token_urlsafe(16)[:20]

            # Link to user if authenticated
            if request.user.is_authenticated:
                participant.user = request.user

            participant.save()

            # Create quest session
            session = QuestSession.objects.create(
                quest=quest,
                participant=participant,
                status='not_started',
                current_level=1
            )

            # Store participant info in session
            request.session['participant_id'] = participant.id
            request.session['join_code'] = participant.join_code

            messages.success(request, f'Welcome {participant.display_name}! Your quest begins now.')
            return redirect('quest_ciq:level', quest_slug=quest.slug, level_number=1)
    else:
        form = JoinQuestForm()

    context = {
        'quest': quest,
        'form': form,
        'page_title': f'Join {quest.title}'
    }
    return render(request, 'quest_ciq/join.html', context)


@require_ciq_enabled
def level_view(request, quest_slug, level_number):
    """Display and handle a specific level"""
    quest = get_object_or_404(Quest, slug=quest_slug, is_active=True)
    level = get_object_or_404(QuestLevel, quest=quest, level_number=level_number)

    # Get participant from session
    participant_id = request.session.get('participant_id')
    if not participant_id:
        messages.warning(request, 'Please join the quest first.')
        return redirect('quest_ciq:join', quest_slug=quest.slug)

    participant = get_object_or_404(Participant, id=participant_id)
    session = get_object_or_404(QuestSession, quest=quest, participant=participant)

    # Start session if not started
    if session.status == 'not_started':
        session.start_session()

    # Check if already answered
    existing_response = LevelResponse.objects.filter(session=session, level=level).first()

    if request.method == 'POST' and not existing_response:
        form = LevelResponseForm(request.POST)
        if form.is_valid():
            response = form.save(commit=False)
            response.session = session
            response.level = level

            # Calculate score
            response.score = calculate_level_score(response.response_text, level)

            response.save()

            # Update session score
            session.total_score = session.level_responses.aggregate(Sum('score'))['score__sum'] or 0
            session.current_level = max(session.current_level, level_number + 1)
            session.save()

            # Check if quest complete
            total_levels = quest.levels.count()
            if level_number >= total_levels:
                session.complete_session()
                update_leaderboard(session)
                messages.success(request, 'Congratulations! You completed the quest!')
                return redirect('quest_ciq:summary', quest_slug=quest.slug)

            messages.success(request, f'Level {level_number} complete! Score: {response.score}')
            return redirect('quest_ciq:level', quest_slug=quest.slug, level_number=level_number + 1)
    else:
        form = LevelResponseForm()

    context = {
        'quest': quest,
        'level': level,
        'session': session,
        'form': form,
        'existing_response': existing_response,
        'total_levels': quest.levels.count(),
        'page_title': f'{quest.title} - Level {level_number}'
    }
    return render(request, 'quest_ciq/level.html', context)


@require_ciq_enabled
def summary_view(request, quest_slug):
    """Show quest completion summary"""
    quest = get_object_or_404(Quest, slug=quest_slug)

    participant_id = request.session.get('participant_id')
    if not participant_id:
        messages.warning(request, 'No session found.')
        return redirect('quest_ciq:home')

    participant = get_object_or_404(Participant, id=participant_id)
    session = get_object_or_404(QuestSession, quest=quest, participant=participant)

    responses = session.level_responses.select_related('level').order_by('level__level_number')

    context = {
        'quest': quest,
        'session': session,
        'responses': responses,
        'page_title': f'Summary - {quest.title}'
    }
    return render(request, 'quest_ciq/summary.html', context)


@require_ciq_enabled
def leaderboard_view(request, quest_slug):
    """Display quest leaderboard"""
    quest = get_object_or_404(Quest, slug=quest_slug)

    leaderboard = Leaderboard.objects.filter(quest=quest).select_related('participant').order_by('rank')[:100]

    # Get current participant's rank if available
    participant_id = request.session.get('participant_id')
    current_rank = None
    if participant_id:
        try:
            participant = Participant.objects.get(id=participant_id)
            current_rank = Leaderboard.objects.filter(quest=quest, participant=participant).first()
        except Participant.DoesNotExist:
            pass

    context = {
        'quest': quest,
        'leaderboard': leaderboard,
        'current_rank': current_rank,
        'page_title': f'Leaderboard - {quest.title}'
    }
    return render(request, 'quest_ciq/leaderboard.html', context)


@require_ciq_enabled
def teacher_dashboard_view(request):
    """Teacher dashboard to manage quests"""
    quests = Quest.objects.annotate(
        participant_count=Count('sessions', distinct=True),
        completed_count=Count('sessions', filter=Q(sessions__status='completed'), distinct=True)
    ).order_by('-created_at')

    context = {
        'quests': quests,
        'page_title': 'Teacher Dashboard'
    }
    return render(request, 'quest_ciq/teacher_dash.html', context)


@require_ciq_enabled
def facilitate_view(request, quest_slug):
    """Real-time facilitation view for teachers"""
    quest = get_object_or_404(Quest, slug=quest_slug)

    sessions = QuestSession.objects.filter(quest=quest).select_related('participant').order_by('-started_at')

    stats = {
        'total_participants': sessions.count(),
        'in_progress': sessions.filter(status='in_progress').count(),
        'completed': sessions.filter(status='completed').count(),
        'average_score': sessions.filter(status='completed').aggregate(avg_score=Sum('total_score'))['avg_score'] or 0
    }

    context = {
        'quest': quest,
        'sessions': sessions,
        'stats': stats,
        'page_title': f'Facilitate - {quest.title}'
    }
    return render(request, 'quest_ciq/facilitate.html', context)
