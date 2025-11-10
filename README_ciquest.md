# Classroom Innovation Quest (CIQ)

A 5-step design-thinking mini-game for Grade 9 students following the Design Thinking process: **Empathy → Define → Ideate → Prototype → Test**.

## Overview

The Classroom Innovation Quest guides students through the design thinking process to solve real classroom problems. Students progress through 5 levels, earning points for their submissions and bonus points for quality work.

## The 5 Levels

| Level | Name | Description | Key Activities |
|-------|------|-------------|----------------|
| 1 | **Empathy** | Spot a real classroom/user problem | Observe problems, identify affected users, explain importance |
| 2 | **Define** | Frame the problem clearly | Write problem statement, identify root causes |
| 3 | **Ideate** | Generate creative solutions | Brainstorm multiple ideas, think creatively |
| 4 | **Prototype** | Create a quick mock/sketch/link | Build prototype, describe materials and benefits |
| 5 | **Test** | Get peer rating and comments | Test with peers, collect feedback and ratings |

## Scoring System

### Base Score
Every level submission earns **+10 points** automatically.

### Bonus Points

| Level | Bonus Criteria | Bonus Points |
|-------|----------------|--------------|
| **Level 3: Ideate** | Ideas list ≥ 120 characters OR ≥ 2 distinct ideas | +10 |
| **Level 4: Prototype** | Prototype link provided OR image uploaded | +10 |
| **Level 5: Test** | Peer rating ≥ 4 (out of 5) | +10 |

### Maximum Scores
- **Without bonuses:** 50 points (10 per level × 5 levels)
- **With all bonuses:** 80 points (50 base + 30 bonus)

## Installation & Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Add to Settings
The quest_ciq app is already added to `INSTALLED_APPS` in `settings/base.py`:
```python
INSTALLED_APPS = [
    # ... other apps
    'quest_ciq',  # Classroom Innovation Quest
]
```

Feature flag (already set):
```python
ENABLE_CIQ = config('ENABLE_CIQ', default=True, cast=bool)
```

### 3. Run Migrations
```bash
python manage.py makemigrations quest_ciq
python manage.py migrate
```

### 4. Seed the Quest
```bash
python manage.py seed_ciq
```

This command will:
- Create the "Classroom Innovation Quest"
- Create all 5 levels (Empathy, Define, Ideate, Prototype, Test)
- Display quest URLs and instructions

## Quest URLs

### Student URLs
- **Quest Home:** `/ciq/quest/classroom-innovation-quest/`
- **Join Quest:** `/ciq/quest/classroom-innovation-quest/join/`
- **Level Pages:** `/ciq/quest/classroom-innovation-quest/level/<1-5>/`
- **Summary:** `/ciq/quest/classroom-innovation-quest/summary/`
- **Leaderboard:** `/ciq/quest/classroom-innovation-quest/leaderboard/`

### Teacher URLs (Staff Only)
- **Teacher Dashboard:** `/ciq/quest/classroom-innovation-quest/teacher/`
- **Facilitate (Prototypes):** `/ciq/quest/classroom-innovation-quest/facilitate/`

## Features

### For Students
- ✅ **Progressive Levels:** Must complete levels in order (gating logic)
- ✅ **Real-time Scoring:** Instant feedback on points earned
- ✅ **Leaderboard:** See rankings and compete with classmates
- ✅ **Summary View:** Review all submitted work in one place
- ✅ **Image Uploads:** Upload prototype images (Level 4)
- ✅ **Mobile Responsive:** Works on all devices with Tailwind CSS

### For Teachers
- ✅ **Dashboard:** Monitor all student progress
- ✅ **Prototype Showcase:** View all student prototypes in one place
- ✅ **Leaderboard Access:** See complete rankings
- ✅ **Session Freezing:** Ability to freeze sessions (prevent changes)

## Gating Logic

Students must complete levels sequentially:
- **Level 1 (Empathy)** is always accessible
- **Level 2 (Define)** unlocks after completing Level 1
- **Level 3 (Ideate)** unlocks after completing Level 2
- **Level 4 (Prototype)** unlocks after completing Level 3
- **Level 5 (Test)** unlocks after completing Level 4

