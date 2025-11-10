"""
Views for Classroom Innovation Quest.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.http import Http404
from django.utils import timezone

from .models import Quest, QuestLevel, Participant, QuestSession, LevelResponse, Leaderboard
from .forms import get_form_for_level
from .services.scoring import score_and_update_session


def check_ciq_enabled():
    """Check if CIQ feature is enabled."""
    return getattr(settings, 'ENABLE_CIQ', False)


@login_required
def quest_home(request, slug):
    """Quest home page showing current progress and CTA to continue."""
    if not check_ciq_enabled():
        raise Http404("Classroom Innovation Quest is not enabled")

    quest = get_object_or_404(Quest, slug=slug, is_active=True)

    # Get or check participant status
    try:
        participant = Participant.objects.get(user=request.user, quest=quest)
    except Participant.DoesNotExist:
        # Redirect to join page
        return redirect('quest_ciq:quest_join', slug=slug)

    # Get active session
    session = participant.sessions.filter(quest=quest).order_by('-started_at').first()

    if not session:
        # Create new session if none exists
        session = QuestSession.objects.create(
            participant=participant,
            quest=quest
        )

    # Get current progress
    highest_level = session.get_highest_completed_level()
    next_level = highest_level + 1 if highest_level < 5 else None

    # Calculate progress percentage
    progress_percent = (highest_level / 5) * 100

    context = {
        'quest': quest,
        'session': session,
        'participant': participant,
        'highest_level': highest_level,
        'next_level': next_level,
        'progress_percent': progress_percent,
        'is_complete': highest_level >= 5,
    }

    return render(request, 'quest_ciq/home.html', context)


@login_required
def quest_join(request, slug):
    """Join a quest."""
    if not check_ciq_enabled():
        raise Http404("Classroom Innovation Quest is not enabled")

    quest = get_object_or_404(Quest, slug=slug, is_active=True)

    # Check if already a participant
    participant, created = Participant.objects.get_or_create(
        user=request.user,
        quest=quest,
        defaults={'is_active': True}
    )

    if created:
        messages.success(request, f'Welcome to {quest.title}! Let\'s start your journey.')
    else:
        messages.info(request, f'Welcome back to {quest.title}!')

    return redirect('quest_ciq:quest_home', slug=slug)


@login_required
def quest_level(request, slug, order):
    """
    Quest level form page.
    Implements gating: can only access level N if level N-1 is completed.
    """
    if not check_ciq_enabled():
        raise Http404("Classroom Innovation Quest is not enabled")

    quest = get_object_or_404(Quest, slug=slug, is_active=True)
    level = get_object_or_404(QuestLevel, quest=quest, order=order)

    # Get participant
    try:
        participant = Participant.objects.get(user=request.user, quest=quest)
    except Participant.DoesNotExist:
        messages.warning(request, 'Please join the quest first.')
        return redirect('quest_ciq:quest_join', slug=slug)

    # Get or create active session
    session = participant.sessions.filter(quest=quest).order_by('-started_at').first()
    if not session:
        session = QuestSession.objects.create(participant=participant, quest=quest)

    # Check if session is frozen
    if session.is_frozen:
        messages.error(request, 'This session is frozen. You cannot submit new responses.')
        return redirect('quest_ciq:quest_home', slug=slug)

    # Gating logic: Check if user can access this level
    if not session.can_access_level(order):
        messages.error(
            request,
            f'You must complete Level {order - 1} before accessing Level {order}.'
        )
        return redirect('quest_ciq:quest_home', slug=slug)

    # Get existing response if any
    existing_response = LevelResponse.objects.filter(
        session=session,
        level=level
    ).first()

    # Get form class
    FormClass = get_form_for_level(order)
    if not FormClass:
        raise Http404("Form not found for this level")

    if request.method == 'POST':
        # Handle file upload separately for prototype level
        if order == 4:
            form = FormClass(request.POST, request.FILES)
        else:
            form = FormClass(request.POST)

        if form.is_valid():
            # Save form data to answers JSON
            answers = form.cleaned_data.copy()

            # Handle file upload for prototype level
            prototype_upload = None
            if order == 4 and 'prototype_upload' in answers:
                prototype_upload = answers.pop('prototype_upload')

            # Create or update response
            if existing_response:
                existing_response.answers = answers
                if prototype_upload:
                    existing_response.prototype_upload = prototype_upload
                existing_response.save()
                response = existing_response
            else:
                response = LevelResponse.objects.create(
                    session=session,
                    level=level,
                    answers=answers,
                    prototype_upload=prototype_upload if order == 4 else None
                )

            # Calculate score and update session
            score_and_update_session(response)

            messages.success(
                request,
                f'Level {order} completed! You earned {response.score} points.'
            )

            # Check if this is the last level
            if order >= 5:
                session.completed_at = timezone.now()
                session.save()
                return redirect('quest_ciq:quest_summary', slug=slug)

            # Redirect to next level
            return redirect('quest_ciq:quest_level', slug=slug, order=order + 1)

    else:
        # Pre-fill form with existing answers
        if existing_response:
            form = FormClass(initial=existing_response.answers)
        else:
            form = FormClass()

    # Calculate progress
    progress_percent = (order / 5) * 100

    context = {
        'quest': quest,
        'level': level,
        'form': form,
        'session': session,
        'order': order,
        'progress_percent': progress_percent,
        'existing_response': existing_response,
        'is_frozen': session.is_frozen,
    }

    return render(request, 'quest_ciq/level.html', context)


@login_required
def quest_summary(request, slug):
    """Summary page showing all level responses."""
    if not check_ciq_enabled():
        raise Http404("Classroom Innovation Quest is not enabled")

    quest = get_object_or_404(Quest, slug=slug, is_active=True)

    # Get participant
    try:
        participant = Participant.objects.get(user=request.user, quest=quest)
    except Participant.DoesNotExist:
        messages.warning(request, 'Please join the quest first.')
        return redirect('quest_ciq:quest_join', slug=slug)

    # Get session
    session = participant.sessions.filter(quest=quest).order_by('-started_at').first()
    if not session:
        messages.warning(request, 'No session found.')
        return redirect('quest_ciq:quest_home', slug=slug)

    # Get all responses
    responses = session.responses.select_related('level').order_by('level__order')

    # Organize responses by level
    level_data = []
    for level in quest.levels.all().order_by('order'):
        response = responses.filter(level=level).first()
        level_data.append({
            'level': level,
            'response': response,
            'answers': response.answers if response else {},
            'score': response.score if response else 0,
        })

    context = {
        'quest': quest,
        'session': session,
        'level_data': level_data,
        'total_score': session.total_score,
    }

    return render(request, 'quest_ciq/summary.html', context)


@login_required
def quest_leaderboard(request, slug):
    """Leaderboard page for the quest."""
    if not check_ciq_enabled():
        raise Http404("Classroom Innovation Quest is not enabled")

    quest = get_object_or_404(Quest, slug=slug, is_active=True)

    # Get leaderboard entries
    leaderboard = Leaderboard.objects.filter(
        quest=quest
    ).select_related('participant__user').order_by('rank')

    # Get current user's rank if participating
    user_rank = None
    try:
        participant = Participant.objects.get(user=request.user, quest=quest)
        user_entry = leaderboard.filter(participant=participant).first()
        if user_entry:
            user_rank = user_entry.rank
    except Participant.DoesNotExist:
        pass

    context = {
        'quest': quest,
        'leaderboard': leaderboard,
        'user_rank': user_rank,
    }

    return render(request, 'quest_ciq/leaderboard.html', context)


@login_required
def teacher_dashboard(request, slug):
    """Teacher dashboard to view all participants and their progress."""
    if not check_ciq_enabled():
        raise Http404("Classroom Innovation Quest is not enabled")

    # Only allow staff users
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to view this page.')
        return redirect('quest_ciq:quest_home', slug=slug)

    quest = get_object_or_404(Quest, slug=slug, is_active=True)

    # Get all participants with their latest session
    participants_data = []
    for participant in quest.participants.filter(is_active=True).select_related('user'):
        session = participant.sessions.filter(quest=quest).order_by('-started_at').first()
        if session:
            highest_level = session.get_highest_completed_level()
            participants_data.append({
                'participant': participant,
                'session': session,
                'highest_level': highest_level,
                'progress_percent': (highest_level / 5) * 100,
            })

    # Sort by progress
    participants_data.sort(key=lambda x: x['highest_level'], reverse=True)

    context = {
        'quest': quest,
        'participants_data': participants_data,
    }

    return render(request, 'quest_ciq/teacher_dash.html', context)


@login_required
def facilitate(request, slug):
    """Facilitate page showing prototypes from all participants."""
    if not check_ciq_enabled():
        raise Http404("Classroom Innovation Quest is not enabled")

    # Only allow staff users
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to view this page.')
        return redirect('quest_ciq:quest_home', slug=slug)

    quest = get_object_or_404(Quest, slug=slug, is_active=True)

    # Get level 4 (Prototype) responses
    prototype_level = quest.levels.filter(order=4).first()
    prototypes = []

    if prototype_level:
        responses = LevelResponse.objects.filter(
            level=prototype_level
        ).select_related('session__participant__user')

        for response in responses:
            prototypes.append({
                'user': response.session.participant.user,
                'answers': response.answers,
                'upload': response.prototype_upload,
                'score': response.score,
            })

    context = {
        'quest': quest,
        'prototypes': prototypes,
    }

    return render(request, 'quest_ciq/facilitate.html', context)
