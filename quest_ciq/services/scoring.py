"""
Scoring service for Classroom Innovation Quest
Handles student scoring, teacher scoring, and weighted totals
"""


def calculate_student_score(session):
    """
    Calculate student score based on level responses
    Returns the sum of base scores + bonuses
    """
    from quest_ciq.models import LevelResponse
    from quest_ciq.constants import SCORING

    score = 0
    responses = session.responses.all()

    for response in responses:
        # Base score per level
        score += SCORING['base_per_level']

        answers = response.get_answers()

        # Level-specific bonuses
        if response.level_order == 3:  # Ideate
            ideas = answers.get('ideas', [])
            non_empty_ideas = [i for i in ideas if i.strip()]
            total_chars = sum(len(i) for i in non_empty_ideas)

            if len(non_empty_ideas) >= 2:
                score += SCORING['l3_bonus_ideas']
            if total_chars >= 120:
                score += SCORING['l3_bonus_chars']

        elif response.level_order == 4:  # Prototype
            if answers.get('prototype_link') or answers.get('prototype_upload'):
                score += SCORING['l4_bonus_upload']

        # Note: Level 5 bonus removed since it's now presentation-only

    return score


def get_teacher_score(team, classroom, quest):
    """
    Get teacher score for a specific team/classroom/quest combination
    Returns score or None if not graded yet
    """
    from quest_ciq.models import TeacherTeamScore

    try:
        teacher_score_obj = TeacherTeamScore.objects.get(
            team=team,
            classroom=classroom,
            quest=quest
        )
        return teacher_score_obj.score
    except TeacherTeamScore.DoesNotExist:
        return None


def calculate_weighted_score(student_score, teacher_score):
    """
    Calculate weighted final score
    Formula: 0.4 * student_score + 0.6 * teacher_score

    Args:
        student_score: int, score from student's level responses
        teacher_score: int or None, teacher's grading score (0-100)

    Returns:
        int: weighted score, or student_score if no teacher score
    """
    if teacher_score is None:
        # No teacher score yet, return student score only
        return student_score

    # Apply weighting: 40% student + 60% teacher
    weighted = round(student_score * 0.4 + teacher_score * 0.6)
    return weighted


def get_final_score(session):
    """
    Get final score for a session, considering both student and teacher scores

    Returns:
        dict: {
            'student_score': int,
            'teacher_score': int or None,
            'final_score': int,
            'awaiting_teacher': bool
        }
    """
    student_score = calculate_student_score(session)

    # Check if session has team/classroom association
    if not session.team or not session.classroom:
        # No team association, return student score only
        return {
            'student_score': student_score,
            'teacher_score': None,
            'final_score': student_score,
            'awaiting_teacher': False
        }

    # Get quest from classroom
    quest = session.classroom.quest
    teacher_score = get_teacher_score(session.team, session.classroom, quest)

    final_score = calculate_weighted_score(student_score, teacher_score)

    return {
        'student_score': student_score,
        'teacher_score': teacher_score,
        'final_score': final_score,
        'awaiting_teacher': teacher_score is None
    }


def get_team_aggregated_responses(team, classroom):
    """
    Aggregate team responses from all team members
    Returns the latest completed response for each level

    Args:
        team: Team instance
        classroom: ClassRoom instance

    Returns:
        dict: {level_order: LevelResponse} for levels 1-5
    """
    from quest_ciq.models import LevelResponse

    aggregated = {}

    # Get all sessions for this team in this classroom
    sessions = team.sessions.filter(classroom=classroom)

    for level_order in range(1, 6):
        # Get the latest response for this level across all team members
        latest_response = LevelResponse.objects.filter(
            session__in=sessions,
            level_order=level_order
        ).order_by('-submitted_at').first()

        if latest_response:
            aggregated[level_order] = latest_response

    return aggregated


def get_team_scores(team, classroom):
    """
    Get aggregated scores for a team

    Returns:
        dict: {
            'avg_student_score': float,
            'teacher_score': int or None,
            'avg_final_score': float,
            'members_count': int,
            'awaiting_teacher': bool
        }
    """
    sessions = team.sessions.filter(classroom=classroom)

    if not sessions.exists():
        return {
            'avg_student_score': 0,
            'teacher_score': None,
            'avg_final_score': 0,
            'members_count': 0,
            'awaiting_teacher': True
        }

    # Calculate student scores for all members
    student_scores = [calculate_student_score(session) for session in sessions]
    avg_student_score = sum(student_scores) / len(student_scores) if student_scores else 0

    # Get teacher score
    quest = classroom.quest
    teacher_score = get_teacher_score(team, classroom, quest)

    # Calculate final scores for all members
    final_scores = []
    for session in sessions:
        score_data = get_final_score(session)
        final_scores.append(score_data['final_score'])

    avg_final_score = sum(final_scores) / len(final_scores) if final_scores else 0

    return {
        'avg_student_score': round(avg_student_score, 1),
        'teacher_score': teacher_score,
        'avg_final_score': round(avg_final_score, 1),
        'members_count': sessions.count(),
        'awaiting_teacher': teacher_score is None
    }
