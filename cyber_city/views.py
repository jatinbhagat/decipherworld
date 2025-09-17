
from django.shortcuts import get_object_or_404, render, redirect
from django.http import JsonResponse
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from django.urls import reverse
from games.base.views import BaseGameSessionView, BaseGameActionView, QuickGameView
from .models import CyberCitySession, CyberCityPlayer, SecurityChallenge, PlayerChallenge, CyberBadge, CyberbullyChallenge, PlayerCyberbullyChallenge
from .plugin import CyberCityProtectionSquadPlugin

class CyberCityGameView(BaseGameSessionView):
    """Main game view for Cyber City Protection Squad - Mission Hub"""
    
    template_name = 'cyber_security/mission_hub.html'
    session_model = CyberCitySession
    player_model = CyberCityPlayer
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        session_code = kwargs.get('session_code')
        
        if session_code:
            session = self.get_session(session_code)
            player = self.get_player(session)
            
            context.update({
                'session': session,
                'player': player,
            })
        
        return context

class PasswordFortressView(BaseGameSessionView):
    """Mission 1: Password Fortress game view"""
    
    template_name = 'cyber_security/game.html'
    session_model = CyberCitySession
    player_model = CyberCityPlayer
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        session_code = kwargs.get('session_code')
        
        if session_code:
            session = self.get_session(session_code)
            player = self.get_player(session)
            
            # Get current challenge
            current_challenge = None
            if player and player.current_challenge <= 5:
                try:
                    current_challenge = SecurityChallenge.objects.get(
                        challenge_number=player.current_challenge
                    )
                except SecurityChallenge.DoesNotExist:
                    pass
            
            # Calculate progress percentage
            challenges_completed = player.challenges_completed if player else 0
            progress_percentage = (challenges_completed * 20) if challenges_completed else 0
            
            context.update({
                'session': session,
                'player': player,
                'current_challenge': current_challenge,
                'mission_stage': session.mission_stage if session else 'intro',
                'city_security_level': session.city_security_level if session else 0,
                'challenges_completed': challenges_completed,
                'progress_percentage': progress_percentage,
                'total_challenges': 5,
                'badges_earned': player.badges_earned if player else [],
            })
        
        return context

class CyberbullyCrisisView(BaseGameSessionView):
    """Mission 2: Cyberbully Crisis game view"""
    
    template_name = 'cyber_security/cyberbully_crisis.html'
    session_model = CyberCitySession
    player_model = CyberCityPlayer
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        session_code = kwargs.get('session_code')
        
        if session_code:
            session = self.get_session(session_code)
            player = self.get_player(session)
            
            # Get current cyberbully challenge
            current_challenge = None
            if player and player.cyberbully_current_challenge <= 5:
                try:
                    current_challenge = CyberbullyChallenge.objects.get(
                        challenge_number=player.cyberbully_current_challenge
                    )
                except CyberbullyChallenge.DoesNotExist:
                    pass
            
            context.update({
                'session': session,
                'player': player,
                'current_challenge': current_challenge,
            })
        
        return context

class CyberCityAvatarView(BaseGameSessionView):
    """Avatar customization view"""
    
    template_name = 'cyber_security/avatar.html'
    session_model = CyberCitySession
    player_model = CyberCityPlayer
    
    def post(self, request, session_code):
        """Handle avatar creation"""
        session = self.get_session(session_code)
        
        # Get form data
        hero_nickname = request.POST.get('hero_nickname', '').strip()
        suit_style = request.POST.get('suit_style', 'neon_knight')
        suit_color = request.POST.get('suit_color', '#00FFFF')
        
        if not hero_nickname:
            messages.error(request, 'Please enter a hero nickname!')
            return render(request, self.template_name, {'session': session})
        
        # Create player
        player = CyberCityPlayer.objects.create(
            session=session,
            player_name=hero_nickname,
            hero_nickname=hero_nickname,
            suit_style=suit_style,
            suit_color=suit_color,
            player_session_id=self.ensure_player_session()
        )
        
        # Store player ID in session
        request.session['player_id'] = player.id
        
        # Update session stage
        session.mission_stage = 'mission_brief'
        session.save()
        
        messages.success(request, f'Welcome to the Squad, {hero_nickname}!')
        return redirect('cyber_city:game', session_code=session_code)