Students cannot skip levels or access future levels without completing previous ones.

## Media Uploads

### Configuration
Media files are configured in `settings/base.py`:
```python
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
```

### File Requirements (Level 4: Prototype)
- **File types:** JPG, JPEG, PNG only
- **Max size:** 2MB
- **Optional:** Students can provide a link instead of uploading

### Production Considerations
For production deployments, configure Azure Blob Storage or AWS S3 for media file storage.

## Testing

Run the comprehensive test suite:
```bash
python manage.py test quest_ciq
```

### Test Coverage
- ✅ Model creation and relationships
- ✅ Seed command (idempotency)
- ✅ Gating logic (level access control)
- ✅ Scoring logic (base + bonuses)
- ✅ Leaderboard sorting
- ✅ Feature flag (ENABLE_CIQ)
- ✅ View authentication and permissions

## Development Workflow

### 1. Local Development
```bash
# Start the dev server
python manage.py runserver

# Visit the quest
# http://localhost:8000/ciq/quest/classroom-innovation-quest/join/
```

### 2. Creating Test Data
```bash
# Create superuser
python manage.py createsuperuser

# Create test users
python manage.py shell
>>> from django.contrib.auth.models import User
>>> User.objects.create_user('student1', password='pass123')
>>> User.objects.create_user('student2', password='pass123')
```

### 3. Resetting Quest Data
```bash
# Clear all quest data
python manage.py shell
>>> from quest_ciq.models import Quest
>>> Quest.objects.all().delete()

# Re-seed
python manage.py seed_ciq
```

## Architecture

### Models
- **Quest:** Top-level quest container
- **QuestLevel:** Individual levels (1-5)
- **Participant:** Links users to quests
- **QuestSession:** User's journey through a quest
- **LevelResponse:** Submission for each level
- **Leaderboard:** Cached ranking data

### Forms
Each level has its own form class:
- `EmpathyLevelForm` (Level 1)
- `DefineLevelForm` (Level 2)
- `IdeateLevelForm` (Level 3)
- `PrototypeLevelForm` (Level 4)
- `TestLevelForm` (Level 5)

### Scoring Service
Located in `quest_ciq/services/scoring.py`:
- `calculate_level_score()` - Main scoring function
- `calculate_ideate_bonus()` - Level 3 bonus
- `calculate_prototype_bonus()` - Level 4 bonus
- `calculate_test_bonus()` - Level 5 bonus
- `score_and_update_session()` - Updates session and leaderboard

## Troubleshooting

### Quest URLs return 404
**Solution:** Check that `ENABLE_CIQ = True` in your settings or environment variables.

### Images not displaying
**Solution:**
1. Check `MEDIA_URL` and `MEDIA_ROOT` in settings
2. Ensure media URLs are configured in `urls.py` (already done for DEBUG mode)
3. For production, configure cloud storage

### Migrations fail
**Solution:**
```bash
# Clear migrations
rm quest_ciq/migrations/0*.py

# Recreate
python manage.py makemigrations quest_ciq
python manage.py migrate
```

### Leaderboard not updating
**Solution:** Leaderboard refreshes automatically when scores are saved. To manually refresh:
```python
from quest_ciq.models import Leaderboard, Quest
quest = Quest.objects.get(slug='classroom-innovation-quest')
Leaderboard.refresh_for_quest(quest)
```

## Future Enhancements

Potential additions for v2:
- 🔜 Multiple quests support
- 🔜 Team-based quests
- 🔜 Peer review system
- 🔜 Analytics dashboard
- 🔜 Export results to CSV
- 🔜 Quest templates
- 🔜 Badges and achievements
- 🔜 Time-limited quests

## Support

For issues or questions:
1. Check this documentation
2. Review test cases in `quest_ciq/tests.py`
3. Examine the seed command output: `python manage.py seed_ciq`

## License

Part of the Decipherworld project. See main README for license information.
