"""
Management command to seed the Classroom Innovation Quest.
"""
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from quest_ciq.models import Quest, QuestLevel


class Command(BaseCommand):
    help = 'Seeds the Classroom Innovation Quest with 5 levels (Empathy → Define → Ideate → Prototype → Test)'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('Starting Classroom Innovation Quest seeding...'))

        # Create or update the Quest (idempotently)
        quest, created = Quest.objects.get_or_create(
            slug='classroom-innovation-quest',
            defaults={
                'title': 'Classroom Innovation Quest',
                'description': 'A 5-step design-thinking mini-game for Grade 9: Empathy → Define → Ideate → Prototype → Test.',
                'is_active': True,
            }
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f'✓ Created quest: "{quest.title}"'))
        else:
            # Update existing quest
            quest.title = 'Classroom Innovation Quest'
            quest.description = 'A 5-step design-thinking mini-game for Grade 9: Empathy → Define → Ideate → Prototype → Test.'
            quest.is_active = True
            quest.save()
            self.stdout.write(self.style.SUCCESS(f'✓ Updated quest: "{quest.title}"'))

        # Define the 5 levels with their metadata
        levels_data = [
            {
                'order': 1,
                'name': 'Empathy',
                'short_help': 'Spot a real classroom/user problem.',
                'schema': {
                    'fields': ['observed_problem', 'who_is_affected', 'why_important'],
                    'description': 'Observe and identify a real problem in your classroom or among users.'
                }
            },
            {
                'order': 2,
                'name': 'Define',
                'short_help': 'Frame the problem clearly.',
                'schema': {
                    'fields': ['problem_statement', 'root_causes'],
                    'description': 'Define the problem statement and identify root causes.'
                }
            },
            {
                'order': 3,
                'name': 'Ideate',
                'short_help': 'Generate creative solutions.',
                'schema': {
                    'fields': ['ideas_list', 'wildcard_idea'],
                    'description': 'Brainstorm multiple creative solutions to the problem.'
                }
            },
            {
                'order': 4,
                'name': 'Prototype',
                'short_help': 'Create a quick mock/sketch/link.',
                'schema': {
                    'fields': ['prototype_link', 'materials', 'one_line_benefit', 'prototype_upload'],
                    'description': 'Build a simple prototype or mockup of your solution.'
                }
            },
            {
                'order': 5,
                'name': 'Test',
                'short_help': 'Get peer rating and comments.',
                'schema': {
                    'fields': ['peer_name', 'peer_rating', 'peer_comment'],
                    'description': 'Test your prototype with peers and gather feedback.'
                }
            },
        ]

        # Create or update levels (idempotently)
        for level_data in levels_data:
            level, created = QuestLevel.objects.get_or_create(
                quest=quest,
                order=level_data['order'],
                defaults={
                    'name': level_data['name'],
                    'short_help': level_data['short_help'],
                    'schema': level_data['schema'],
                }
            )

            if created:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'  ✓ Created Level {level.order}: {level.name} - "{level.short_help}"'
                    )
                )
            else:
                # Update existing level
                level.name = level_data['name']
                level.short_help = level_data['short_help']
                level.schema = level_data['schema']
                level.save()
                self.stdout.write(
                    self.style.SUCCESS(
                        f'  ✓ Updated Level {level.order}: {level.name} - "{level.short_help}"'
                    )
                )

        # Print join instructions
        self.stdout.write('')
        self.stdout.write(self.style.NOTICE('═' * 80))
        self.stdout.write(self.style.NOTICE('CLASSROOM INNOVATION QUEST - READY TO PLAY!'))
        self.stdout.write(self.style.NOTICE('═' * 80))
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('Quest Setup Complete!'))
        self.stdout.write('')
        self.stdout.write('The quest has been seeded with 5 levels:')
        self.stdout.write('  1. Empathy   - Spot a real classroom/user problem')
        self.stdout.write('  2. Define    - Frame the problem clearly')
        self.stdout.write('  3. Ideate    - Generate creative solutions')
        self.stdout.write('  4. Prototype - Create a quick mock/sketch/link')
        self.stdout.write('  5. Test      - Get peer rating and comments')
        self.stdout.write('')
        self.stdout.write(self.style.WARNING('Quest URLs:'))
        self.stdout.write(f'  • Quest Home:  /ciq/quest/classroom-innovation-quest/')
        self.stdout.write(f'  • Join Quest:  /ciq/quest/classroom-innovation-quest/join/')
        self.stdout.write(f'  • Level 1:     /ciq/quest/classroom-innovation-quest/level/1/')
        self.stdout.write(f'  • Summary:     /ciq/quest/classroom-innovation-quest/summary/')
        self.stdout.write(f'  • Leaderboard: /ciq/quest/classroom-innovation-quest/leaderboard/')
        self.stdout.write('')
        self.stdout.write(self.style.WARNING('Next Steps:'))
        self.stdout.write('  1. Make sure ENABLE_CIQ = True in your settings')
        self.stdout.write('  2. Run migrations: python manage.py migrate')
        self.stdout.write('  3. Start the server and visit the quest URLs above')
        self.stdout.write('')
        self.stdout.write(self.style.NOTICE('═' * 80))
