#!/usr/bin/env python
"""
Production data sync script for GameLearningModule
Run this in production Django shell: python manage.py shell < sync_gamelearningmodule_production.py
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'decipherworld.settings.production')
django.setup()

from group_learning.models import GameLearningModule, ConstitutionQuestion, ConstitutionOption

def sync_gamelearningmodule_data():
    """Sync GameLearningModule data to production"""
    
    print("=== SYNCING GameLearningModule DATA TO PRODUCTION ===")
    
    # Data to create
    modules_data = [
        {'title': 'Understanding Democracy', 'game_type': 'constitution_challenge', 'trigger_condition': 'topic_based', 'is_enabled': True, 'is_skippable': True, 'display_timing': 'instant', 'principle_explanation': 'Democracy is a form of government where power rests with the people, either directly or through elected representatives. In a democratic system, citizens have the right to participate in decision-making processes that affect their lives.', 'key_takeaways': '• Democracy means "rule by the people"\n• Citizens elect representatives to make decisions\n• Everyone has equal rights and freedoms\n• Majority rule with minority rights protection', 'action_impact_title': 'Impact of Your Decision', 'governance_impact': 'Democratic choices strengthen citizen participation and government accountability.', 'score_reasoning': 'Democratic decisions typically increase governance scores by promoting transparency and public participation.', 'country_state_changes': 'Cities grow stronger with democratic institutions, public squares, and civic engagement.', 'societal_impact': 'Citizens feel more empowered and engaged when their voices are heard in democratic processes.', 'constitution_topic_title': 'Learn from the Indian Constitution', 'constitution_chapter': 'introduction', 'constitution_principle': 'Democratic Governance', 'constitution_explanation': 'The Indian Constitution establishes India as a democratic republic where sovereignty lies with the people. Citizens elect representatives at various levels of government.', 'constitution_article_reference': 'Preamble: "We, the people of India"', 'trigger_topic': 'leadership'},
        {'title': 'Fundamental Rights', 'game_type': 'constitution_challenge', 'trigger_condition': 'topic_based', 'is_enabled': True, 'is_skippable': True, 'display_timing': 'instant', 'principle_explanation': 'Fundamental Rights are basic human rights guaranteed by the Constitution to all citizens. These rights ensure dignity, freedom, and equality for everyone.', 'key_takeaways': '• Right to Equality (Articles 14-18)\n• Right to Freedom (Articles 19-22)\n• Right against Exploitation (Articles 23-24)\n• Right to Freedom of Religion (Articles 25-28)\n• Cultural and Educational Rights (Articles 29-30)\n• Right to Constitutional Remedies (Article 32)', 'action_impact_title': 'Impact of Your Decision', 'governance_impact': 'Protecting fundamental rights builds trust between government and citizens.', 'score_reasoning': 'Upholding rights increases governance scores by ensuring justice and equality.', 'country_state_changes': 'Countries with strong rights protection see economic growth and social harmony.', 'societal_impact': 'Citizens feel secure and free when their fundamental rights are protected.', 'constitution_topic_title': 'Learn from the Indian Constitution', 'constitution_chapter': 'rights_duties', 'constitution_principle': 'Fundamental Rights', 'constitution_explanation': 'Part III of the Indian Constitution (Articles 12-35) guarantees fundamental rights to all citizens, creating a framework for individual liberty and social justice.', 'constitution_article_reference': 'Articles 12-35: Fundamental Rights', 'trigger_topic': 'rights'},
        {'title': 'Justice and Fairness', 'game_type': 'constitution_challenge', 'trigger_condition': 'topic_based', 'is_enabled': True, 'is_skippable': True, 'display_timing': 'instant', 'principle_explanation': 'Justice means treating everyone fairly and equally under the law. A fair justice system protects the innocent, punishes wrongdoers, and ensures due process for all.', 'key_takeaways': '• Equal treatment under the law\n• Independent judiciary\n• Due process and fair trials\n• Rule of law over rule of individuals\n• Access to justice for all citizens', 'action_impact_title': 'Impact of Your Decision', 'governance_impact': 'A fair justice system strengthens public trust in government institutions.', 'score_reasoning': 'Fair judicial decisions increase governance scores by ensuring rule of law.', 'country_state_changes': 'Countries with fair justice systems attract investment and maintain social order.', 'societal_impact': 'People feel secure when they know justice will be served fairly and impartially.', 'constitution_topic_title': 'Learn from the Indian Constitution', 'constitution_chapter': 'government_branches', 'constitution_principle': 'Independent Judiciary', 'constitution_explanation': 'The Indian Constitution establishes an independent judiciary with the Supreme Court at the apex, ensuring justice and upholding constitutional values.', 'constitution_article_reference': 'Articles 124-147: Supreme Court and High Courts', 'trigger_topic': 'justice'},
        {'title': 'Citizen Participation', 'game_type': 'constitution_challenge', 'trigger_condition': 'topic_based', 'is_enabled': True, 'is_skippable': True, 'display_timing': 'instant', 'principle_explanation': 'Citizen participation is the cornerstone of democracy. When citizens actively engage in governance through voting, advocacy, and civic duties, democracy becomes stronger.', 'key_takeaways': '• Voting is both a right and responsibility\n• Citizens can petition government\n• Public participation in policy-making\n• Civic engagement strengthens democracy\n• Informed citizens make better decisions', 'action_impact_title': 'Impact of Your Decision', 'governance_impact': 'Higher citizen participation leads to more responsive and accountable governance.', 'score_reasoning': 'Encouraging participation increases governance scores through better representation.', 'country_state_changes': 'Participatory governance leads to better public services and infrastructure.', 'societal_impact': 'Active citizens create vibrant communities and hold leaders accountable.', 'constitution_topic_title': 'Learn from the Indian Constitution', 'constitution_chapter': 'rights_duties', 'constitution_principle': 'Democratic Participation', 'constitution_explanation': 'The Indian Constitution ensures citizen participation through universal adult suffrage, right to information, and various democratic institutions.', 'constitution_article_reference': 'Article 326: Universal Adult Suffrage', 'trigger_topic': 'participation'},
        {'title': 'Checks and Balances', 'game_type': 'constitution_challenge', 'trigger_condition': 'topic_based', 'is_enabled': True, 'is_skippable': True, 'display_timing': 'instant', 'principle_explanation': 'Checks and balances prevent any single branch of government from becoming too powerful. The executive, legislative, and judicial branches each have powers to check the others.', 'key_takeaways': '• Separation of powers between branches\n• Each branch can check the others\n• Prevents concentration of power\n• Ensures accountability and transparency\n• Protects against tyranny and abuse', 'action_impact_title': 'Impact of Your Decision', 'governance_impact': 'Effective checks and balances prevent corruption and ensure good governance.', 'score_reasoning': 'Strong institutional checks increase governance scores by preventing abuse of power.', 'country_state_changes': 'Countries with effective checks see stable institutions and economic growth.', 'societal_impact': 'Citizens trust government more when power is distributed and accountable.', 'constitution_topic_title': 'Learn from the Indian Constitution', 'constitution_chapter': 'government_branches', 'constitution_principle': 'Separation of Powers', 'constitution_explanation': 'The Indian Constitution divides power among the Executive (President, PM, Cabinet), Legislature (Parliament), and Judiciary (Courts), with each checking the others.', 'constitution_article_reference': 'Articles 52-151: Distribution of powers', 'trigger_topic': 'checks'},
        {'title': 'Achieving High Governance Score', 'game_type': 'constitution_challenge', 'trigger_condition': 'score_based', 'is_enabled': True, 'is_skippable': True, 'display_timing': 'instant', 'principle_explanation': 'Excellent governance requires balancing multiple factors: citizen rights, institutional strength, democratic participation, and effective leadership working together harmoniously.', 'key_takeaways': '• Balanced approach to all governance aspects\n• Strong institutions with public trust\n• Active citizen participation\n• Transparent and accountable leadership\n• Protection of rights with social responsibility', 'action_impact_title': 'Impact of Your Decision', 'governance_impact': 'High governance scores reflect effective democratic institutions and citizen satisfaction.', 'score_reasoning': 'Balanced decisions across all areas create synergistic effects that boost overall governance.', 'country_state_changes': 'High-performing democracies become thriving nations with prosperity and social harmony.', 'societal_impact': 'Citizens in well-governed countries enjoy better quality of life and opportunities.', 'constitution_topic_title': 'Learn from the Indian Constitution', 'constitution_chapter': 'features', 'constitution_principle': 'Good Governance', 'constitution_explanation': 'The Indian Constitution provides a framework for good governance through democratic institutions, fundamental rights, directive principles, and constitutional remedies.', 'constitution_article_reference': 'Entire Constitution: Framework for governance', 'min_score': 15},
        {'title': 'Democratic Rights and Good Governance', 'game_type': 'constitution_challenge', 'trigger_condition': 'always', 'is_enabled': True, 'is_skippable': True, 'display_timing': 'instant', 'principle_explanation': 'Good governance emerges when democratic rights are protected, institutions function effectively, and citizens actively participate in shaping their government.', 'key_takeaways': '• Democratic rights enable citizen participation\n• Good governance requires institutional integrity\n• Transparency and accountability are essential\n• Balance between rights and responsibilities\n• Continuous improvement through feedback', 'action_impact_title': 'Impact of Your Decision', 'governance_impact': 'Strong democratic rights create the foundation for effective governance.', 'score_reasoning': 'Protecting rights while maintaining effective governance creates optimal outcomes.', 'country_state_changes': 'Balanced democracy and governance create prosperous, stable nations.', 'societal_impact': 'Citizens flourish when they have both rights and effective government services.', 'constitution_topic_title': 'Learn from the Indian Constitution', 'constitution_chapter': 'features', 'constitution_principle': 'Democratic Governance', 'constitution_explanation': 'The Indian Constitution establishes a framework where democratic rights and good governance reinforce each other for national development.', 'constitution_article_reference': 'Preamble and Fundamental Rights'},
        {'title': 'Balancing Individual Rights and Social Harmony', 'game_type': 'constitution_challenge', 'trigger_condition': 'topic_based', 'is_enabled': True, 'is_skippable': True, 'display_timing': 'instant', 'principle_explanation': 'A healthy democracy balances individual freedoms with collective welfare. Rights come with responsibilities, and personal liberty must coexist with social order.', 'key_takeaways': '• Individual rights have reasonable restrictions\n• Personal freedom with social responsibility\n• Rights of one person end where others begin\n• Community welfare alongside individual liberty\n• Balance prevents chaos while protecting freedom', 'action_impact_title': 'Impact of Your Decision', 'governance_impact': 'Balanced rights and duties create stable, harmonious governance.', 'score_reasoning': 'Thoughtful balance between freedom and order optimizes governance outcomes.', 'country_state_changes': 'Societies with balanced rights and duties experience sustainable development.', 'societal_impact': 'Citizens enjoy maximum freedom while contributing to collective wellbeing.', 'constitution_topic_title': 'Learn from the Indian Constitution', 'constitution_chapter': 'rights_duties', 'constitution_principle': 'Rights and Duties', 'constitution_explanation': 'The Indian Constitution balances fundamental rights with fundamental duties, ensuring individual liberty while promoting social harmony and national integrity.', 'constitution_article_reference': 'Articles 12-35 (Rights) and Article 51A (Duties)', 'trigger_topic': 'rights'},
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
                if field not in ['trigger_question_id', 'trigger_option_id']:
                    setattr(existing_module, field, value)
            
            # Handle foreign key fields
            if 'trigger_question_id' in module_data:
                try:
                    existing_module.trigger_question_id = module_data['trigger_question_id']
                except:
                    pass  # Ignore if question doesn't exist
            
            if 'trigger_option_id' in module_data:
                try:
                    existing_module.trigger_option_id = module_data['trigger_option_id']
                except:
                    pass  # Ignore if option doesn't exist
            
            existing_module.save()
            updated_count += 1
            print(f"✅ Updated: {title[:50]}...")
            
        else:
            # Create new module
            try:
                # Remove foreign key fields for initial creation
                create_data = {k: v for k, v in module_data.items() 
                              if k not in ['trigger_question_id', 'trigger_option_id']}
                
                new_module = GameLearningModule.objects.create(**create_data)
                
                # Set foreign key fields if they exist
                if 'trigger_question_id' in module_data:
                    try:
                        new_module.trigger_question_id = module_data['trigger_question_id']
                        new_module.save()
                    except:
                        pass
                
                if 'trigger_option_id' in module_data:
                    try:
                        new_module.trigger_option_id = module_data['trigger_option_id']
                        new_module.save()
                    except:
                        pass
                
                synced_count += 1
                print(f"✅ Created: {title[:50]}...")
                
            except Exception as e:
                print(f"❌ Failed to create {title[:30]}...: {e}")
    
    print(f"\n=== SYNC COMPLETE ===")
    print(f"Created: {synced_count} modules")
    print(f"Updated: {updated_count} modules")
    print(f"Total in production: {GameLearningModule.objects.count()}")

if __name__ == "__main__":
    sync_gamelearningmodule_data()
