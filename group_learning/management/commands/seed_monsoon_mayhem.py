from django.core.management.base import BaseCommand
from group_learning.models import (
    LearningModule, LearningObjective, Game, Role, Scenario, 
    Action, Outcome
)


class Command(BaseCommand):
    help = 'Seeds the database with the Monsoon Mayhem scenario data for Climate Crisis India'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting to seed Monsoon Mayhem scenario...'))
        
        # Create Learning Module
        climate_module, created = LearningModule.objects.get_or_create(
            name="Climate Change & Disaster Management",
            defaults={
                'module_type': 'climate_science',
                'grade_level': 'middle_school',
                'description': 'Understanding climate impacts on Indian communities and sustainable disaster response strategies'
            }
        )
        
        # Create Learning Objectives
        objectives_data = [
            {
                'title': 'Community Resilience Planning',
                'objective_type': 'problem_solving',
                'description': 'Develop skills to create community-level disaster preparedness plans',
                'success_criteria': ['Identify key community roles', 'Prioritize emergency actions', 'Allocate resources effectively']
            },
            {
                'title': 'Environmental Impact Assessment', 
                'objective_type': 'critical_thinking',
                'description': 'Analyze how climate events affect different stakeholders differently',
                'success_criteria': ['Compare impact on various groups', 'Identify root causes', 'Propose sustainable solutions']
            },
            {
                'title': 'Collaborative Decision Making',
                'objective_type': 'collaboration',
                'description': 'Practice making decisions that balance multiple perspectives and constraints',
                'success_criteria': ['Listen to all stakeholders', 'Find win-win solutions', 'Manage resource constraints']
            }
        ]
        
        learning_objectives = []
        for obj_data in objectives_data:
            obj, created = LearningObjective.objects.get_or_create(
                title=obj_data['title'],
                defaults=obj_data
            )
            obj.learning_modules.add(climate_module)
            learning_objectives.append(obj)
            if created:
                self.stdout.write(f'Created learning objective: {obj.title}')
        
        # Create the main game
        game, created = Game.objects.get_or_create(
            title="Climate Crisis India – Monsoon Mayhem",
            defaults={
                'subtitle': 'Navigate the Floods, Save the Village',
                'game_type': 'crisis_management',
                'description': '''Heavy monsoon rains have caused severe flooding in Rajganj village, West Bengal. 
                Critical infrastructure is damaged, families need evacuation, and difficult resource allocation 
                decisions must be made quickly. Players take on key community roles to coordinate emergency 
                response while balancing immediate safety with long-term sustainability.''',
                'context': 'Rural West Bengal during intense monsoon season',
                'introduction_text': '''Welcome to Rajganj village. The monsoon rains have been unprecedented this year. 
                The Teesta River has overflowed, roads are impassable, and 200 families are at risk. As community 
                leaders, you must work together to ensure everyone's safety while planning for long-term resilience.''',
                'min_players': 3,
                'max_players': 4,
                'estimated_duration': 45,
                'difficulty_level': 2,
                'target_age_min': 12,
                'target_age_max': 16
            }
        )
        if created:
            self.stdout.write(f'Created game: {game.title}')
        
        # Add learning objectives to game
        for obj in learning_objectives:
            game.learning_objectives.add(obj)
        
        # Create Roles
        roles_data = [
            {
                'name': 'District Collector',
                'short_name': 'Collector', 
                'description': 'Senior administrative officer responsible for district-wide disaster management coordination',
                'authority_level': 4,
                'expertise_areas': ['Policy Implementation', 'Resource Allocation', 'Inter-agency Coordination', 'Emergency Protocols'],
                'icon': '🏛️',
                'color': '#1e40af'
            },
            {
                'name': 'Local Farmer Leader',
                'short_name': 'Farmer',
                'description': 'Represents agricultural community interests and local ground-level knowledge',
                'authority_level': 2,
                'expertise_areas': ['Local Geography', 'Community Networks', 'Agricultural Practices', 'Traditional Knowledge'],
                'icon': '🌾',
                'color': '#15803d'
            },
            {
                'name': 'Civil Engineer',
                'short_name': 'Engineer',
                'description': 'Technical expert responsible for infrastructure assessment and emergency repairs',
                'authority_level': 3,
                'expertise_areas': ['Infrastructure Assessment', 'Emergency Repairs', 'Technical Solutions', 'Safety Protocols'],
                'icon': '⚙️',
                'color': '#dc2626'
            },
            {
                'name': 'School Principal',
                'short_name': 'Principal',
                'description': 'Educational leader managing school as evacuation center and student welfare',
                'authority_level': 2,
                'expertise_areas': ['Facility Management', 'Community Organization', 'Child Welfare', 'Education Continuity'],
                'icon': '🎓',
                'color': '#7c3aed'
            }
        ]
        
        roles = []
        for role_data in roles_data:
            role, created = Role.objects.get_or_create(
                name=role_data['name'],
                defaults=role_data
            )
            roles.append(role)
            if created:
                self.stdout.write(f'Created role: {role.name}')
        
        collector, farmer, engineer, principal = roles
        
        # Create Main Scenario
        main_scenario, created = Scenario.objects.get_or_create(
            title="Emergency Response Phase",
            game=game,
            defaults={
                'scenario_type': 'crisis_response',
                'order': 1,
                'situation_description': '''It's 6 AM on July 15th. The Teesta River has breached its banks after 72 hours 
                of continuous heavy rainfall. Water levels in Rajganj village are rising rapidly. The main road to Siliguri 
                is completely flooded, cutting off the primary evacuation route. The government school building on higher 
                ground can serve as an evacuation center, but it needs preparation. Mobile networks are intermittent, 
                making coordination challenging. 200 families (approximately 800 people) are in immediate danger, with 
                50 families already stranded on rooftops. Emergency services from Siliguri are delayed due to road conditions.''',
                'urgency_level': 4,
                'location': 'Rajganj Village, West Bengal',
                'cultural_context': '''Traditional Bengali joint family structures mean evacuation decisions affect 
                multiple generations. Many elderly residents are reluctant to leave ancestral homes. Local fishing 
                community has boats that could assist in rescue. Village panchayat system provides existing 
                community organization structure.''',
                'time_limit': 30
            }
        )
        if created:
            self.stdout.write(f'Created scenario: {main_scenario.title}')
        
        # Add required roles and learning objectives to scenario
        for role in roles:
            main_scenario.required_roles.add(role)
        for obj in learning_objectives:
            main_scenario.learning_objectives.add(obj)
        
        # Create Actions for each role
        actions_data = {
            collector: [
                {
                    'title': 'Deploy NDRF Teams',
                    'action_type': 'resource_deployment',
                    'description': 'Request National Disaster Response Force teams for high-risk rescues',
                    'effectiveness_factors': ['Weather conditions', 'Communication systems', 'Transportation access'],
                    'resource_cost': 4,  # Very High Cost
                    'time_required': 4   # Long Term
                },
                {
                    'title': 'Coordinate with State Government',
                    'action_type': 'coordination',
                    'description': 'Escalate to state level for additional resources and helicopter support',
                    'effectiveness_factors': ['Bureaucratic processes', 'Resource availability', 'Political priorities'],
                    'resource_cost': 2,  # Medium Cost
                    'time_required': 3   # Medium Term
                },
                {
                    'title': 'Issue Evacuation Order',
                    'action_type': 'administration',
                    'description': 'Mandate immediate evacuation of all high-risk areas',
                    'effectiveness_factors': ['Community compliance', 'Communication reach', 'Enforcement capacity'],
                    'resource_cost': 1,  # Low Cost
                    'time_required': 2   # Short Term
                }
            ],
            farmer: [
                {
                    'title': 'Mobilize Local Boats',
                    'action_type': 'resource_mobilization',
                    'description': 'Organize fishing community boats for rescue operations',
                    'effectiveness_factors': ['Boat availability', 'Owner cooperation', 'Water conditions'],
                    'resource_cost': 1,  # Low Cost
                    'time_required': 2   # Short Term
                },
                {
                    'title': 'Guide Safe Routes',
                    'action_type': 'information_sharing',
                    'description': 'Use local knowledge to identify safest evacuation paths',
                    'effectiveness_factors': ['Current water levels', 'Local terrain knowledge', 'Weather changes'],
                    'resource_cost': 1,  # Low Cost
                    'time_required': 2   # Short Term
                },
                {
                    'title': 'Convince Elderly Residents',
                    'action_type': 'community_engagement',
                    'description': 'Use community trust to persuade reluctant elderly to evacuate',
                    'effectiveness_factors': ['Relationship strength', 'Cultural sensitivity', 'Family dynamics'],
                    'resource_cost': 1,  # Low Cost
                    'time_required': 3   # Medium Term
                }
            ],
            engineer: [
                {
                    'title': 'Assess Infrastructure Damage',
                    'action_type': 'assessment',
                    'description': 'Evaluate safety of buildings and identify structural risks',
                    'effectiveness_factors': ['Access conditions', 'Equipment availability', 'Expertise level'],
                    'resource_cost': 2,  # Medium Cost
                    'time_required': 4   # Long Term
                },
                {
                    'title': 'Fortify School Building',
                    'action_type': 'construction',
                    'description': 'Strengthen evacuation center and ensure basic facilities',
                    'effectiveness_factors': ['Material availability', 'Worker access', 'Time constraints'],
                    'resource_cost': 3,  # High Cost
                    'time_required': 4   # Long Term
                },
                {
                    'title': 'Restore Communication Systems',
                    'action_type': 'technical_repair',
                    'description': 'Fix cell towers and establish emergency communication',
                    'effectiveness_factors': ['Equipment damage level', 'Power availability', 'Technical expertise'],
                    'resource_cost': 3,  # High Cost
                    'time_required': 3   # Medium Term
                }
            ],
            principal: [
                {
                    'title': 'Prepare Evacuation Center',
                    'action_type': 'facility_management',
                    'description': 'Set up school as temporary shelter with basic amenities',
                    'effectiveness_factors': ['Volunteer availability', 'Supply access', 'Space limitations'],
                    'resource_cost': 2,  # Medium Cost
                    'time_required': 3   # Medium Term
                },
                {
                    'title': 'Organize Community Volunteers',
                    'action_type': 'volunteer_coordination',
                    'description': 'Mobilize teachers, parents and students for relief operations',
                    'effectiveness_factors': ['Community willingness', 'Safety conditions', 'Leadership skills'],
                    'resource_cost': 1,  # Low Cost
                    'time_required': 2   # Short Term
                },
                {
                    'title': 'Manage Child Welfare',
                    'action_type': 'welfare_management',
                    'description': 'Ensure separated children are cared for and families reunited',
                    'effectiveness_factors': ['Documentation systems', 'Staff availability', 'Family cooperation'],
                    'resource_cost': 2,  # Medium Cost
                    'time_required': 4   # Long Term
                }
            ]
        }
        
        created_actions = {}
        for role, actions in actions_data.items():
            created_actions[role] = []
            for action_data in actions:
                action, created = Action.objects.get_or_create(
                    scenario=main_scenario,
                    role=role,
                    title=action_data['title'],
                    defaults=action_data
                )
                created_actions[role].append(action)
                if created:
                    self.stdout.write(f'Created action: {action.title} for {role.short_name}')
        
        # Create Outcomes based on action combinations
        outcomes_data = [
            {
                'title': 'Swift and Coordinated Response',
                'outcome_type': 'success',
                'success_score': 95,
                'description': 'Excellent coordination between all roles leads to efficient evacuation with minimal casualties.',
                'immediate_consequences': ['All 800 people evacuated safely', 'No casualties reported', 'Evacuation center well-organized'],
                'long_term_effects': ['Community trust in authorities strengthened', 'Better disaster preparedness protocols established', 'Regional recognition for effective response'],
                'learning_points': ['Importance of multi-stakeholder coordination', 'Value of local knowledge in crisis response', 'Effective resource allocation under pressure'],
                'reflection_questions': [
                    'How did different perspectives contribute to the solution?',
                    'What role did local knowledge play in the response?',
                    'How can communities prepare better for future disasters?'
                ],
                'required_actions_roles': ['collector', 'farmer', 'engineer', 'principal'],
                'probability_weight': 0.25
            },
            {
                'title': 'Mixed Results with Some Challenges',
                'outcome_type': 'partial_success',
                'success_score': 75,
                'description': 'Good coordination but some delays and resource constraints affect the response.',
                'immediate_consequences': ['Most people evacuated safely', '5 minor injuries during evacuation', 'Evacuation center crowded but functional'],
                'long_term_effects': ['Some community criticism of response delays', 'Lessons learned for future improvements', 'Need for better resource planning identified'],
                'learning_points': ['Impact of resource limitations on crisis response', 'Importance of backup planning', 'Communication challenges in emergencies'],
                'reflection_questions': [
                    'What caused the delays in response?',
                    'How could resource allocation have been improved?',
                    'What backup plans should have been in place?'
                ],
                'required_actions_roles': ['collector', 'farmer'],
                'probability_weight': 0.35
            },
            {
                'title': 'Significant Challenges and Criticism',
                'outcome_type': 'failure',
                'success_score': 45,
                'description': 'Poor coordination and delayed response leads to preventable casualties and community distress.',
                'immediate_consequences': ['2 elderly casualties due to delayed evacuation', 'Evacuation center unprepared and chaotic', 'Community anger and protests'],
                'long_term_effects': ['Loss of public trust in disaster management', 'Media criticism and political consequences', 'Trauma and reduced community resilience'],
                'learning_points': ['Critical importance of preparation and coordination', 'How leadership failures cascade through crisis response', 'Community consequences of poor disaster management'],
                'reflection_questions': [
                    'What were the key failure points in coordination?',
                    'How do leadership decisions affect vulnerable populations?',
                    'What systemic changes are needed to prevent such outcomes?'
                ],
                'required_actions_roles': [],
                'probability_weight': 0.15
            }
        ]
        
        for outcome_data in outcomes_data:
            required_roles = outcome_data.pop('required_actions_roles', [])
            outcome, created = Outcome.objects.get_or_create(
                scenario=main_scenario,
                title=outcome_data['title'],
                defaults=outcome_data
            )
            
            # Add required actions based on roles
            for role_short in required_roles:
                role_obj = next((r for r in roles if r.short_name.lower() == role_short), None)
                if role_obj and role_obj in created_actions:
                    # Add the most relevant action for each role
                    if created_actions[role_obj]:
                        outcome.required_actions.add(created_actions[role_obj][0])
            
            if created:
                self.stdout.write(f'Created outcome: {outcome.title}')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\nSuccessfully seeded Monsoon Mayhem scenario!\n'
                f'- Learning Module: {climate_module.name}\n'
                f'- Learning Objectives: {len(learning_objectives)}\n'
                f'- Game: {game.title}\n'
                f'- Roles: {len(roles)}\n'
                f'- Scenario: {main_scenario.title}\n'
                f'- Actions: {sum(len(actions) for actions in created_actions.values())}\n'
                f'- Outcomes: {len(outcomes_data)}\n'
                f'\nYou can now access the Django admin to view and manage the seeded data!'
            )
        )