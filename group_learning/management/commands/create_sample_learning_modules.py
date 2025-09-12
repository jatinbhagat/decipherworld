from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from group_learning.models import GameLearningModule, Game, ConstitutionQuestion


class Command(BaseCommand):
    help = 'Create sample learning modules for Constitution Challenge game'

    def add_arguments(self, parser):
        parser.add_argument(
            '--overwrite',
            action='store_true',
            help='Delete existing sample modules first',
        )

    def handle(self, *args, **options):
        if options['overwrite']:
            GameLearningModule.objects.filter(title__startswith='Sample:').delete()
            self.stdout.write(
                self.style.WARNING('Deleted existing sample learning modules')
            )

        # Get or create a Constitution game
        try:
            constitution_game = Game.objects.get(
                game_type='constitution_challenge',
                title__icontains='constitution'
            )
        except Game.DoesNotExist:
            self.stdout.write(
                self.style.ERROR('No Constitution Challenge game found. Please create one first.')
            )
            return

        # Get the first admin user as created_by
        admin_user = User.objects.filter(is_superuser=True).first()

        sample_modules = [
            {
                'title': 'Sample: Understanding Democracy',
                'game_type': 'constitution_challenge',
                'principle_explanation': '''Democracy is a system of government where power ultimately rests with the people. In a democratic system, citizens have the right to participate in decision-making processes, either directly or through elected representatives.

The word "democracy" comes from the Greek words "demos" (people) and "kratos" (power or rule), literally meaning "rule by the people." This fundamental principle ensures that government serves the interests of its citizens rather than a small elite group.''',
                'key_takeaways': '''• Democracy means "rule by the people" - citizens have ultimate power
• People participate through voting and electing representatives
• Democratic governments are accountable to their citizens
• Individual rights are protected even within majority rule
• Democratic systems include checks and balances to prevent abuse of power''',
                'historical_context': '''The concept of democracy has ancient roots, with early examples in ancient Greece around 500 BCE. The city-state of Athens practiced direct democracy where citizens could directly participate in decision-making.

Modern democracy evolved through centuries of struggle, with key milestones including the Magna Carta (1215), the American Revolution (1776), and the French Revolution (1789). Each contributed ideas about limiting government power and protecting individual rights.''',
                'real_world_example': '''India is the world\'s largest democracy, with over 900 million eligible voters. During elections, citizens from diverse backgrounds - farmers, urban professionals, students - all have equal voting power regardless of their economic status.

The Indian Constitution ensures that even minority voices are heard through reserved seats in Parliament and state legislatures. This shows how democracy can work in a diverse, multi-cultural society.''',
                'trigger_condition': 'topic_based',
                'trigger_topic': 'leadership',
                'display_timing': 'instant',
                'is_skippable': True,
                'is_enabled': True,
            },
            {
                'title': 'Sample: Fundamental Rights',
                'game_type': 'constitution_challenge',
                'principle_explanation': '''Fundamental rights are basic human rights guaranteed by the Constitution that protect individual freedom and dignity. These rights create a protective shield around citizens, ensuring the government cannot arbitrarily restrict their liberties.

The Indian Constitution guarantees six fundamental rights: Right to Equality, Right to Freedom, Right against Exploitation, Right to Freedom of Religion, Cultural and Educational Rights, and Right to Constitutional Remedies. These rights are enforceable by courts and are essential for human dignity.''',
                'key_takeaways': '''• Fundamental rights protect individual freedom and dignity
• These rights are guaranteed by the Constitution and enforced by courts
• They include equality, freedom, protection from exploitation, and religious freedom
• Right to Constitutional Remedies allows citizens to approach courts when rights are violated
• Rights come with responsibilities - freedom must be exercised responsibly''',
                'historical_context': '''The concept of fundamental rights emerged from centuries of struggle against oppression. The American Bill of Rights (1791) and the French Declaration of Rights (1789) were early examples.

India\'s freedom struggle highlighted the need for protecting individual rights. Leaders like Dr. B.R. Ambedkar, who chaired the Constitution Drafting Committee, ensured that fundamental rights would be an integral part of independent India\'s Constitution.''',
                'real_world_example': '''When the government tried to impose emergency in 1975, many fundamental rights were suspended. Citizens could be arrested without trial, and press freedom was curtailed. 

This experience taught Indians the importance of protecting fundamental rights. After the emergency was lifted in 1977, constitutional amendments were made to ensure such violations could never happen again, showing how rights protect democracy itself.''',
                'trigger_condition': 'topic_based',
                'trigger_topic': 'rights',
                'display_timing': 'instant',
                'is_skippable': True,
                'is_enabled': True,
            },
            {
                'title': 'Sample: Justice and Fairness',
                'game_type': 'constitution_challenge',
                'principle_explanation': '''Justice means treating all people fairly and equally under the law. A just system ensures that everyone gets what they deserve based on their actions and circumstances, not their background, wealth, or social status.

The Constitution establishes an independent judiciary to ensure justice. Courts interpret laws, settle disputes, and protect citizens\' rights. The principle "justice delayed is justice denied" emphasizes that fair treatment must be both accessible and timely.''',
                'key_takeaways': '''• Justice means treating all people fairly and equally under the law
• Independent judiciary protects citizens from government overreach
• Courts interpret laws and settle disputes impartially
• Everyone has the right to a fair trial and legal representation
• Justice must be accessible to all, regardless of social or economic status''',
                'historical_context': '''The idea of impartial justice has deep roots in human civilization. Ancient codes like Hammurabi\'s Code (1750 BCE) established early legal principles.

In India, the concept of "Dharma" traditionally emphasized righteous conduct and fair treatment. The modern Indian judicial system combines this heritage with contemporary legal principles, creating a system that respects both tradition and progress.''',
                'real_world_example': '''The Right to Information Act (2005) empowers ordinary citizens to seek information from government offices. A farmer in rural Maharashtra used RTI to discover corruption in a local development project.

Despite having limited resources, the farmer could approach courts for justice. The case was decided purely on facts and law, not on the farmer\'s social status, demonstrating how justice works equally for all citizens.''',
                'trigger_condition': 'topic_based',
                'trigger_topic': 'justice',
                'display_timing': 'instant',
                'is_skippable': True,
                'is_enabled': True,
            },
            {
                'title': 'Sample: Citizen Participation',
                'game_type': 'constitution_challenge',
                'principle_explanation': '''Citizen participation is the cornerstone of democracy. It means that people don\'t just vote once every few years, but actively engage in the democratic process through various means - voting, contesting elections, participating in public debates, and holding government accountable.

Effective citizen participation requires both rights and responsibilities. Citizens must stay informed about issues, participate constructively in debates, and exercise their civic duties responsibly. Democracy works best when citizens are engaged and active.''',
                'key_takeaways': '''• Democracy requires active participation from citizens, not just voting
• Citizens can participate through elections, public debates, and civic activities
• Staying informed about issues is a civic responsibility
• Peaceful protest and constructive criticism strengthen democracy
• Local participation (panchayats, municipal bodies) is as important as national politics''',
                'historical_context': '''The Indian independence movement was built on mass participation. Mahatma Gandhi\'s methods showed how ordinary citizens could participate in political change through non-violent resistance.

The 73rd and 74th Constitutional Amendments (1992) created local self-government institutions (panchayats and municipalities), bringing democracy closer to people and encouraging grassroots participation.''',
                'real_world_example': '''In Kerala, the People\'s Planning Campaign involves citizens directly in planning local development projects. Villagers gather in gram sabhas (village assemblies) to discuss priorities like road construction, water supply, and education.

These meetings aren\'t just consultative - citizens make actual decisions about how government funds are spent in their area. This shows how meaningful participation goes beyond voting to include direct involvement in governance.''',
                'trigger_condition': 'topic_based',
                'trigger_topic': 'participation',
                'display_timing': 'instant',
                'is_skippable': True,
                'is_enabled': True,
            },
            {
                'title': 'Sample: Checks and Balances',
                'game_type': 'constitution_challenge',
                'principle_explanation': '''Checks and balances prevent any single institution from becoming too powerful. In a democracy, power is distributed among different branches of government - legislative (makes laws), executive (implements laws), and judiciary (interprets laws) - so they can monitor and limit each other.

This system ensures that no person or group can abuse power. Each branch has specific powers but also faces limitations from the other branches. This balance protects democracy from both tyranny and chaos.''',
                'key_takeaways': '''• Power is divided among legislature, executive, and judiciary to prevent abuse
• Each branch can limit the others through constitutional mechanisms
• Parliament can impeach judges, courts can strike down unconstitutional laws
• President can return bills to Parliament for reconsideration
• Independent institutions like Election Commission ensure fair governance''',
                'historical_context': '''The concept was developed by French philosopher Montesquieu and implemented in the American Constitution. The Indian Constitution adopted this principle while adapting it to parliamentary democracy.

Dr. B.R. Ambedkar emphasized that constitutional methods must be used to achieve social and political goals, highlighting the importance of institutional safeguards over individual personalities.''',
                'real_world_example': '''In 2019, the Supreme Court held that the Chief Justice of India\'s office falls under the Right to Information Act. This decision, opposed by the executive, showed how judicial independence works.

When Parliament passes a law, courts can review if it violates constitutional principles. When governments try to influence elections, the Election Commission can take action. These real-world checks prevent any single institution from dominating others.''',
                'trigger_condition': 'topic_based',
                'trigger_topic': 'checks',
                'display_timing': 'instant',
                'is_skippable': True,
                'is_enabled': True,
            },
            {
                'title': 'Sample: Achieving High Governance Score',
                'game_type': 'constitution_challenge',
                'principle_explanation': '''Congratulations on building a strong democratic foundation! High governance scores indicate that your constitutional choices are creating a balanced, fair, and effective system of government.

Your decisions show understanding of how different constitutional principles work together. Democracy isn\'t just about one aspect - it requires balancing majority rule with minority rights, efficiency with accountability, and individual freedom with collective responsibility.''',
                'key_takeaways': '''• Strong democracy requires balance between competing values
• High scores show good understanding of constitutional principles
• Effective governance combines multiple elements working together
• Your choices demonstrate civic maturity and democratic thinking
• Real democracy is an ongoing process of balancing different needs''',
                'high_performance_content': '''Your exceptional performance shows deep understanding of constitutional governance! You\'ve demonstrated that effective democracy requires sophisticated thinking about complex trade-offs.

Consider how you might apply this understanding in real life - whether in student government, community organizations, or future civic participation. The skills you\'ve shown here translate directly to real-world democratic participation.''',
                'trigger_condition': 'score_based',
                'min_score': 18,
                'display_timing': 'instant',
                'is_skippable': True,
                'is_enabled': True,
            }
        ]

        created_count = 0
        for module_data in sample_modules:
            module_data['created_by'] = admin_user
            learning_module = GameLearningModule(**module_data)
            learning_module.save()
            created_count += 1
            
            self.stdout.write(
                self.style.SUCCESS(f'Created: {learning_module.title}')
            )

        self.stdout.write(
            self.style.SUCCESS(
                f'\nSuccessfully created {created_count} sample learning modules for Constitution Challenge!'
            )
        )
        self.stdout.write(
            self.style.WARNING(
                'You can now view and edit these modules in Django Admin under "Learning Modules"'
            )
        )