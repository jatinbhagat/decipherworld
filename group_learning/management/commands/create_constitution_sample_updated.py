from django.core.management.base import BaseCommand
from group_learning.models import (
    Game, ConstitutionQuestion, ConstitutionOption, GameSession,
    LearningModule, LearningObjective
)


class Command(BaseCommand):
    help = 'Create updated Constitution Challenge game with comprehensive Indian Constitution questions'

    def add_arguments(self, parser):
        parser.add_argument('--reset', action='store_true', help='Reset existing data')

    def handle(self, *args, **options):
        if options['reset']:
            self.stdout.write('🗑️  Clearing existing Constitution Challenge data...')
            Game.objects.filter(game_type='constitution_challenge').delete()
            self.stdout.write(self.style.WARNING('Existing data cleared.'))

        # Create learning module
        learning_module, created = LearningModule.objects.get_or_create(
            name='Indian Constitution Fundamentals',
            defaults={
                'module_type': 'civics',
                'description': 'Comprehensive understanding of Indian Constitution principles, rights, duties, and governance structures',
                'grade_level': '8-12',
            }
        )

        # Create learning objectives
        objectives = [
            {
                'title': 'Understand democratic governance principles',
                'objective_type': 'knowledge',
                'description': 'Students will understand the basic principles of democratic governance and Indian Constitution',
            },
            {
                'title': 'Analyze fundamental rights and duties',
                'objective_type': 'critical_thinking',
                'description': 'Students will analyze the importance of fundamental rights and duties in a democracy',
            },
            {
                'title': 'Evaluate constitutional structures',
                'objective_type': 'skills',
                'description': 'Students will evaluate different aspects of constitutional governance and their consequences',
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
                'subtitle': 'Learn Indian Constitution by building your virtual country',
                'game_type': 'constitution_challenge',
                'description': 'A comprehensive team-based educational game where students learn about the Indian Constitution, fundamental rights, duties, governance structures, and democratic principles by making decisions that build and evolve their virtual country.',
                'context': 'Students work in teams to answer 16 multiple-choice questions covering all major aspects of the Indian Constitution including democracy, fundamental rights, duties, separation of powers, federalism, secularism, and socialism. Each answer affects their country\'s development and governance score.',
                'min_players': 1,
                'max_players': 50,
                'estimated_duration': 60,
                'target_age_min': 13,
                'target_age_max': 18,
                'difficulty_level': 2,
                'introduction_text': 'Welcome to Build Your Country! You and your team will explore the Indian Constitution by making important decisions about governance, rights, duties, and democratic principles. Every choice you make will shape your virtual country and help you understand how constitutional principles work in practice. Build the strongest democracy possible!',
            }
        )

        if created:
            game.learning_objectives.add(*created_objectives)
            self.stdout.write(self.style.SUCCESS(f'✅ Created game: {game.title}'))
        else:
            self.stdout.write(f'📋 Using existing game: {game.title}')

        # Comprehensive Constitution Challenge questions based on Indian Constitution
        questions_data = [
            # Q1 - Foundation
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
            
            # Q2 - Democracy
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
            
            # Q3 - Rights Protection
            {
                'order': 3,
                'category': 'rights',
                'question_text': 'What is the best way to protect everyone\'s rights in your country?',
                'scenario_context': 'Your country needs a system to ensure all citizens are treated fairly and their basic rights are protected.',
                'learning_module_title': 'Constitutional Rights Protection',
                'learning_module_content': 'A written constitution with clear rights ensures everyone knows what protections they have. When rights are written down, they cannot be easily changed or ignored by leaders.\n\nThis creates predictable protection for all citizens and prevents arbitrary decisions by those in power.',
                'options': [
                    {
                        'letter': 'A',
                        'text': 'A list of rights in the rulebook that everyone must respect',
                        'score': 2,
                        'feedback': 'A written list means rights are clear, protected, and for all. Universal, predictable protection.',
                        'principle': 'Constitutional Rights',
                        'color': 'green'
                    },
                    {
                        'letter': 'B',
                        'text': 'Let leaders decide what\'s fair each time',
                        'score': -2,
                        'feedback': 'Changing rules each time can be unfair; people never know their rights. Too much leader control.',
                        'principle': 'Arbitrary Rule',
                        'color': 'red'
                    },
                    {
                        'letter': 'C',
                        'text': 'Rights are only for groups who support the government',
                        'score': -3,
                        'feedback': 'Excluding groups creates unfairness; this can lead to conflict. Unfair, recipe for division.',
                        'principle': 'Conditional Rights',
                        'color': 'red'
                    }
                ]
            },
            
            # Q4 - Fundamental Rights
            {
                'order': 4,
                'category': 'rights',
                'question_text': 'In your new country, how should people\'s freedoms be handled?',
                'scenario_context': 'Citizens need basic freedoms to live with dignity and participate fully in society.',
                'learning_module_title': 'Fundamental Rights – Freedom & Equality',
                'learning_module_content': 'Fundamental Rights in India include: Right to Equality, Right to Freedom, Right against Exploitation, Right to Freedom of Religion, Cultural & Educational Rights, and Right to Constitutional Remedies.\n\nThese rights protect dignity and ensure all citizens can participate equally in society regardless of their background.',
                'options': [
                    {
                        'letter': 'A',
                        'text': 'Everyone should have freedom of expression, religion, equality before law',
                        'score': 2,
                        'feedback': 'Freedoms and equality protect dignity and fairness for all.',
                        'principle': 'Fundamental Rights',
                        'color': 'green'
                    },
                    {
                        'letter': 'B',
                        'text': 'Only certain groups get freedoms, depending on loyalty',
                        'score': -3,
                        'feedback': 'Rights only for loyal groups creates discrimination.',
                        'principle': 'Discriminatory System',
                        'color': 'red'
                    },
                    {
                        'letter': 'C',
                        'text': 'People have freedoms but can be taken away anytime leaders want',
                        'score': -2,
                        'feedback': 'Unstable freedoms mean people live in fear.',
                        'principle': 'Unstable Rights',
                        'color': 'red'
                    }
                ]
            },
            
            # Q5 - Freedom of Speech
            {
                'order': 5,
                'category': 'rights',
                'question_text': 'What should happen if citizens criticize the government publicly?',
                'scenario_context': 'Sometimes citizens may want to express disagreement with government actions or policies.',
                'learning_module_title': 'Right to Freedom of Speech and Expression',
                'learning_module_content': 'Article 19 of the Indian Constitution guarantees the Right to Freedom of Speech and Expression. This allows citizens to voice opinions, debate policies, and criticize government actions.\n\nWhile there are reasonable restrictions for security and public order, the ability to speak freely and criticize is essential for democracy to function properly.',
                'options': [
                    {
                        'letter': 'A',
                        'text': 'They should be punished for speaking against leaders',
                        'score': -3,
                        'feedback': 'This silences freedom and creates fear.',
                        'principle': 'Authoritarian Control',
                        'color': 'red'
                    },
                    {
                        'letter': 'B',
                        'text': 'They should be allowed to speak, even if leaders don\'t like it',
                        'score': 2,
                        'feedback': 'Freedom of speech allows ideas and improvements.',
                        'principle': 'Free Expression',
                        'color': 'green'
                    },
                    {
                        'letter': 'C',
                        'text': 'Only positive speech should be free, negative speech banned',
                        'score': -2,
                        'feedback': 'If only praise is allowed, real issues remain hidden.',
                        'principle': 'Censorship',
                        'color': 'red'
                    }
                ]
            },
            
            # Q6 - Resolving Conflicts
            {
                'order': 6,
                'category': 'justice',
                'question_text': 'If two groups in your country disagree—say, one wants a festival holiday and another does not—how should decisions be made?',
                'scenario_context': 'Different groups in society sometimes have conflicting interests that need to be resolved fairly.',
                'learning_module_title': 'Majority vs Minority Rights and Rule of Law',
                'learning_module_content': 'In India, the Constitution protects minority rights while allowing majority rule. Articles 14-16 ensure equality and prevent discrimination.\n\nThe Rule of Law means that decisions should be made fairly, considering both majority wishes and minority protection, ensuring no group is completely ignored.',
                'options': [
                    {
                        'letter': 'A',
                        'text': 'The bigger group always wins',
                        'score': -2,
                        'feedback': 'Majority rule can silence smaller groups. Risk of unfairness.',
                        'principle': 'Majority Tyranny',
                        'color': 'red'
                    },
                    {
                        'letter': 'B',
                        'text': 'The minority group also gets protected, with fair compromise',
                        'score': 2,
                        'feedback': 'Balancing both sides respects diversity. Protects minorities, supports inclusiveness.',
                        'principle': 'Minority Protection',
                        'color': 'green'
                    },
                    {
                        'letter': 'C',
                        'text': 'Leaders ignore the conflict and move on',
                        'score': -1,
                        'feedback': 'Ignoring issues makes groups unhappy and can cause bigger problems. Conflict grows unresolved.',
                        'principle': 'Avoidance',
                        'color': 'orange'
                    }
                ]
            },
            
            # Q7 - Citizen Duties
            {
                'order': 7,
                'category': 'participation',
                'question_text': 'In your new country, what should citizens be expected to do to keep society functioning well?',
                'scenario_context': 'Rights come with responsibilities. Your country needs to decide what citizens should contribute to society.',
                'learning_module_title': 'Citizen Responsibilities',
                'learning_module_content': 'Just as people claim rights, they also must uphold duties. When citizens follow laws, pay taxes, and contribute to society, the country becomes stronger and more fair for everyone.\n\nShared responsibility creates trust between citizens and government, and helps build a better society for all.',
                'options': [
                    {
                        'letter': 'A',
                        'text': 'Nothing. Only the government should do everything',
                        'score': -2,
                        'feedback': 'If citizens do nothing, the government cannot function effectively. No shared responsibility.',
                        'principle': 'Government Dependency',
                        'color': 'red'
                    },
                    {
                        'letter': 'B',
                        'text': 'Citizens should obey laws and pay taxes',
                        'score': 2,
                        'feedback': 'When people follow laws and contribute, society is stronger. Collective responsibility, fairness.',
                        'principle': 'Civic Duty',
                        'color': 'green'
                    },
                    {
                        'letter': 'C',
                        'text': 'Citizens should help only if it benefits them personally',
                        'score': -1,
                        'feedback': 'Helping only when it benefits you weakens trust. Self-interest harms the country.',
                        'principle': 'Selfish Behavior',
                        'color': 'orange'
                    }
                ]
            },
            
            # Q8 - Fundamental Duties
            {
                'order': 8,
                'category': 'participation',
                'question_text': 'Suppose some citizens refuse to respect the national flag or damage public property. What should be expected?',
                'scenario_context': 'Your country needs to establish expectations for how citizens should treat national symbols and public resources.',
                'learning_module_title': 'Fundamental Duties – Respect & Responsibility',
                'learning_module_content': 'Article 51A of the Indian Constitution lists Fundamental Duties including respecting the Constitution, promoting harmony, and protecting the environment.\n\nThese duties create respect and responsibility and keep society united. Citizens have both rights and duties to ensure a balanced democracy.',
                'options': [
                    {
                        'letter': 'A',
                        'text': 'Citizens must respect national symbols, protect environment, preserve heritage',
                        'score': 2,
                        'feedback': 'Duties create respect and responsibility and keep society united. Shared responsibility.',
                        'principle': 'Fundamental Duties',
                        'color': 'green'
                    },
                    {
                        'letter': 'B',
                        'text': 'Citizens have only rights, no duties',
                        'score': -2,
                        'feedback': 'Rights without duties can lead to misuse and imbalance.',
                        'principle': 'Rights Without Duties',
                        'color': 'red'
                    },
                    {
                        'letter': 'C',
                        'text': 'Leaders alone must take care; citizens need not bother',
                        'score': -2,
                        'feedback': 'Without citizen cooperation, the nation falters.',
                        'principle': 'Citizen Apathy',
                        'color': 'red'
                    }
                ]
            },
            
            # Q9 - Separation of Powers
            {
                'order': 9,
                'category': 'checks',
                'question_text': 'In your new country, how should power be divided?',
                'scenario_context': 'Your country needs to organize government power to prevent any single group from having too much control.',
                'learning_module_title': 'Separation of Powers – Who Makes, Who Enforces, Who Checks?',
                'learning_module_content': 'India follows Separation of Powers with Legislature (makes laws), Executive (implements laws), and Judiciary (interprets & checks laws).\n\nThis division ensures no one has absolute power and prevents dictatorship-like concentration of authority. Each branch can check the others for balance.',
                'options': [
                    {
                        'letter': 'A',
                        'text': 'One group of leaders makes laws, enforces them, and judges disputes',
                        'score': -3,
                        'feedback': 'If one group controls everything, there is no fairness. Dangerous concentration of power.',
                        'principle': 'Concentrated Power',
                        'color': 'red'
                    },
                    {
                        'letter': 'B',
                        'text': 'Different groups—one makes laws, one enforces them, one interprets them',
                        'score': 2,
                        'feedback': 'Separation ensures no one has absolute power. Legislature makes laws, executive carries them out, judiciary checks fairness. Balanced governance.',
                        'principle': 'Separation of Powers',
                        'color': 'green'
                    },
                    {
                        'letter': 'C',
                        'text': 'Leaders make rules, and judges just follow orders from them',
                        'score': -2,
                        'feedback': 'Judges must stay independent; otherwise justice is not possible. No real checks.',
                        'principle': 'Dependent Judiciary',
                        'color': 'red'
                    }
                ]
            },
            
            # Q10 - Judicial Review
            {
                'order': 10,
                'category': 'checks',
                'question_text': 'In your country, leaders are making rules—but who will ensure they don\'t misuse their powers?',
                'scenario_context': 'Even elected leaders might sometimes make unfair laws or abuse their power. Your country needs a system to check this.',
                'learning_module_title': 'Judicial Review and Independent Judiciary',
                'learning_module_content': 'In India, the Supreme Court ensures government actions follow the Constitution through Judicial Review. Independent judges can review and stop unfair laws.\n\nThis system protects citizens\' rights even from their own elected representatives, ensuring government power has limits.',
                'options': [
                    {
                        'letter': 'A',
                        'text': 'Nobody. Leaders should be fully trusted',
                        'score': -3,
                        'feedback': 'Without limits, power can be abused. Unsafe governance.',
                        'principle': 'Unlimited Power',
                        'color': 'red'
                    },
                    {
                        'letter': 'B',
                        'text': 'A group of judges who can review and stop unfair laws',
                        'score': 2,
                        'feedback': 'Judges act independently to check bad laws. Judiciary protects fairness.',
                        'principle': 'Judicial Review',
                        'color': 'green'
                    },
                    {
                        'letter': 'C',
                        'text': 'Citizens protest later if something goes wrong',
                        'score': 0,
                        'feedback': 'Protests can help, but prevention is better than cure. Not reliable enough.',
                        'principle': 'Reactive Response',
                        'color': 'yellow'
                    }
                ]
            },
            
            # Q11 - Constitutional Amendments
            {
                'order': 11,
                'category': 'checks',
                'question_text': 'Sometimes the country may need to update rules as society grows. How should changes be made to the Constitution?',
                'scenario_context': 'Societies change over time, and sometimes the basic rules of government may need updates to stay relevant.',
                'learning_module_title': 'Constitutional Amendments',
                'learning_module_content': 'In India, some parts of the Constitution can be changed by Parliament, but core principles like equality, democracy, and secularism cannot be destroyed.\n\nThis balance allows necessary updates while protecting fundamental democratic values from being eliminated.',
                'options': [
                    {
                        'letter': 'A',
                        'text': 'Leaders can change anything whenever they want',
                        'score': -2,
                        'feedback': 'Too easy to change—it may lose its stability.',
                        'principle': 'Easy Amendment',
                        'color': 'red'
                    },
                    {
                        'letter': 'B',
                        'text': 'Citizens must all agree every time—no matter how small',
                        'score': -1,
                        'feedback': 'If unanimous agreement is required, no changes may ever happen.',
                        'principle': 'Rigid Amendment',
                        'color': 'orange'
                    },
                    {
                        'letter': 'C',
                        'text': 'A special process with discussion and checks before changes are added',
                        'score': 2,
                        'feedback': 'Careful process balances flexibility and stability.',
                        'principle': 'Balanced Amendment',
                        'color': 'green'
                    }
                ]
            },
            
            # Q12 - Federalism
            {
                'order': 12,
                'category': 'participation',
                'question_text': 'Imagine your country is very large—how should it be organised?',
                'scenario_context': 'Large countries face the challenge of governing both national and local issues effectively across diverse regions.',
                'learning_module_title': 'Three-Tier Federalism – Who Governs What?',
                'learning_module_content': 'India\'s three-tier federal system includes Union Government, State Governments, and Local Governments (73rd & 74th Amendments).\n\nThis division allows central government to handle big issues like defense and foreign policy, states to manage regional matters like health and education, and local bodies to address immediate community needs like water and sanitation.',
                'options': [
                    {
                        'letter': 'A',
                        'text': 'Only one central government decides everything',
                        'score': -2,
                        'feedback': 'Too much central control ignores local needs. Over-centralization.',
                        'principle': 'Centralization',
                        'color': 'red'
                    },
                    {
                        'letter': 'B',
                        'text': 'Central, regional (states), and local bodies share responsibilities',
                        'score': 2,
                        'feedback': 'Division allows central government to handle big things, states regional issues, local bodies immediate needs. Efficient + inclusive.',
                        'principle': 'Federalism',
                        'color': 'green'
                    },
                    {
                        'letter': 'C',
                        'text': 'Every village should make all decisions without any higher body',
                        'score': -1,
                        'feedback': 'Only local governments might struggle with big issues like national security. Fragmented governance.',
                        'principle': 'Extreme Localization',
                        'color': 'orange'
                    }
                ]
            },
            
            # Q13 - Directive Principles
            {
                'order': 13,
                'category': 'participation',
                'question_text': 'Your leaders must plan the country\'s future. What should guide their decisions?',
                'scenario_context': 'Government leaders need principles to guide them when making policies that will shape society\'s future.',
                'learning_module_title': 'Directive Principles – Guiding Government Choices',
                'learning_module_content': 'Directive Principles of State Policy guide governments to build justice, equality, and welfare through policies like free education and workers\' rights.\n\nWhile not legally enforceable like Fundamental Rights, these principles help create a fairer society and reduce inequality over time.',
                'options': [
                    {
                        'letter': 'A',
                        'text': 'Focus only on today\'s survival, forget future justice or welfare',
                        'score': -1,
                        'feedback': 'Short-term vision ignores society\'s long-term needs.',
                        'principle': 'Short-term Focus',
                        'color': 'orange'
                    },
                    {
                        'letter': 'B',
                        'text': 'Include goals like free education, reducing poverty, gender equality in state policies',
                        'score': 2,
                        'feedback': 'These guiding principles help create a fairer society, even if they are not enforceable laws.',
                        'principle': 'Directive Principles',
                        'color': 'green'
                    },
                    {
                        'letter': 'C',
                        'text': 'Government should not care about fairness, only money growth',
                        'score': -2,
                        'feedback': 'Ignoring fairness causes inequality and unrest.',
                        'principle': 'Economic Focus Only',
                        'color': 'red'
                    }
                ]
            },
            
            # Q14 - Preamble
            {
                'order': 14,
                'category': 'leadership',
                'question_text': 'Your new country\'s rulebook starts with an opening promise. What should it say?',
                'scenario_context': 'The opening statement of your constitution will set the tone and values for your entire country.',
                'learning_module_title': 'Preamble – Core Values',
                'learning_module_content': 'India\'s Preamble begins "We the People..." and declares goals of sovereignty, socialism, secularism, democracy, republic, justice, liberty, equality, and fraternity.\n\nThese values guide the entire Constitution and show what kind of society India aims to build.',
                'options': [
                    {
                        'letter': 'A',
                        'text': 'It should declare that the country belongs to some groups only',
                        'score': -3,
                        'feedback': 'Excluding groups breaks unity.',
                        'principle': 'Exclusionary Values',
                        'color': 'red'
                    },
                    {
                        'letter': 'B',
                        'text': 'It should promise democracy, justice, liberty, equality, and fraternity for all',
                        'score': 3,
                        'feedback': 'Values like justice, liberty, equality, fraternity guide the whole Constitution. Positive foundation.',
                        'principle': 'Democratic Values',
                        'color': 'green'
                    },
                    {
                        'letter': 'C',
                        'text': 'It should only talk about economic growth, nothing else',
                        'score': -1,
                        'feedback': 'Ignoring equality and fairness neglects people\'s dignity.',
                        'principle': 'Economic Focus Only',
                        'color': 'orange'
                    }
                ]
            },
            
            # Q15 - Secularism
            {
                'order': 15,
                'category': 'rights',
                'question_text': 'How should your country treat religion?',
                'scenario_context': 'Your diverse country has citizens of many different faiths who all need to feel equally treated and protected.',
                'learning_module_title': 'Secularism – Religion in Governance',
                'learning_module_content': 'Secularism in India means equal treatment of all faiths and protection of minorities. Articles 25-28 guarantee freedom of religion.\n\nThis creates harmony and peace by ensuring no religious group is favored or discriminated against by the government.',
                'options': [
                    {
                        'letter': 'A',
                        'text': 'Government should support only one religion',
                        'score': -3,
                        'feedback': 'Favouring one religion causes unfairness and division.',
                        'principle': 'Religious Favoritism',
                        'color': 'red'
                    },
                    {
                        'letter': 'B',
                        'text': 'Government should treat all religions equally, without bias',
                        'score': 2,
                        'feedback': 'True secularism means equal respect for all faiths. Harmony and peace.',
                        'principle': 'Secularism',
                        'color': 'green'
                    },
                    {
                        'letter': 'C',
                        'text': 'Government should allow religion to control politics',
                        'score': -2,
                        'feedback': 'Religion dominating politics risks discrimination and conflict.',
                        'principle': 'Theocratic Control',
                        'color': 'red'
                    }
                ]
            },
            
            # Q16 - Socialism
            {
                'order': 16,
                'category': 'rights',
                'question_text': 'In your country, many citizens are poor. How should the Constitution address this?',
                'scenario_context': 'Your country has economic inequality, with some citizens lacking basic necessities while others have plenty.',
                'learning_module_title': 'Socialism – Who Should Help the Poor?',
                'learning_module_content': 'Socialism in India\'s Preamble means the democracy combines individual freedoms with social justice, helping uplift weaker sections of society.\n\nGovernment policies to reduce poverty and provide welfare ensure fairness and prevent extreme inequality that could harm social stability.',
                'options': [
                    {
                        'letter': 'A',
                        'text': 'Government should work to reduce inequality and ensure welfare',
                        'score': 2,
                        'feedback': 'Government policies to reduce poverty and provide welfare ensure fairness.',
                        'principle': 'Social Justice',
                        'color': 'green'
                    },
                    {
                        'letter': 'B',
                        'text': 'It\'s not the government\'s job; poor people are on their own',
                        'score': -2,
                        'feedback': 'Ignoring the poor creates huge inequality.',
                        'principle': 'Social Neglect',
                        'color': 'red'
                    },
                    {
                        'letter': 'C',
                        'text': 'Only rich people decide on charity if they wish',
                        'score': -1,
                        'feedback': 'Charity is uncertain and unfair.',
                        'principle': 'Voluntary Charity',
                        'color': 'orange'
                    }
                ]
            }
        ]

        # Create questions and options
        self.stdout.write('📝 Creating comprehensive Constitution Challenge questions...')
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
                    'time_limit': 120,  # 2 minutes per question
                }
            )

            if created:
                self.stdout.write(f'  ✅ Created question {q_data["order"]}: {q_data["question_text"][:60]}...')
                
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
            session_code='CONST2024',
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
        self.stdout.write(self.style.SUCCESS('🎉 Comprehensive Constitution Challenge setup complete!'))
        self.stdout.write('')
        self.stdout.write('📊 Summary:')
        self.stdout.write(f'  • Game: {game.title}')
        self.stdout.write(f'  • Questions: {game.constitution_questions.count()}')
        self.stdout.write(f'  • Demo Session: {session.session_code}')
        self.stdout.write('')
        self.stdout.write('📚 Topics Covered:')
        self.stdout.write('  • Foundation of Governance & Democracy')
        self.stdout.write('  • Fundamental Rights & Freedom of Speech')
        self.stdout.write('  • Fundamental Duties & Civic Responsibility')
        self.stdout.write('  • Separation of Powers & Judicial Review')
        self.stdout.write('  • Federalism & Constitutional Amendments')
        self.stdout.write('  • Directive Principles & Preamble Values')
        self.stdout.write('  • Secularism & Social Justice')
        self.stdout.write('')
        self.stdout.write('🚀 To test the game:')
        self.stdout.write(f'  1. Visit: http://localhost:8000/learn/constitution/{session.session_code}/')
        self.stdout.write('  2. Create a team and start building your country!')
        self.stdout.write('')