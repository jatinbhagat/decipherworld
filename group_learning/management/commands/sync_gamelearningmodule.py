"""
Django management command to sync GameLearningModule data to production
Usage: python manage.py sync_gamelearningmodule
"""
from django.core.management.base import BaseCommand
from group_learning.models import GameLearningModule

class Command(BaseCommand):
    help = 'Sync GameLearningModule data to database'

    def handle(self, *args, **options):
        self.stdout.write("=== SYNCING GameLearningModule DATA ===")
        
        # Data to create/update
        modules_data = [
            {'title': 'Sample: Understanding Democracy', 'game_type': 'constitution_challenge', 'trigger_condition': 'always', 'is_enabled': False, 'is_skippable': True, 'display_timing': 'instant', 'principle_explanation': 'Understanding what democracy means and how it works in practice. Democracy is more than just voting - it includes citizen participation, checks and balances, and protection of individual rights while serving the common good.', 'key_takeaways': '• Democracy requires active citizen participation\n• Voting is just one part of democratic governance\n• Balance between individual rights and collective good\n• Importance of checks and balances in government', 'trigger_topic': ''},
            {'title': 'Sample: Fundamental Rights', 'game_type': 'constitution_challenge', 'trigger_condition': 'always', 'is_enabled': False, 'is_skippable': True, 'display_timing': 'instant', 'principle_explanation': 'Fundamental rights are basic human rights that every citizen enjoys, protected by the Constitution. These include right to equality, freedom of speech, right to life and personal liberty, and others that form the foundation of a democratic society.', 'key_takeaways': '• Right to Equality (Article 14-18)\n• Right to Freedom (Article 19-22)\n• Right against Exploitation (Article 23-24)\n• Right to Freedom of Religion (Article 25-28)\n• Cultural and Educational Rights (Article 29-30)', 'trigger_topic': ''},
            {'title': 'Sample: Justice and Fairness', 'game_type': 'constitution_challenge', 'trigger_condition': 'always', 'is_enabled': False, 'is_skippable': True, 'display_timing': 'instant', 'principle_explanation': 'Justice means treating people fairly and ensuring equal opportunities for all. In governance, this means making decisions that consider the needs of all citizens, not just the powerful or wealthy ones.', 'key_takeaways': '• Equal treatment under the law\n• Fair distribution of resources and opportunities\n• Protection of minority rights\n• Access to justice for all citizens\n• Transparent and accountable governance', 'trigger_topic': ''},
            {'title': 'Sample: Citizen Participation', 'game_type': 'constitution_challenge', 'trigger_condition': 'always', 'is_enabled': False, 'is_skippable': True, 'display_timing': 'instant', 'principle_explanation': 'In a democracy, citizens have both rights and responsibilities. Active participation through voting, civic engagement, and holding leaders accountable is essential for a healthy democracy.', 'key_takeaways': '• Voting in elections is a civic duty\n• Citizens can participate beyond elections\n• Right to information and transparency\n• Peaceful protest and expression of views\n• Community involvement in decision-making', 'trigger_topic': ''},
            {'title': 'Sample: Checks and Balances', 'game_type': 'constitution_challenge', 'trigger_condition': 'always', 'is_enabled': False, 'is_skippable': True, 'display_timing': 'instant', 'principle_explanation': 'The separation of powers into executive, legislative, and judicial branches prevents any one branch from becoming too powerful. Each branch can check the others, ensuring balanced governance.', 'key_takeaways': '• Executive: Implements and enforces laws\n• Legislative: Makes laws and policies\n• Judicial: Interprets laws and ensures justice\n• Each branch limits the power of others\n• Independent institutions protect democracy', 'trigger_topic': ''},
            {'title': 'Sample: Achieving High Governance Score', 'game_type': 'constitution_challenge', 'trigger_condition': 'score_based', 'is_enabled': False, 'is_skippable': True, 'display_timing': 'instant', 'principle_explanation': 'Congratulations on achieving a high governance score! This reflects your understanding of democratic principles and effective decision-making in governance.', 'key_takeaways': '• Good governance requires balancing different interests\n• Democratic decisions consider long-term consequences\n• Strong institutions protect citizen rights\n• Transparency builds public trust\n• Effective governance serves all citizens', 'min_score': 80, 'max_score': 100, 'trigger_topic': ''},
            {'title': 'Democratic Rights and Good Governance', 'game_type': 'constitution_challenge', 'trigger_condition': 'topic_based', 'is_enabled': True, 'is_skippable': True, 'display_timing': 'instant', 'principle_explanation': 'Democratic governance is built on the foundation of fundamental rights that protect every citizen. When leaders make decisions, they must balance individual freedoms with collective welfare, ensuring that the rights of all citizens are respected and protected.', 'key_takeaways': '• Fundamental rights form the backbone of democracy\n• Good governance protects individual freedoms\n• Leaders must serve all citizens, not just supporters\n• Constitutional principles guide decision-making\n• Balance between rights and responsibilities is key', 'trigger_topic': 'rights'},
            {'title': 'Balancing Individual Rights and Social Harmony', 'game_type': 'constitution_challenge', 'trigger_condition': 'topic_based', 'is_enabled': True, 'is_skippable': True, 'display_timing': 'instant', 'principle_explanation': "In democratic societies, individual rights must be balanced with the need for social harmony and collective good. This doesn't mean suppressing individual freedoms, but finding ways to ensure that everyone's rights are protected while maintaining peace and order in society.", 'key_takeaways': '• Individual rights are not absolute but have reasonable limits\n• Social harmony requires respect for diversity\n• Constitutional framework provides balance\n• Peaceful resolution of conflicts protects democracy\n• Inclusive policies benefit the entire society', 'trigger_topic': 'social_issues'},
        ]
        
        synced_count = 0
        updated_count = 0
        
        for module_data in modules_data:
            title = module_data['title']
            
            # Check if module already exists
            existing_module = GameLearningModule.objects.filter(title=title).first()
            
            if existing_module:
                # Update existing module
                for field, value in module_data.items():
                    setattr(existing_module, field, value)
                
                existing_module.save()
                updated_count += 1
                self.stdout.write(f"✅ Updated: {title[:50]}...")
                
            else:
                # Create new module
                try:
                    new_module = GameLearningModule.objects.create(**module_data)
                    synced_count += 1
                    self.stdout.write(f"✅ Created: {title[:50]}...")
                    
                except Exception as e:
                    self.stdout.write(f"❌ Failed to create {title[:30]}...: {e}")
        
        self.stdout.write(f"\n=== SYNC COMPLETE ===")
        self.stdout.write(f"Created: {synced_count} modules")
        self.stdout.write(f"Updated: {updated_count} modules")
        self.stdout.write(f"Total in database: {GameLearningModule.objects.count()}")
        
        # Show enabled modules
        enabled_modules = GameLearningModule.objects.filter(is_enabled=True)
        self.stdout.write(f"Enabled modules: {enabled_modules.count()}")
        for module in enabled_modules:
            self.stdout.write(f"  ✅ {module.title}")