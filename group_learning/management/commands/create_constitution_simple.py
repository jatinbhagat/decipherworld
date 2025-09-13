from django.core.management.base import BaseCommand
from group_learning.models import Game, ConstitutionQuestion, ConstitutionOption, GameSession


class Command(BaseCommand):
    help = 'Create simple Constitution Challenge game for production'

    def handle(self, *args, **options):
        self.stdout.write('🏛️ Creating Constitution Challenge game...')
        
        # Create the game with minimal fields to avoid field errors
        game, created = Game.objects.get_or_create(
            title='Build Your Country: The Constitution Challenge',
            defaults={
                'subtitle': 'Learn governance by building your virtual country',
                'game_type': 'constitution_challenge',
                'description': 'A team-based educational game where students learn about constitutional principles, governance, and democracy by making decisions that build and evolve their virtual country.',
                'context': 'Students work in teams to answer multiple-choice questions about governance, leadership, citizen rights, and constitutional principles.',
                'min_players': 1,
                'max_players': 50,
                'estimated_duration': 45,
                'target_age_min': 12,
                'target_age_max': 18,
                'difficulty_level': 2,
                'introduction_text': 'Welcome to Build Your Country! You and your team will make important decisions about governance, leadership, and citizen rights.',
                'is_active': True
            }
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f'✅ Created game: {game.title}'))
        else:
            self.stdout.write(f'📋 Using existing game: {game.title}')

        # Create a few basic questions
        basic_questions = [
            {
                'order': 1,
                'category': 'leadership',
                'question_text': 'How should leaders be chosen in your country?',
                'scenario_context': 'Your country needs a system for selecting leaders.',
                'learning_module_title': 'Democratic Leadership',
                'learning_module_content': 'Democracy means rule by the people through elections.',
                'options': [
                    {
                        'letter': 'A',
                        'text': 'Through free and fair elections',
                        'score': 3,
                        'feedback': 'Elections make leaders accountable to the people.',
                        'principle': 'Democracy',
                        'color': 'green'
                    },
                    {
                        'letter': 'B',
                        'text': 'Leaders choose their successors',
                        'score': -2,
                        'feedback': 'This denies choice to citizens.',
                        'principle': 'Hereditary Rule',
                        'color': 'red'
                    }
                ]
            },
            {
                'order': 2,
                'category': 'rights',
                'question_text': 'What rights should all citizens have?',
                'scenario_context': 'Rights protect people\'s freedoms and dignity.',
                'learning_module_title': 'Fundamental Rights',
                'learning_module_content': 'Basic human rights include freedom of speech, religion, and assembly.',
                'options': [
                    {
                        'letter': 'A',
                        'text': 'Freedom of speech, religion, and assembly',
                        'score': 5,
                        'feedback': 'These fundamental rights protect democracy.',
                        'principle': 'Human Rights',
                        'color': 'green'
                    },
                    {
                        'letter': 'B',
                        'text': 'Only basic needs like food and shelter',
                        'score': 1,
                        'feedback': 'Basic needs are important, but people need more rights.',
                        'principle': 'Minimal Rights',
                        'color': 'yellow'
                    }
                ]
            }
        ]

        # Create questions and options
        for q_data in basic_questions:
            question, created = ConstitutionQuestion.objects.get_or_create(
                game=game,
                order=q_data['order'],
                defaults={
                    'category': q_data['category'],
                    'question_text': q_data['question_text'],
                    'scenario_context': q_data['scenario_context'],
                    'learning_module_title': q_data['learning_module_title'],
                    'learning_module_content': q_data['learning_module_content'],
                    'time_limit': 90,
                }
            )

            if created:
                self.stdout.write(f'  ✅ Created question {q_data["order"]}: {q_data["question_text"][:50]}...')
                
                # Create options for this question
                for opt_data in q_data['options']:
                    ConstitutionOption.objects.create(
                        question=question,
                        option_letter=opt_data['letter'],
                        option_text=opt_data['text'],
                        score_value=opt_data['score'],
                        feedback_message=opt_data['feedback'],
                        governance_principle=opt_data['principle'],
                        color_class=opt_data['color'],
                    )
            else:
                self.stdout.write(f'  📋 Question {q_data["order"]} already exists')

        # Create demo session
        session, created = GameSession.objects.get_or_create(
            game=game,
            session_code='DEMO01',
            defaults={
                'status': 'waiting',
                'allow_spectators': True,
                'auto_assign_roles': False,
            }
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f'✅ Created demo session: {session.session_code}'))
        else:
            self.stdout.write(f'📋 Demo session already exists: {session.session_code}')

        # Final summary
        question_count = ConstitutionQuestion.objects.filter(game=game).count()
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('🎉 Constitution Challenge setup complete!'))
        self.stdout.write(f'  • Game: {game.title}')
        self.stdout.write(f'  • Questions: {question_count}')
        self.stdout.write(f'  • Demo Session: {session.session_code}')
        self.stdout.write(f'  • Game is active: {game.is_active}')