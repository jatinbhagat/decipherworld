"""
Scoring logic for Classroom Innovation Quest levels.
"""
import re


def calculate_level_score(level_response):
    """
    Calculate score for a level response based on level-specific rules.

    Base rule: +10 points on any level submit.

    Bonuses:
    - L3 (Ideate): +10 if ideas_list >= 120 chars or >= 2 items (split by newline/comma/semicolon)
    - L4 (Prototype): +10 if prototype_link provided or prototype_upload saved
    - L5 (Test): +10 if peer_rating >= 4

    Args:
        level_response: LevelResponse instance

    Returns:
        int: Calculated score
    """
    base_score = 10
    bonus = 0

    level_order = level_response.level.order
    answers = level_response.answers or {}

    if level_order == 3:
        # L3 (Ideate) bonus
        bonus += calculate_ideate_bonus(answers)

    elif level_order == 4:
        # L4 (Prototype) bonus
        bonus += calculate_prototype_bonus(answers, level_response)

    elif level_order == 5:
        # L5 (Test) bonus
        bonus += calculate_test_bonus(answers)

    return base_score + bonus


def calculate_ideate_bonus(answers):
    """
    Calculate bonus for Ideate level (L3).
    +10 if ideas_list >= 120 chars OR >= 2 items when split.
    """
    ideas_list = answers.get('ideas_list', '')

    if not ideas_list:
        return 0

    # Check character count
    if len(ideas_list) >= 120:
        return 10

    # Check number of items (split by newline, comma, or semicolon)
    items = re.split(r'[\n,;]+', ideas_list.strip())
    items = [item.strip() for item in items if item.strip()]

    if len(items) >= 2:
        return 10

    return 0


def calculate_prototype_bonus(answers, level_response):
    """
    Calculate bonus for Prototype level (L4).
    +10 if prototype_link provided or prototype_upload exists.
    """
    prototype_link = answers.get('prototype_link', '')

    # Check if link is provided
    if prototype_link and prototype_link.strip():
        return 10

    # Check if file upload exists
    if level_response.prototype_upload:
        return 10

    return 0


def calculate_test_bonus(answers):
    """
    Calculate bonus for Test level (L5).
    +10 if peer_rating >= 4.
    """
    try:
        peer_rating = int(answers.get('peer_rating', 0))
        if peer_rating >= 4:
            return 10
    except (ValueError, TypeError):
        pass

    return 0


def score_and_update_session(level_response):
    """
    Calculate score for a level response and update the session total.
    Also refreshes the leaderboard for the quest.

    Args:
        level_response: LevelResponse instance
    """
    # Calculate and save score
    level_response.calculate_score()
    level_response.save(update_fields=['score'])

    # Update session total score
    session = level_response.session
    session.update_total_score()

    # Refresh leaderboard
    from quest_ciq.models import Leaderboard
    Leaderboard.refresh_for_quest(session.quest)
