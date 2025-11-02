"""
Django management command to setup simplified Design Thinking game configurations
Creates default game, missions, and input schemas for simplified student-driven sessions
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from group_learning.models import (
    DesignThinkingGame, DesignMission, Game, LearningObjective
)


class Command(BaseCommand):
    help = 'Setup simplified Design Thinking game with auto-progression'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--game-name',
            type=str,
            default='Simplified Classroom Innovation Challenge',
            help='Name for the simplified Design Thinking game'
        )
        parser.add_argument(
            '--overwrite',
            action='store_true',
            help='Overwrite existing game configuration'
        )
    
    def handle(self, *args, **options):
        game_name = options['game_name']
        overwrite = options['overwrite']
        
        self.stdout.write(
            self.style.SUCCESS(f'Setting up simplified Design Thinking game: {game_name}')
        )
        
        try:
            with transaction.atomic():
                # Create or get the simplified game
                game = self._create_simplified_game(game_name, overwrite)
                
                # Create simplified missions with input schemas
                missions = self._create_simplified_missions(game, overwrite)
                
                # Create learning objectives
                self._create_learning_objectives(game)
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✅ Successfully created simplified Design Thinking game with {len(missions)} missions'
                    )
                )
                self.stdout.write(f'Game ID: {game.id}')
                self.stdout.write(f'Auto-progression: {game.auto_advance_enabled}')
                self.stdout.write(f'Completion threshold: {game.completion_threshold_percentage}%')
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error setting up game: {str(e)}')
            )
            raise
    
    def _create_simplified_game(self, game_name, overwrite):
        """Create the simplified Design Thinking game"""
        try:
            game = DesignThinkingGame.objects.get(title=game_name)
            if not overwrite:
                self.stdout.write(
                    self.style.WARNING(f'Game "{game_name}" already exists. Use --overwrite to replace.')
                )
                return game
            else:
                self.stdout.write(f'Overwriting existing game: {game_name}')
        except DesignThinkingGame.DoesNotExist:
            pass
        
        # Create or update the game
        game, created = DesignThinkingGame.objects.update_or_create(
            title=game_name,
            defaults={
                'subtitle': 'Student-driven innovation with auto-progression',
                'game_type': 'community_building',
                'description': 'Simplified Design Thinking process where students work through innovation challenges with minimal teacher intervention and automatic phase progression.',
                'context': 'Educational innovation focused on classroom improvements through simplified design thinking methodology.',
                'min_players': 2,
                'max_players': 30,
                'estimated_duration': 45,  # 45 minutes total
                'target_age_min': 14,
                'target_age_max': 18,
                'difficulty_level': 1,  # Beginner
                'introduction_text': 'Welcome to the Simplified Classroom Innovation Challenge! Work with your team to identify problems in your classroom and design simple solutions. Each phase requires quick, focused inputs that automatically advance when your team is ready.',
                
                # Simplified auto-progression settings
                'auto_advance_enabled': True,
                'completion_threshold_percentage': 100,  # All team members must complete
                'phase_transition_delay': 3,  # 3 seconds countdown
                
                # Simplified scoring settings
                'enable_teacher_scoring': True,
                'scoring_system': 'abc',  # A/B/C letter grades
                
                'is_active': True
            }
        )
        
        action = "Created" if created else "Updated"
        self.stdout.write(f'✅ {action} simplified Design Thinking game: {game.title}')
        return game
    
    def _create_simplified_missions(self, game, overwrite):
        """Create simplified missions with predefined input schemas"""
        missions_config = [
            {
                'mission_type': 'kickoff',
                'order': 1,
                'title': 'Welcome & Team Formation',
                'description': 'Quick team introduction and goal setting',
                'instructions': 'Introduce yourselves and set your team mission for improving classroom learning.',
                'estimated_duration': 5,
                'input_schema': {
                    'inputs': [
                        {
                            'type': 'text_short',
                            'label': 'Your name:',
                            'required': True,
                            'max_length': 30
                        }
                    ]
                },
                'requires_all_team_members': True,
                'allow_optional_upload': False
            },
            {
                'mission_type': 'empathy',
                'order': 2,
                'title': 'Understanding Student Challenges',
                'description': 'Identify what frustrates students most in classrooms',
                'instructions': 'Think about classroom challenges from a student perspective. What makes learning difficult?',
                'estimated_duration': 10,
                'input_schema': {
                    'inputs': [
                        {
                            'type': 'radio',
                            'label': 'What frustrates students most in classrooms?',
                            'required': True,
                            'options': [
                                'Boring lessons and lectures',
                                'Too much homework and pressure',
                                'Difficulty understanding concepts',
                                'Not enough hands-on activities'
                            ]
                        },
                        {
                            'type': 'radio',
                            'label': 'Who struggles most with learning?',
                            'required': True,
                            'options': [
                                'Students who learn differently',
                                'Students who are shy or quiet',
                                'Students who fall behind',
                                'Students who get distracted easily'
                            ]
                        }
                    ]
                },
                'requires_all_team_members': True,
                'allow_optional_upload': False
            },
            {
                'mission_type': 'define',
                'order': 3,
                'title': 'Define the Problem',
                'description': 'Create a clear problem statement based on your observations',
                'instructions': 'Based on your empathy research, define the specific problem you want to solve.',
                'estimated_duration': 10,
                'input_schema': {
                    'inputs': [
                        {
                            'type': 'dropdown',
                            'label': 'Problem category:',
                            'required': True,
                            'options': [
                                'Student engagement',
                                'Learning differences',
                                'Teacher-student communication',
                                'Classroom environment',
                                'Study habits and motivation'
                            ]
                        },
                        {
                            'type': 'text_short',
                            'label': 'Problem statement (50 characters max):',
                            'required': True,
                            'max_length': 50,
                            'placeholder': 'Students need...'
                        }
                    ]
                },
                'requires_all_team_members': True,
                'allow_optional_upload': False
            },
            {
                'mission_type': 'ideate',
                'order': 4,
                'title': '💡 IDEATE — Think of Awesome Ideas!',
                'description': 'Turn your "How Might We" question into creative solutions',
                'instructions': 'Create three different ideas to solve your problem. Think wild, creative, and fun!',
                'estimated_duration': 15,
                'input_schema': {
                    'inputs': [
                        {
                            'type': 'text_short',
                            'label': '🧠 Idea 1 — What\'s your first solution?',
                            'required': True,
                            'max_length': 100,
                            'placeholder': 'Type your first idea...'
                        },
                        {
                            'type': 'text_short', 
                            'label': '🚀 Idea 2 — What\'s a wilder or cooler version?',
                            'required': True,
                            'max_length': 100,
                            'placeholder': 'Think outside the box...'
                        },
                        {
                            'type': 'text_short',
                            'label': '🎨 Idea 3 — What\'s something totally different?',
                            'required': True,
                            'max_length': 100,
                            'placeholder': 'Try a completely new approach...'
                        },
                        {
                            'type': 'radio',
                            'label': '🎯 Pick your favorite idea:',
                            'required': True,
                            'options': ['Idea 1', 'Idea 2', 'Idea 3']
                        }
                    ]
                },
                'requires_all_team_members': True,
                'allow_optional_upload': False
            },
            {
                'mission_type': 'prototype',
                'order': 5,
                'title': '🛠️ PROTOTYPE — Make It Real!',
                'description': 'Turn your favorite idea into something you can explain',
                'instructions': 'Describe how your idea will work. Focus on what people will see, do, and experience.',
                'estimated_duration': 15,
                'input_schema': {
                    'inputs': [
                        {
                            'type': 'text_medium',
                            'label': '🏗️ Describe your prototype (how it works):',
                            'required': True,
                            'max_length': 300,
                            'placeholder': 'Our solution works by... Students will be able to... The teacher can... When someone uses this, they will...'
                        },
                        {
                            'type': 'checkbox',
                            'label': 'Prototype completion:',
                            'required': True,
                            'options': ['✅ My prototype is ready for presentation']
                        }
                    ]
                },
                'requires_all_team_members': True,
                'allow_optional_upload': True
            }
        ]
        
        missions = []
        for mission_config in missions_config:
            mission, created = DesignMission.objects.update_or_create(
                game=game,
                mission_type=mission_config['mission_type'],
                defaults=mission_config
            )
            
            action = "Created" if created else "Updated"
            self.stdout.write(f'  ✅ {action} mission: {mission.title}')
            missions.append(mission)
        
        return missions
    
    def _create_learning_objectives(self, game):
        """Create learning objectives for the simplified game"""
        objectives_data = [
            {
                'title': 'Collaborative Problem Solving',
                'objective_type': 'collaboration',
                'description': 'Students work together to identify and solve classroom challenges through structured teamwork.'
            },
            {
                'title': 'Empathy and Perspective Taking',
                'objective_type': 'empathy',
                'description': 'Students develop understanding of different learning needs and challenges faced by their peers.'
            },
            {
                'title': 'Creative Solution Generation',
                'objective_type': 'critical_thinking',
                'description': 'Students practice generating multiple creative solutions to identified problems.'
            },
            {
                'title': 'Problem Definition Skills',
                'objective_type': 'skills',
                'description': 'Students learn to clearly define problems based on observations and research.'
            }
        ]
        
        for obj_data in objectives_data:
            objective, created = LearningObjective.objects.get_or_create(
                title=obj_data['title'],
                defaults=obj_data
            )
            
            if created:
                self.stdout.write(f'  ✅ Created learning objective: {objective.title}')
            
            # Link to game
            game.learning_objectives.add(objective)
        
        self.stdout.write(f'✅ Linked {game.learning_objectives.count()} learning objectives to game')