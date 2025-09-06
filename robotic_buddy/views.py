from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView, ListView, CreateView, DetailView
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.urls import reverse_lazy
import json
import uuid
import random

from .models import RoboticBuddy, GameActivity, TrainingSession, TrainingExample, BuddyAchievement


class GameHomeView(TemplateView):
    """
    Main entry point for the Robotic Buddy game
    """
    template_name = 'robotic_buddy/game_home.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Check if user has an existing buddy (via session)
        session_id = self.request.session.get('buddy_session_id')
        buddy = None
        
        if session_id:
            try:
                buddy = RoboticBuddy.objects.get(session_id=session_id)
            except RoboticBuddy.DoesNotExist:
                pass
        
        context.update({
            'buddy': buddy,
            'has_buddy': buddy is not None,
            'page_title': 'Meet Your AI Buddy!',
            'available_activities': GameActivity.objects.filter(is_active=True)[:3]
        })
        return context


class CreateBuddyView(TemplateView):
    """
    Buddy creation and customization page
    """
    template_name = 'robotic_buddy/create_buddy.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'personalities': RoboticBuddy.PERSONALITY_CHOICES,
            'colors': RoboticBuddy.COLOR_CHOICES,
            'page_title': 'Create Your AI Buddy'
        })
        return context
    
    def post(self, request, *args, **kwargs):
        """Handle buddy creation"""
        try:
            # Generate unique session ID
            session_id = str(uuid.uuid4())
            
            # Create the buddy
            buddy = RoboticBuddy.objects.create(
                name=request.POST.get('name', 'Buddy')[:50],
                session_id=session_id,
                personality=request.POST.get('personality', 'cheerful'),
                primary_color=request.POST.get('primary_color', 'blue'),
                secondary_color=request.POST.get('secondary_color', 'green')
            )
            
            # Store session ID for future reference
            request.session['buddy_session_id'] = session_id
            
            messages.success(request, f'🎉 Meet {buddy.name}! Your AI buddy is ready to learn!')
            return redirect('robotic_buddy:my_buddy')
            
        except Exception as e:
            messages.error(request, f'Error creating buddy: {str(e)}')
            return self.get(request, *args, **kwargs)