@method_decorator(csrf_exempt, name='dispatch')
class CyberCityActionAPI(BaseGameActionView):
    """API for processing Cyber City Protection Squad challenge answers"""
    
    session_model = CyberCitySession
    player_model = CyberCityPlayer
    
    def process_game_action(self, session, player, action_data):
        """Process cybersecurity challenge answers"""
        
        action_type = action_data.get('action_type')
        
        if action_type == 'submit_answer':
            return self._process_challenge_answer(session, player, action_data)
        elif action_type == 'start_mission':
            return self._start_mission(session, player)
        elif action_type == 'start_cyberbully_mission':
            return self._start_cyberbully_mission(session, player)
        elif action_type == 'submit_cyberbully_answer':
            return self._process_cyberbully_answer(session, player, action_data)
        else:
            raise ValueError(f"Unknown action type: {action_type}")
    
    def _process_challenge_answer(self, session, player, action_data):
        """Process a challenge answer submission"""
        challenge_id = action_data.get('challenge_id')
        answer = action_data.get('answer')
        time_taken = action_data.get('time_taken', 30)
        
        try:
            challenge = SecurityChallenge.objects.get(id=challenge_id)
        except SecurityChallenge.DoesNotExist:
            return {'error': 'Challenge not found'}
        
        # Check if player already answered this challenge
        existing_response = PlayerChallenge.objects.filter(
            player=player, challenge=challenge
        ).first()
        
        if existing_response:
            return {'error': 'Challenge already completed'}
        
        # Check if answer is correct
        is_correct = answer.upper() == challenge.correct_answer
        points_earned = 100 if is_correct else 0
        
        # Create player challenge response
        PlayerChallenge.objects.create(
            player=player,
            challenge=challenge,
            answer_given=answer.upper(),
            is_correct=is_correct,
            points_earned=points_earned,
            time_taken=time_taken
        )
        
        # Update player stats
        if is_correct:
            player.correct_answers += 1
            player.challenges_completed += 1
            player.current_challenge += 1
        else:
            player.wrong_answers += 1
        
        player.total_score += points_earned
        player.save()
        
        # Check for badge unlocks
        badges_earned = self._check_badge_unlocks(player)
        
        # Update mission progress
        if player.challenges_completed >= 5:
            session.mission_stage = 'completed'
            session.city_security_level = 100
            session.save()
        
        return {
            'action_result': 'answer_correct' if is_correct else 'answer_incorrect',
            'is_correct': is_correct,
            'points_earned': points_earned,
            'new_score': player.total_score,
            'explanation': challenge.explanation,
            'tessa_tip': challenge.tessa_tip,
            'badges_earned': badges_earned,
            'mission_complete': player.challenges_completed >= 5
        }
    
    def _start_mission(self, session, player):
        """Start the password fortress mission"""
        session.mission_stage = 'in_progress'
        session.save()
        
        return {
            'action_result': 'mission_started',
            'mission_stage': 'in_progress'
        }
    
    def _start_cyberbully_mission(self, session, player):
        """Start the cyberbully crisis mission"""
        # Ensure player has completed Mission 1
        if player.challenges_completed < 5:
            return {'error': 'Must complete Password Fortress mission first'}
        
        # Set cyberbully mission as started
        if player.cyberbully_current_challenge == 1 and player.cyberbully_challenges_completed == 0:
            return {
                'action_result': 'mission_started',
                'mission_stage': 'cyberbully_in_progress'
            }
        
        return {
            'action_result': 'mission_started',
            'mission_stage': 'cyberbully_in_progress'
        }
    
    def _process_cyberbully_answer(self, session, player, action_data):
        """Process a cyberbully challenge answer submission"""
        challenge_id = action_data.get('challenge_id')
        answer = action_data.get('answer')
        time_taken = action_data.get('time_taken', 30)
        
        try:
            challenge = CyberbullyChallenge.objects.get(id=challenge_id)
        except CyberbullyChallenge.DoesNotExist:
            return {'error': 'Challenge not found'}
        
        # Check if player already answered this challenge
        existing_response = PlayerCyberbullyChallenge.objects.filter(
            player=player, challenge=challenge
        ).first()
        
        if existing_response:
            return {'error': 'Challenge already completed'}
        
        # Check if answer is correct (should identify the bully message)
        is_correct = answer.upper() == challenge.correct_answer
        points_earned = 100 if is_correct else 0
        
        # Create player challenge response
        PlayerCyberbullyChallenge.objects.create(
            player=player,
            challenge=challenge,
            answer_given=answer.upper(),
            is_correct=is_correct,
            points_earned=points_earned,
            time_taken=time_taken
        )
        
        # Update player stats
        if is_correct:
            player.correct_answers += 1
            player.cyberbully_challenges_completed += 1
            player.cyberbully_current_challenge += 1
        else:
            player.wrong_answers += 1
        
        player.total_score += points_earned
        player.save()
        
        # Check for badge unlocks
        badges_earned = self._check_cyberbully_badge_unlocks(player)
        
        # Update mission progress
        if player.cyberbully_challenges_completed >= 5:
            if 'cyberbully_crisis' not in player.missions_completed:
                player.missions_completed.append('cyberbully_crisis')
                player.save()
        
        return {
            'action_result': 'cyberbully_answer_correct' if is_correct else 'cyberbully_answer_incorrect',
            'is_correct': is_correct,
            'points_earned': points_earned,
            'new_score': player.total_score,
            'correct_answers': player.correct_answers,
            'explanation': challenge.explanation,
            'mentor_tip': challenge.mentor_tip,
            'mentor_voice_text': challenge.mentor_voice_text,
            'badges_earned': badges_earned,
            'mission_complete': player.cyberbully_challenges_completed >= 5
        }
    
    def _check_cyberbully_badge_unlocks(self, player):
        """Check if player unlocked any new cyberbully badges"""
        new_badges = []
        
        # Kindness Guardian Badge
        if player.cyberbully_challenges_completed >= 3:
            if 'kindness_guardian' not in player.badges_earned:
                player.badges_earned.append('kindness_guardian')
                new_badges.append('💖 Kindness Guardian')
        
        # Perfect Reporting Badge
        cyberbully_correct = PlayerCyberbullyChallenge.objects.filter(
            player=player, is_correct=True
        ).count()
        cyberbully_total = PlayerCyberbullyChallenge.objects.filter(
            player=player
        ).count()
        
        if cyberbully_correct >= 5 and cyberbully_total == cyberbully_correct:
            if 'perfect_reporter' not in player.badges_earned:
                player.badges_earned.append('perfect_reporter')
                new_badges.append('🎯 Perfect Reporter')
        
        # Mission Complete Badge
        if player.cyberbully_challenges_completed >= 5:
            if 'cyber_street_hero' not in player.badges_earned:
                player.badges_earned.append('cyber_street_hero')
                new_badges.append('🦸‍♀️ Cyber Street Hero')
        
        if new_badges:
            player.save()
        
        return new_badges
    
    def _check_badge_unlocks(self, player):
        """Check if player unlocked any new badges"""
        new_badges = []
        
        # Perfect Score Badge
        if player.correct_answers >= 5 and player.wrong_answers == 0:
            if 'perfect_defender' not in player.badges_earned:
                player.badges_earned.append('perfect_defender')
                new_badges.append('🛡️ Perfect Defender')
        
        # Speed Badge
        if player.challenges_completed >= 3:
            if 'cyber_speedster' not in player.badges_earned:
                player.badges_earned.append('cyber_speedster')
                new_badges.append('⚡ Cyber Speedster')
        
        # Mission Complete Badge
        if player.challenges_completed >= 5:
            if 'password_master' not in player.badges_earned:
                player.badges_earned.append('password_master')
                new_badges.append('🔐 Password Master')
        
        if new_badges:
            player.save()
        
        return new_badges

