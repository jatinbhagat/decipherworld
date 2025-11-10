"""
Constants for Classroom Innovation Quest
"""

# Preset pain points for Level 1 (Empathy)
CLASSROOM_PAIN_POINTS = [
    "Classroom noise",
    "Students forgetting materials",
    "Not enough time to finish tasks",
    "Hydration / water reminders",
    "Messy desks",
    "Can't see the board clearly",
    "Slow internet",
    "Bullying or loneliness",
    "Heavy backpacks",
    "Not understanding instructions",
    "Staying focused in class",
    "Homework confusion",
    "Classroom safety",
    "Uncomfortable seating",
    "Lost stationery",
    "Forgetting timetable/schedule",
    "Hard to ask questions",
    "Break rush / long queues",
]

# Who is affected choices
WHO_AFFECTED_CHOICES = [
    ('students', 'Students'),
    ('teacher', 'Teacher'),
    ('both', 'Both'),
]

# Level configuration
LEVEL_CONFIG = {
    1: {
        'name': 'Empathy',
        'emoji': '👀',
        'tooltip': 'Empathy = observe needs before solving',
        'success_message': '👏 Great observation! You unlocked Define.',
    },
    2: {
        'name': 'Define',
        'emoji': '🎯',
        'tooltip': 'Define the problem clearly before jumping to solutions',
        'success_message': '🎯 Perfect! Problem defined. Now let\'s brainstorm!',
    },
    3: {
        'name': 'Ideate',
        'emoji': '💡',
        'tooltip': 'Quantity first, quality later! Generate many ideas',
        'success_message': '💡 Amazing ideas! Time to build a prototype!',
    },
    4: {
        'name': 'Prototype',
        'emoji': '🛠️',
        'tooltip': 'Build something simple to test your idea',
        'success_message': '🛠️ Prototype ready! Let\'s get feedback!',
    },
    5: {
        'name': 'Test',
        'emoji': '🧪',
        'tooltip': 'Get feedback to improve your solution',
        'success_message': '🎉 Quest complete! Check the leaderboard!',
    },
}

# Scoring configuration
SCORING = {
    'base_per_level': 10,
    'l3_bonus_ideas': 10,  # Bonus if ≥2 ideas
    'l3_bonus_chars': 10,  # Bonus if ≥120 chars total
    'l4_bonus_upload': 10,  # Bonus if link or upload present
    'l5_bonus_rating': 10,  # Bonus if rating ≥4
}

# Emoji rating mapping for Level 5
EMOJI_RATINGS = [
    (1, '😟', 'Needs work'),
    (2, '🙁', 'Could be better'),
    (3, '😐', 'It\'s okay'),
    (4, '🙂', 'Good idea!'),
    (5, '🤩', 'Amazing!'),
]