class MyBuddyView(TemplateView):
    """
    Main buddy dashboard showing progress and available activities
    """
    template_name = 'robotic_buddy/my_buddy.html'
    
    def get(self, request, *args, **kwargs):
        # Ensure user has a buddy
        session_id = request.session.get('buddy_session_id')
        if not session_id:
            return redirect('robotic_buddy:create_buddy')
        
        try:
            self.buddy = RoboticBuddy.objects.get(session_id=session_id)
        except RoboticBuddy.DoesNotExist:
            return redirect('robotic_buddy:create_buddy')
            
        return super().get(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get available activities based on buddy level
        available_activities = GameActivity.objects.filter(
            is_active=True,
            required_level__lte=self.buddy.current_level
        )
        
        # Get recent training sessions
        recent_sessions = TrainingSession.objects.filter(
            buddy=self.buddy
        ).select_related('activity')[:5]
        
        context.update({
            'buddy': self.buddy,
            'available_activities': available_activities,
            'recent_sessions': recent_sessions,
            'greeting_message': self.buddy.get_personality_greeting(),
            'page_title': f'{self.buddy.name} - Your AI Buddy'
        })
        return context


class ActivitiesView(ListView):
    """
    List all available training activities
    """
    template_name = 'robotic_buddy/activities.html'
    context_object_name = 'activities'
    
    def get_queryset(self):
        return GameActivity.objects.filter(is_active=True).order_by('required_level', 'name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get buddy if exists
        session_id = self.request.session.get('buddy_session_id')
        buddy = None
        if session_id:
            try:
                buddy = RoboticBuddy.objects.get(session_id=session_id)
            except RoboticBuddy.DoesNotExist:
                pass
        
        context.update({
            'buddy': buddy,
            'page_title': 'Training Activities'
        })
        return context


class ActivityDetailView(DetailView):
    """
    Detailed view of a specific training activity
    """
    model = GameActivity
    template_name = 'robotic_buddy/activity_detail.html'
    context_object_name = 'activity'
    pk_url_kwarg = 'activity_id'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get buddy if exists
        session_id = self.request.session.get('buddy_session_id')
        buddy = None
        can_play = False
        
        if session_id:
            try:
                buddy = RoboticBuddy.objects.get(session_id=session_id)
                can_play = buddy.current_level >= self.object.required_level
            except RoboticBuddy.DoesNotExist:
                pass
        
        context.update({
            'buddy': buddy,
            'can_play': can_play,
            'page_title': self.object.name
        })
        return context


class TrainingSessionView(TemplateView):
    """
    Active training session interface
    """
    template_name = 'robotic_buddy/training_session.html'
    
    def get(self, request, activity_id, *args, **kwargs):
        # Ensure user has a buddy
        session_id = request.session.get('buddy_session_id')
        if not session_id:
            return redirect('robotic_buddy:create_buddy')
        
        try:
            self.buddy = RoboticBuddy.objects.get(session_id=session_id)
            self.activity = get_object_or_404(GameActivity, id=activity_id, is_active=True)
            
            # Check if buddy meets level requirement
            if self.buddy.current_level < self.activity.required_level:
                messages.error(request, f'Your buddy needs to be level {self.activity.required_level} to try this activity!')
                return redirect('robotic_buddy:my_buddy')
                
        except RoboticBuddy.DoesNotExist:
            return redirect('robotic_buddy:create_buddy')
            
        # Create or get current training session
        self.session, created = TrainingSession.objects.get_or_create(
            buddy=self.buddy,
            activity=self.activity,
            status='in_progress',
            defaults={'session_data': {}}
        )
        
        return super().get(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'buddy': self.buddy,
            'activity': self.activity,
            'session': self.session,
            'page_title': f'Training: {self.activity.name}'
        })
        return context


class SimpleGameView(TemplateView):
    """
    Simple click-based animal classification game
    """
    template_name = 'robotic_buddy/simple_game.html'


class ClassificationGameView(TemplateView):
    """
    Our MVP classification training game
    """
    template_name = 'robotic_buddy/classification_game.html'
    
    def get(self, request, *args, **kwargs):
        # Ensure user has a buddy
        session_id = request.session.get('buddy_session_id')
        if not session_id:
            return redirect('robotic_buddy:create_buddy')
        
        try:
            self.buddy = RoboticBuddy.objects.get(session_id=session_id)
        except RoboticBuddy.DoesNotExist:
            return redirect('robotic_buddy:create_buddy')
        
        # Get or create classification activity
        self.activity, created = GameActivity.objects.get_or_create(
            activity_type='classification',
            name='Animal Classification',
            defaults={
                'description': 'Teach your buddy to recognize different animals!',
                'instructions': 'Show your buddy examples by dragging animals into the correct categories. Watch as your buddy learns to classify them!',
                'min_examples_needed': 3,
                'max_examples': 8,
                'experience_reward': 15,
                'required_level': 1
            }
        )
        
        return super().get(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Predefined animals for classification game
        animals = {
            'mammals': ['dog', 'cat', 'elephant', 'lion', 'bear', 'monkey'],
            'birds': ['eagle', 'parrot', 'penguin', 'owl', 'robin', 'flamingo'],
            'fish': ['goldfish', 'shark', 'tuna', 'salmon', 'clownfish', 'whale']
        }
        
        context.update({
            'buddy': self.buddy,
            'activity': self.activity,
            'animals': animals,
            'page_title': f'{self.buddy.name} Learns Animals!'
        })
        return context


class BuddyStatsView(TemplateView):
    """
    Buddy progress and statistics page
    """
    template_name = 'robotic_buddy/buddy_stats.html'
    
    def get(self, request, *args, **kwargs):
        session_id = request.session.get('buddy_session_id')
        if not session_id:
            return redirect('robotic_buddy:create_buddy')
        
        try:
            self.buddy = RoboticBuddy.objects.get(session_id=session_id)
        except RoboticBuddy.DoesNotExist:
            return redirect('robotic_buddy:create_buddy')
            
        return super().get(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get training history
        sessions = TrainingSession.objects.filter(buddy=self.buddy).select_related('activity')
        completed_sessions = sessions.filter(status='completed')
        
        context.update({
            'buddy': self.buddy,
            'completed_sessions': completed_sessions,
            'total_sessions': sessions.count(),
            'average_accuracy': sum(s.accuracy for s in completed_sessions) / max(len(completed_sessions), 1),
            'page_title': f'{self.buddy.name} Stats'
        })
        return context


class AchievementsView(ListView):
    """
    Buddy achievements and milestones
    """
    template_name = 'robotic_buddy/achievements.html'
    context_object_name = 'achievements'
    
    def get_queryset(self):
        session_id = self.request.session.get('buddy_session_id')
        if session_id:
            try:
                buddy = RoboticBuddy.objects.get(session_id=session_id)
                return BuddyAchievement.objects.filter(buddy=buddy)
            except RoboticBuddy.DoesNotExist:
                pass
        return BuddyAchievement.objects.none()


# AJAX API Views
@csrf_exempt
def submit_training_example(request):
    """
    AJAX endpoint for submitting training examples during sessions
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    
    try:
        data = json.loads(request.body)
        
        # Handle session creation
        if data.get('action') == 'create_session':
            session_id = request.session.get('buddy_session_id')
            if not session_id:
                return JsonResponse({'error': 'No buddy session'}, status=400)
            
            buddy = RoboticBuddy.objects.get(session_id=session_id)
            activity = GameActivity.objects.get(id=data['activity_id'])
            
            # Create new training session
            session, created = TrainingSession.objects.get_or_create(
                buddy=buddy,
                activity=activity,
                status='in_progress',
                defaults={'session_data': {}}
            )
            
            return JsonResponse({
                'success': True,
                'session_id': session.id
            })
        
        # Handle training example submission
        session_id = request.session.get('buddy_session_id')
        
        if not session_id:
            return JsonResponse({'error': 'No buddy session'}, status=400)
        
        buddy = RoboticBuddy.objects.get(session_id=session_id)
        session = TrainingSession.objects.get(
            id=data['session_id'],
            buddy=buddy,
            status='in_progress'
        )
        
        # Create training example
        example = TrainingExample.objects.create(
            session=session,
            example_type=data['example_type'],
            label=data['label'],
            data=data.get('data', {}),
            buddy_prediction=data.get('prediction', ''),
            was_correct=data.get('was_correct', False),
            confidence_level=data.get('confidence', 0.5)
        )
        
        # Update session stats
        session.examples_provided += 1
        if data.get('was_correct'):
            session.correct_predictions += 1
        session.total_predictions += 1
        session.save()
        
        return JsonResponse({
            'success': True,
            'examples_count': session.examples_provided,
            'accuracy': session.accuracy
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
def get_buddy_prediction(request):
    """
    AJAX endpoint to get buddy's prediction for a given example
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    
    try:
        data = json.loads(request.body)
        session_id = request.session.get('buddy_session_id')
        
        if not session_id:
            return JsonResponse({'error': 'No buddy session'}, status=400)
        
        buddy = RoboticBuddy.objects.get(session_id=session_id)
        
        # Simulate AI prediction based on buddy's knowledge and level
        # This is where we'd integrate real ML in the future
        prediction = simulate_buddy_prediction(buddy, data)
        
        return JsonResponse(prediction)
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
def complete_training_session(request):
    """
    AJAX endpoint to complete a training session
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    
    try:
        data = json.loads(request.body)
        session_id = request.session.get('buddy_session_id')
        
        if not session_id:
            return JsonResponse({'error': 'No buddy session'}, status=400)
        
        buddy = RoboticBuddy.objects.get(session_id=session_id)
        session = TrainingSession.objects.get(
            id=data['session_id'],
            buddy=buddy,
            status='in_progress'
        )
        
        # Complete the session
        session.complete_session()
        
        return JsonResponse({
            'success': True,
            'experience_earned': session.experience_earned,
            'buddy_level': buddy.current_level,
            'total_xp': buddy.experience_points
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def simulate_buddy_prediction(buddy, example_data):
    """
    Simulate buddy making a prediction based on its current knowledge
    """
    example_type = example_data.get('type', 'classification')
    item = example_data.get('item', '')
    
    if example_type == 'classification' and 'animal' in item.lower():
        # Simple animal classification simulation
        animal_categories = {
            'mammals': ['dog', 'cat', 'elephant', 'lion', 'bear', 'monkey', 'whale'],
            'birds': ['eagle', 'parrot', 'penguin', 'owl', 'robin', 'flamingo'],
            'fish': ['goldfish', 'shark', 'tuna', 'salmon', 'clownfish']
        }
        
        # Check buddy's knowledge base
        knowledge = buddy.knowledge_base.get('animal_classification', {})
        examples_seen = sum(len(animals) for animals in knowledge.values())
        
        # Simulate learning: more examples = better accuracy
        base_accuracy = min(0.9, 0.3 + (examples_seen * 0.1))
        
        # Find correct category
        correct_category = None
        for category, animals in animal_categories.items():
            if item.lower() in animals:
                correct_category = category
                break
        
        # Buddy's prediction logic
        if correct_category and random.random() < base_accuracy:
            prediction = correct_category
            confidence = min(0.95, base_accuracy + random.uniform(0.0, 0.1))
            is_correct = True
        else:
            # Make incorrect guess
            categories = list(animal_categories.keys())
            if correct_category:
                categories.remove(correct_category)
            prediction = random.choice(categories)
            confidence = random.uniform(0.3, 0.6)
            is_correct = False
        
        return {
            'prediction': prediction,
            'confidence': round(confidence, 2),
            'is_correct': is_correct,
            'explanation': f"I think this {item} is a {prediction} because I've learned about {examples_seen} animals so far!"
        }
    
    # Default response
    return {
        'prediction': 'unknown',
        'confidence': 0.5,
        'is_correct': False,
        'explanation': "I'm still learning about this type of thing!"
    }