class CyberCityMissionHubView(TemplateView):
    """Mission Selection Hub - No session required"""
    template_name = 'cyber_security/mission_hub.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'page_title': 'Cyber City Protection Squad - Choose Your Mission',
            'page_description': 'Select your cybersecurity mission and start protecting Cyber City from digital threats!',
        })
        return context

class CyberCityQuickGameView(QuickGameView):
    """Quick game creation for Cyber City Protection Squad"""
    
    session_model = CyberCitySession
    player_model = CyberCityPlayer
    template_name = 'cyber_security/quick_game.html'
    game_plugin_class = CyberCityProtectionSquadPlugin
    
    def get_success_url(self):
        """Redirect to appropriate mission based on URL parameter"""
        mission = self.request.GET.get('mission', 'password_fortress')
        session_code = self.object.session_code
        
        if mission == 'cyberbully_crisis':
            return reverse('cyber_city:cyberbully_crisis', kwargs={'session_code': session_code})
        else:
            return reverse('cyber_city:password_fortress', kwargs={'session_code': session_code})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Check if session_code is provided in URL kwargs (for existing sessions)
        session_code = kwargs.get('session_code')
        if session_code:
            context['session_code'] = session_code
        
        # Add mission selection context
        mission = self.request.GET.get('mission', 'password_fortress')
        context['selected_mission'] = mission
        
        return context
    
    def post(self, request):
        """Handle quick game creation"""
        # Create a new game session
        game_config = self.get_game_config()
        session = self.create_game_session(game_config)
        
        # Redirect to the game page
        return redirect('cyber_city:game', session_code=session.session_code)
