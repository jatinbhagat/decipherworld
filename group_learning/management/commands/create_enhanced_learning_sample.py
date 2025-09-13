from django.core.management.base import BaseCommand
from group_learning.models import GameLearningModule, ConstitutionQuestion, ConstitutionOption


class Command(BaseCommand):
    help = 'Create sample enhanced learning modules for Constitution Challenge'

    def handle(self, *args, **options):
        self.stdout.write('Creating enhanced learning module samples...')

        # Sample 1: Democratic Rights and Governance
        module1 = GameLearningModule.objects.create(
            title='Democratic Rights and Good Governance',
            game_type='constitution_challenge',
            
            # Core content
            principle_explanation='Democratic governance requires balancing majority rule with minority rights while ensuring transparency and accountability.',
            key_takeaways='• Democratic decisions should consider all citizens\n• Transparency builds public trust\n• Minority rights must be protected\n• Accountability prevents corruption',
            
            # Part 1: Action Reasoning
            action_impact_title='How Your Choice Shapes Democracy',
            governance_impact='Your decision to prioritize transparent governance over quick decision-making strengthens democratic institutions. While it may slow immediate progress, it builds long-term trust between citizens and government, creating a foundation for sustainable development.',
            score_reasoning='Governance score increased by +15 points because transparency and citizen participation are fundamental to healthy democracy. Citizens feel more engaged when they understand government decisions, leading to higher cooperation and legitimacy.',
            country_state_changes='The city grows more steadily as citizens trust government planning. Population satisfaction increases, leading to more skilled workers moving to your nation. Economic growth may be slower initially but becomes more sustainable and inclusive.',
            societal_impact='Citizens develop stronger civic engagement and trust in institutions. Social cohesion improves as all groups feel their voices are heard. This creates a positive cycle where democracy reinforces itself through participation.',
            
            # Part 2: Constitution Teaching
            constitution_topic_title='Indian Constitution: Democratic Principles',
            constitution_chapter='features',
            constitution_principle='Democratic Governance and Right to Information',
            constitution_explanation='The Indian Constitution establishes a democratic republic where sovereignty lies with the people. Article 19(1)(a) guarantees freedom of speech and expression, while the Right to Information Act (2005) ensures government transparency. The Preamble declares India as a "Democratic Republic," meaning all power flows from the people.',
            constitution_article_reference='Article 19(1)(a): Freedom of Speech and Expression; Preamble: Democratic Republic; Directive Principles Article 39(b): Distribution of material resources',
            historical_constitutional_context='During the Constituent Assembly debates, Dr. B.R. Ambedkar emphasized that democracy is not just about majority rule but about constitutional morality. The framers were inspired by the American Bill of Rights but adapted it to Indian conditions, ensuring that democracy would protect all communities.',
            
            # Trigger settings
            trigger_condition='always',
            is_enabled=True,
            is_skippable=True
        )

        # Sample 2: Fundamental Rights vs Social Harmony
        module2 = GameLearningModule.objects.create(
            title='Balancing Individual Rights and Social Harmony',
            game_type='constitution_challenge',
            
            # Core content
            principle_explanation='Constitutional democracies must balance individual freedoms with collective welfare and social harmony.',
            key_takeaways='• Individual rights are not absolute\n• Reasonable restrictions protect society\n• Balance prevents both tyranny and chaos\n• Constitutional framework guides decisions',
            
            # Part 1: Action Reasoning
            action_impact_title='Impact of Rights vs. Harmony Balance',
            governance_impact='Your choice to allow peaceful protest while setting clear boundaries shows constitutional wisdom. This demonstrates that rights come with responsibilities, building a culture where freedom and order coexist.',
            score_reasoning='Governance score increased by +12 points for showing constitutional maturity. Citizens see that their rights are protected but not at the expense of social stability, creating trust in the legal system.',
            country_state_changes='Economic activity continues during controlled protests, showing foreign investors that your nation has stable institutions. Cities remain functional while allowing democratic expression, attracting both businesses and civil society organizations.',
            societal_impact='Citizens learn that democracy is about responsible freedom. Minority groups feel protected while majority groups see that rights have reasonable limits. This builds a mature democratic culture.',
            
            # Part 2: Constitution Teaching
            constitution_topic_title='Indian Constitution: Fundamental Rights and Restrictions',
            constitution_chapter='rights_duties',
            constitution_principle='Fundamental Rights with Reasonable Restrictions',
            constitution_explanation='The Indian Constitution grants fundamental rights in Articles 12-35, but these rights are not absolute. Article 19(2) allows "reasonable restrictions" on free speech for sovereignty, public order, and morality. This balance reflects the Constitution\'s wisdom in protecting both individual liberty and collective welfare.',
            constitution_article_reference='Article 19(1): Six Fundamental Rights; Article 19(2): Reasonable Restrictions; Article 21: Right to Life and Personal Liberty',
            historical_constitutional_context='The Constituent Assembly debated whether rights should be absolute or qualified. Influenced by the Irish Constitution and practical governance needs, they chose "reasonable restrictions" - a uniquely Indian approach that balances Western liberalism with social responsibility.',
            
            # Trigger settings
            trigger_condition='topic_based',
            trigger_topic='fundamental_rights',
            is_enabled=True,
            is_skippable=True
        )

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created {GameLearningModule.objects.count()} enhanced learning modules!'
            )
        )
        
        self.stdout.write('Enhanced Learning Modules created:')
        for module in GameLearningModule.objects.all():
            self.stdout.write(f'- {module.title} ({module.get_trigger_condition_display()})')