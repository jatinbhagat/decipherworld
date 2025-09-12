from django.core.management.base import BaseCommand
from group_learning.models import (
    Game, ConstitutionQuestion, ConstitutionOption, GameSession,
    LearningModule, LearningObjective
)


class Command(BaseCommand):
    help = 'Create sample Constitution Challenge game with questions'

    def add_arguments(self, parser):
        parser.add_argument('--reset', action='store_true', help='Reset existing data')

    def handle(self, *args, **options):
        if options['reset']:
            self.stdout.write('🗑️  Clearing existing Constitution Challenge data...')
            Game.objects.filter(game_type='constitution_challenge').delete()
            self.stdout.write(self.style.WARNING('Existing data cleared.'))

        # Create learning module
        learning_module, created = LearningModule.objects.get_or_create(
            name='Constitutional Foundations',
            defaults={
                'module_type': 'civics',
                'description': 'Basic principles of constitutional governance and democracy',
                'grade_level': '6-12',
            }
        )

        # Create learning objectives
        objectives = [
            {
                'title': 'Understand democratic principles',
                'objective_type': 'knowledge',
                'description': 'Students will understand the basic principles of democratic governance',
            },
            {
                'title': 'Analyze governance structures',
                'objective_type': 'critical_thinking',
                'description': 'Students will analyze different approaches to organizing government',
            },
            {
                'title': 'Evaluate constitutional choices',
                'objective_type': 'skills',
                'description': 'Students will evaluate the consequences of different constitutional decisions',
            }
        ]

        created_objectives = []
        for obj_data in objectives:
            obj, created = LearningObjective.objects.get_or_create(
                title=obj_data['title'],
                defaults=obj_data
            )
            if created:
                obj.learning_modules.add(learning_module)
            created_objectives.append(obj)

        # Create the Constitution Challenge game
        game, created = Game.objects.get_or_create(
            title='Build Your Country: The Constitution Challenge',
            defaults={
                'subtitle': 'Learn governance by building your virtual country',
                'game_type': 'constitution_challenge',
                'description': 'A team-based educational game where students learn about constitutional principles, governance, and democracy by making decisions that build and evolve their virtual country.',
                'context': 'Students work in teams to answer multiple-choice questions about governance, leadership, citizen rights, and constitutional principles. Each answer affects their country\'s development and governance score.',
                'min_players': 1,
                'max_players': 50,
                'estimated_duration': 45,
                'target_age_min': 12,
                'target_age_max': 18,
                'difficulty_level': 2,
                'introduction_text': 'Welcome to Build Your Country! You and your team will make important decisions about governance, leadership, and citizen rights. Every choice you make will shape your virtual country and determine whether it becomes a thriving democracy or struggles with poor governance. Work together to build the best country possible!',
            }
        )

        if created:
            game.learning_objectives.add(*created_objectives)
            self.stdout.write(self.style.SUCCESS(f'✅ Created game: {game.title}'))
        else:
            self.stdout.write(f'📋 Using existing game: {game.title}')

        # Updated comprehensive Constitution Challenge questions
        questions_data = [
            {
                'order': 1,
                'category': 'leadership',
                'question_text': 'Imagine your group is starting a new country. Who should have the authority to make the most important rules?',
                'scenario_context': 'Your new country needs a foundation for making crucial decisions. This choice will determine how power is distributed and how important rules are created.',
                'learning_module_title': 'Foundation of Governance',
                'learning_module_content': 'How power is distributed in government affects everyone\'s life. Different systems have different benefits and challenges. A single leader can make quick decisions but risks unfairness. A council promotes discussion and diverse opinions. Involving all citizens ensures everyone has a voice but can be slow for big decisions.\n\nThe key is finding the right balance between efficiency and fairness for your country\'s needs.',
                'options': [
                    {
                        'letter': 'A',
                        'text': 'One wise leader',
                        'score': -2,
                        'feedback': 'One leader can make quick decisions, but risks unfairness or misuse. Too much power in one person.',
                        'principle': 'Autocracy',
                        'color': 'red'
                    },
                    {
                        'letter': 'B',
                        'text': 'A council of chosen people',
                        'score': 2,
                        'feedback': 'A council promotes discussion and diverse opinions, but decisions may take time. Balanced and inclusive approach.',
                        'principle': 'Council Rule',
                        'color': 'green'
                    },
                    {
                        'letter': 'C',
                        'text': 'All citizens together',
                        'score': 1,
                        'feedback': 'All citizens share ideas, but decisions may be slow and confusing for biggest issues. Inclusive, but hard to run everything this way.',
                        'principle': 'Direct Democracy',
                        'color': 'blue'
                    }
                ]
            },
            {
                'order': 2,
                'category': 'leadership',
                'question_text': 'How should leaders be chosen in your country?',
                'scenario_context': 'Your country needs a system for selecting the people who will make important decisions and lead the nation.',
                'learning_module_title': 'Democracy – People\'s Power',
                'learning_module_content': 'Democracy means rule by the people, through regular elections, protecting liberty and fairness. Elections make leaders accountable to the people - they must serve citizens well to stay in power.\n\nIndia is the world\'s largest democracy, showing that diverse countries can successfully use democratic systems to give all citizens a voice in government.',
                'options': [
                    {
                        'letter': 'A',
                        'text': 'By citizens through free, fair elections',
                        'score': 3,
                        'feedback': 'Elections make leaders accountable to the people.',
                        'principle': 'Democracy',
                        'color': 'green'
                    },
                    {
                        'letter': 'B',
                        'text': 'Leaders appoint their children or relatives as rulers',
                        'score': -3,
                        'feedback': 'Hereditary rule denies choice to citizens.',
                        'principle': 'Hereditary Rule',
                        'color': 'red'
                    },
                    {
                        'letter': 'C',
                        'text': 'Military or strongest group picks the leader',
                        'score': -2,
                        'feedback': 'Power through force ignores people\'s will.',
                        'principle': 'Military Rule',
                        'color': 'red'
                    }
                ]
            },
            {
                'order': 3,
                'category': 'rights',
                'question_text': 'What rights should all citizens have in your country?',
                'scenario_context': 'Rights protect people\'s freedoms and dignity. Your country must decide which fundamental rights to guarantee to all citizens.',
                'learning_module_title': 'Fundamental Human Rights',
                'learning_module_content': 'Basic human rights include freedom of speech, religion, and assembly. These rights protect individuals from government oppression and allow people to live with dignity. The right to vote ensures citizens can participate in democracy.\n\nProtecting these rights creates a society where people can express themselves, practice their beliefs, and work together to improve their community.',
                'options': [
                    {
                        'letter': 'A',
                        'text': 'Freedom of speech, religion, assembly, and the right to vote',
                        'score': 5,
                        'feedback': 'Excellent! These fundamental rights protect democracy and human dignity.',
                        'principle': 'Human Rights',
                        'color': 'green'
                    },
                    {
                        'letter': 'B',
                        'text': 'Only basic needs like food and shelter',
                        'score': 1,
                        'feedback': 'Basic needs are important, but people need more rights to thrive.',
                        'principle': 'Minimal Rights',
                        'color': 'yellow'
                    },
                    {
                        'letter': 'C',
                        'text': 'Rights only for citizens who support the government',
                        'score': -2,
                        'feedback': 'Rights should not depend on political opinions - this leads to oppression.',
                        'principle': 'Conditional Rights',
                        'color': 'red'
                    },
                    {
                        'letter': 'D',
                        'text': 'The government decides rights based on what\'s convenient',
                        'score': -3,
                        'feedback': 'Rights must be guaranteed and protected, not subject to government convenience.',
                        'principle': 'Arbitrary Power',
                        'color': 'red'
                    }
                ]
            },
            {
                'order': 4,
                'category': 'justice',
                'question_text': 'How should your country handle disputes and crimes?',
                'scenario_context': 'Every country needs a system to resolve conflicts fairly and deal with people who break the law. This decision affects how safe and fair your society will be.',
                'learning_module_title': 'Independent Judiciary and Rule of Law',
                'learning_module_content': 'An independent court system ensures that justice is fair and unbiased. When judges are independent from political leaders, they can make decisions based on law and evidence, not politics. This protects everyone\'s rights equally.\n\nThe "rule of law" means that everyone, including government leaders, must follow the same laws. This prevents abuse of power and ensures equal treatment.',
                'options': [
                    {
                        'letter': 'A',
                        'text': 'Independent courts with fair trials and equal treatment under law',
                        'score': 5,
                        'feedback': 'Perfect! Independent justice systems protect everyone\'s rights equally.',
                        'principle': 'Rule of Law',
                        'color': 'green'
                    },
                    {
                        'letter': 'B',
                        'text': 'The main leader personally decides all punishments',
                        'score': -3,
                        'feedback': 'This creates unfair treatment and allows abuse of power.',
                        'principle': 'Personal Rule',
                        'color': 'red'
                    },
                    {
                        'letter': 'C',
                        'text': 'Community elders make decisions based on tradition',
                        'score': 2,
                        'feedback': 'Traditional wisdom has value, but formal legal systems provide more consistency.',
                        'principle': 'Traditional Authority',
                        'color': 'blue'
                    },
                    {
                        'letter': 'D',
                        'text': 'Wealthy citizens can buy their way out of punishment',
                        'score': -2,
                        'feedback': 'This creates inequality and undermines justice for everyone.',
                        'principle': 'Corruption',
                        'color': 'red'
                    }
                ]
            },
            {
                'order': 5,
                'category': 'participation',
                'question_text': 'How should citizens participate in government decisions?',
                'scenario_context': 'Citizen participation helps ensure government serves the people\'s needs. Your country must decide how much and what kind of involvement citizens should have.',
                'learning_module_title': 'Civic Engagement and Democracy',
                'learning_module_content': 'Democracy works best when citizens are actively involved. Voting in elections is the most basic form of participation, but citizens can also contact representatives, join civic groups, and peacefully protest.\n\nWhen citizens participate actively, government is more responsive to their needs and less likely to become corrupt or disconnected from the people.',
                'options': [
                    {
                        'letter': 'A',
                        'text': 'Regular elections, public debates, and the right to petition government',
                        'score': 5,
                        'feedback': 'Excellent! Multiple forms of participation strengthen democracy.',
                        'principle': 'Civic Engagement',
                        'color': 'green'
                    },
                    {
                        'letter': 'B',
                        'text': 'Citizens vote once every few years and then leave government alone',
                        'score': 2,
                        'feedback': 'Regular elections are good, but more ongoing participation is better.',
                        'principle': 'Limited Democracy',
                        'color': 'blue'
                    },
                    {
                        'letter': 'C',
                        'text': 'Only educated or wealthy citizens can participate in government',
                        'score': -1,
                        'feedback': 'This excludes many people whose voices matter for good governance.',
                        'principle': 'Restricted Participation',
                        'color': 'orange'
                    },
                    {
                        'letter': 'D',
                        'text': 'Government knows best - citizens should not get involved',
                        'score': -3,
                        'feedback': 'Without citizen input, government becomes disconnected and unaccountable.',
                        'principle': 'Authoritarianism',
                        'color': 'red'
                    }
                ]
            },
            {
                'order': 6,
                'category': 'checks',
                'question_text': 'How should your country prevent any one person or group from having too much power?',
                'scenario_context': 'Power can corrupt people, so your country needs safeguards to prevent abuse. This is crucial for maintaining freedom and fairness.',
                'learning_module_title': 'Checks and Balances',
                'learning_module_content': 'Checks and balances prevent any single person or group from controlling everything. By dividing government power among different branches (like legislative, executive, and judicial), each branch can limit the others.\n\nThis system protects citizens from tyranny and ensures that important decisions are made carefully with input from multiple sources.',
                'options': [
                    {
                        'letter': 'A',
                        'text': 'Divide power among separate branches that can check each other',
                        'score': 5,
                        'feedback': 'Perfect! Separation of powers with checks and balances protects freedom.',
                        'principle': 'Separation of Powers',
                        'color': 'green'
                    },
                    {
                        'letter': 'B',
                        'text': 'Trust leaders to use power responsibly without restrictions',
                        'score': -3,
                        'feedback': 'Even good leaders can be corrupted by unlimited power.',
                        'principle': 'Unlimited Power',
                        'color': 'red'
                    },
                    {
                        'letter': 'C',
                        'text': 'Have regular elections to remove bad leaders',
                        'score': 3,
                        'feedback': 'Elections help, but additional checks during their time in office are important too.',
                        'principle': 'Electoral Accountability',
                        'color': 'blue'
                    },
                    {
                        'letter': 'D',
                        'text': 'Let different regions compete against each other for power',
                        'score': 0,
                        'feedback': 'Competition can be healthy but may lead to conflict rather than cooperation.',
                        'principle': 'Regional Competition',
                        'color': 'yellow'
                    }
                ]
            }
        ]

        # Create questions and options
        self.stdout.write('📝 Creating Constitution Challenge questions...')
        for q_data in questions_data:
            question, created = ConstitutionQuestion.objects.get_or_create(
                game=game,
                order=q_data['order'],
                defaults={
                    'category': q_data['category'],
                    'question_text': q_data['question_text'],
                    'scenario_context': q_data['scenario_context'],
                    'learning_module_title': q_data['learning_module_title'],
                    'learning_module_content': q_data['learning_module_content'],
                    'time_limit': 90,  # 90 seconds per question
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

        # Create a sample game session for testing
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

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('🎉 Constitution Challenge setup complete!'))
        self.stdout.write('')
        self.stdout.write('📊 Summary:')
        self.stdout.write(f'  • Game: {game.title}')
        self.stdout.write(f'  • Questions: {game.constitution_questions.count()}')
        self.stdout.write(f'  • Demo Session: {session.session_code}')
        self.stdout.write('')
        self.stdout.write('🚀 To test the game:')
        self.stdout.write(f'  1. Visit: http://localhost:8000/learn/constitution/{session.session_code}/')
        self.stdout.write('  2. Create a team and start playing!')
        self.stdout.write('')