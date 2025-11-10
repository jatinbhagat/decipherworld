"""
Scoring service for Quest CIQ
Handles score calculation and leaderboard updates
"""
from django.db import transaction
from django.utils import timezone


def calculate_level_score(response_text, level):
    """
    Calculate score for a level response.

    This is a placeholder implementation that calculates score based on:
    - Response length (basic heuristic)
    - Time taken (if applicable)

    In a real implementation, this could use:
    - NLP/AI analysis
    - Keyword matching
    - Rubric-based scoring
    - Manual teacher review

    Args:
        response_text (str): The participant's response
        level (QuestLevel): The level being scored

    Returns:
        int: Score (0 to level.max_score)
    """
    if not response_text or not response_text.strip():
        return 0

    # Basic scoring algorithm - can be replaced with sophisticated logic
    response_length = len(response_text.strip())

    # Score based on response length (simple heuristic)
    if response_length < 50:
        score_percentage = 0.3  # 30% for very short responses
    elif response_length < 150:
        score_percentage = 0.5  # 50% for short responses
    elif response_length < 300:
        score_percentage = 0.7  # 70% for medium responses
    elif response_length < 500:
        score_percentage = 0.85  # 85% for good responses
    else:
        score_percentage = 1.0  # 100% for detailed responses

    # Calculate final score
    score = int(level.max_score * score_percentage)

    return max(0, min(score, level.max_score))


def calculate_creativity_score(response_text):
    """
    Calculate creativity score component.

    Placeholder for future AI-based creativity analysis.
    Could analyze:
    - Uniqueness of ideas
    - Diversity of approaches
    - Novel connections

    Args:
        response_text (str): The participant's response

    Returns:
        float: Creativity score (0.0 to 1.0)
    """
    # Placeholder implementation
    # TODO: Implement actual creativity analysis
    return 0.5


def calculate_intelligence_quotient(session):
    """
    Calculate the overall Curiosity Intelligence Quotient for a session.

    Args:
        session (QuestSession): The quest session

    Returns:
        dict: CIQ breakdown with components
    """
    responses = session.level_responses.select_related('level').all()

    if not responses:
        return {
            'total_score': 0,
            'average_score': 0,
            'completion_rate': 0,
            'ciq_rating': 'Not Started'
        }

    total_possible = sum(r.level.max_score for r in responses)
    total_earned = sum(r.score for r in responses)

    completion_rate = (len(responses) / session.quest.levels.count()) * 100 if session.quest.levels.count() > 0 else 0
    average_score = (total_earned / total_possible * 100) if total_possible > 0 else 0

    # CIQ Rating based on average score
    if average_score >= 90:
        ciq_rating = 'Exceptional'
    elif average_score >= 75:
        ciq_rating = 'Advanced'
    elif average_score >= 60:
        ciq_rating = 'Proficient'
    elif average_score >= 45:
        ciq_rating = 'Developing'
    else:
        ciq_rating = 'Emerging'

    return {
        'total_score': total_earned,
        'total_possible': total_possible,
        'average_score': round(average_score, 2),
        'completion_rate': round(completion_rate, 2),
        'ciq_rating': ciq_rating
    }


@transaction.atomic
def update_leaderboard(session):
    """
    Update leaderboard entry for a completed session.

    Args:
        session (QuestSession): The completed quest session

    Returns:
        Leaderboard: Updated or created leaderboard entry
    """
    from quest_ciq.models import Leaderboard

    # Calculate completion time
    completion_time_seconds = None
    if session.started_at and session.completed_at:
        completion_time_seconds = int((session.completed_at - session.started_at).total_seconds())

    # Update or create leaderboard entry
    leaderboard_entry, created = Leaderboard.objects.update_or_create(
        quest=session.quest,
        participant=session.participant,
        defaults={
            'total_score': session.total_score,
            'completion_time_seconds': completion_time_seconds,
        }
    )

    # Recalculate ranks for this quest
    recalculate_ranks(session.quest)

    return leaderboard_entry


@transaction.atomic
def recalculate_ranks(quest):
    """
    Recalculate all ranks for a quest's leaderboard.
    Ranks are based on:
    1. Higher score (primary)
    2. Faster completion time (tiebreaker)

    Args:
        quest (Quest): The quest to recalculate ranks for
    """
    from quest_ciq.models import Leaderboard

    # Get all entries ordered by score (desc) and time (asc)
    entries = Leaderboard.objects.filter(quest=quest).order_by(
        '-total_score',
        'completion_time_seconds'
    )

    # Update ranks
    for rank, entry in enumerate(entries, start=1):
        if entry.rank != rank:
            entry.rank = rank
            entry.save(update_fields=['rank', 'updated_at'])


def generate_feedback(response_text, level, score):
    """
    Generate automated feedback for a response.

    Placeholder for AI-generated feedback.

    Args:
        response_text (str): The participant's response
        level (QuestLevel): The level
        score (int): The score earned

    Returns:
        str: Feedback message
    """
    score_percentage = (score / level.max_score * 100) if level.max_score > 0 else 0

    if score_percentage >= 90:
        feedback = "Excellent work! Your response demonstrates deep understanding and creativity."
    elif score_percentage >= 75:
        feedback = "Great job! Your response shows strong comprehension and good effort."
    elif score_percentage >= 60:
        feedback = "Good effort! Consider adding more detail and examples to strengthen your response."
    elif score_percentage >= 45:
        feedback = "You're on the right track. Try to elaborate more on your ideas and provide specific examples."
    else:
        feedback = "Keep trying! Make sure to address the question fully and provide detailed explanations."

    return feedback
