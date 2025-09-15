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

from .models import RoboticBuddy, GameActivity, TrainingSession, TrainingExample, BuddyAchievement, AIReasoningExplanation


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


class DragDropGameView(TemplateView):
    """
    Drag and drop animal classification game (no database required)
    """
    template_name = 'robotic_buddy/drag_drop_game.html'


class EmotionGameView(TemplateView):
    """
    Emotion recognition training game - teach AI buddy to understand emotions
    """
    template_name = 'robotic_buddy/emotion_game.html'


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
                'min_examples_needed': 16,
                'max_examples': 16,
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


class SessionResultView(TemplateView):
    """
    Dedicated result page showing detailed AI reasoning and training analysis
    """
    template_name = 'robotic_buddy/session_result.html'
    
    def get(self, request, session_id, *args, **kwargs):
        # Ensure user has a buddy
        buddy_session_id = request.session.get('buddy_session_id')
        if not buddy_session_id:
            return redirect('robotic_buddy:create_buddy')
        
        try:
            self.buddy = RoboticBuddy.objects.get(session_id=buddy_session_id)
            self.training_session = get_object_or_404(
                TrainingSession, 
                id=session_id, 
                buddy=self.buddy
            )
        except RoboticBuddy.DoesNotExist:
            return redirect('robotic_buddy:create_buddy')
            
        return super().get(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get all examples from this session
        examples = TrainingExample.objects.filter(
            session=self.training_session
        ).order_by('created_at')
        
        # Analyze training quality
        animal_categories = {
            'mammals': ['dog', 'cat', 'elephant', 'lion', 'bear', 'monkey', 'whale'],
            'birds': ['eagle', 'parrot', 'penguin', 'owl', 'robin', 'flamingo'],
            'fish': ['goldfish', 'shark', 'tuna', 'salmon', 'clownfish']
        }
        
        training_quality = analyze_training_quality(examples, animal_categories)
        
        # Get detailed reasoning for each prediction example
        prediction_examples = examples.filter(
            data__test_mode=True
        ) if examples.filter(data__test_mode=True).exists() else examples.filter(buddy_prediction__isnull=False)
        
        detailed_reasoning = []
        for example in prediction_examples:
            if example.buddy_prediction:
                # Generate reasoning for this specific example
                reasoning = generate_detailed_reasoning(
                    example.label,
                    example.data.get('correct_category') if example.data else None,
                    examples,
                    training_quality,
                    animal_categories
                )
                
                # Create reasoning explanation record
                reasoning_explanation, created = AIReasoningExplanation.objects.get_or_create(
                    session=self.training_session,
                    example=example,
                    defaults={
                        'reasoning_type': 'example_based',
                        'confidence_score': reasoning['confidence'],
                        'confidence_explanation': reasoning['confidence_explanation'],
                        'reasoning_steps': reasoning['reasoning_steps'],
                        'supporting_examples': reasoning['supporting_examples'],
                        'visual_patterns': reasoning['visual_patterns'],
                        'training_quality_score': reasoning['training_quality_score'],
                        'quality_explanation': f"Training quality was {training_quality['overall_score']:.1%} - this directly impacted my prediction accuracy."
                    }
                )
                
                detailed_reasoning.append({
                    'example': example,
                    'reasoning': reasoning_explanation
                })
        
        # Determine if retrain is recommended
        retrain_recommended = training_quality['overall_score'] < 0.6
        
        context.update({
            'buddy': self.buddy,
            'session': self.training_session,
            'examples': examples,
            'training_quality': training_quality,
            'detailed_reasoning': detailed_reasoning,
            'retrain_recommended': retrain_recommended,
            'page_title': f'{self.buddy.name} - Training Results'
        })
        return context


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
        
        # Generate URL for the dedicated result page
        from django.urls import reverse
        result_url = reverse('robotic_buddy:session_result', kwargs={'session_id': session.id})
        
        return JsonResponse({
            'success': True,
            'experience_earned': session.experience_earned,
            'buddy_level': buddy.current_level,
            'total_xp': buddy.experience_points,
            'redirect_url': result_url
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def simulate_buddy_prediction(buddy, example_data, session=None):
    """
    Advanced AI buddy prediction based on training quality and detailed reasoning
    """
    example_type = example_data.get('type', 'classification')
    item = example_data.get('item', '').replace(' animal', '')
    
    if example_type == 'classification':
        # Animal classification with detailed reasoning
        animal_categories = {
            'mammals': ['dog', 'cat', 'elephant', 'lion', 'bear', 'monkey', 'whale'],
            'birds': ['eagle', 'parrot', 'penguin', 'owl', 'robin', 'flamingo'],
            'fish': ['goldfish', 'shark', 'tuna', 'salmon', 'clownfish']
        }
        
        # Get training history for this buddy
        if session:
            training_examples = TrainingExample.objects.filter(
                session__buddy=buddy,
                example_type='classification_item'
            ).order_by('-created_at')
        else:
            training_examples = TrainingExample.objects.filter(
                session__buddy=buddy,
                example_type='classification_item'
            ).order_by('-created_at')[:20]  # Last 20 examples
        
        # Analyze training quality
        training_quality = analyze_training_quality(training_examples, animal_categories)
        
        # Find correct category for the item
        correct_category = None
        for category, animals in animal_categories.items():
            if item.lower() in animals:
                correct_category = category
                break
        
        # Generate detailed reasoning based on training
        reasoning_result = generate_detailed_reasoning(
            item, correct_category, training_examples, training_quality, animal_categories
        )
        
        return reasoning_result
    
    # Default response for non-classification
    return {
        'prediction': 'unknown',
        'confidence': 0.5,
        'is_correct': False,
        'explanation': "I'm still learning about this type of thing!",
        'reasoning_steps': [],
        'supporting_examples': [],
        'visual_patterns': {},
        'training_quality_score': 1.0
    }


def analyze_training_quality(training_examples, animal_categories):
    """
    Analyze the quality of training data provided by the user
    """
    if not training_examples:
        return {
            'overall_score': 0.5,
            'correct_examples': 0,
            'total_examples': 0,
            'category_accuracy': {},
            'consistency_score': 1.0
        }
    
    total_examples = len(training_examples)
    correct_examples = 0
    category_stats = {category: {'correct': 0, 'total': 0} for category in animal_categories.keys()}
    
    for example in training_examples:
        # Check if the user's label was correct
        animal_name = example.label.lower()
        user_category = None
        correct_category = None
        
        # Find what category the user put it in (from session data)
        if hasattr(example, 'data') and example.data:
            user_category = example.data.get('category')
        
        # Find the actual correct category
        for category, animals in animal_categories.items():
            if animal_name in animals:
                correct_category = category
                break
        
        if user_category and correct_category:
            category_stats[user_category]['total'] += 1
            if user_category == correct_category:
                correct_examples += 1
                category_stats[user_category]['correct'] += 1
    
    # Calculate category-wise accuracy
    category_accuracy = {}
    for category, stats in category_stats.items():
        if stats['total'] > 0:
            category_accuracy[category] = stats['correct'] / stats['total']
        else:
            category_accuracy[category] = 1.0
    
    # Overall training quality score
    overall_score = correct_examples / total_examples if total_examples > 0 else 0.5
    
    # Consistency score (how consistent the user was)
    consistency_score = min(category_accuracy.values()) if category_accuracy else 1.0
    
    return {
        'overall_score': overall_score,
        'correct_examples': correct_examples,
        'total_examples': total_examples,
        'category_accuracy': category_accuracy,
        'consistency_score': consistency_score
    }


def generate_detailed_reasoning(item, correct_category, training_examples, training_quality, animal_categories):
    """
    Generate step-by-step reasoning for AI buddy's prediction
    """
    # Base prediction accuracy heavily influenced by training quality
    base_accuracy = 0.3 + (training_quality['overall_score'] * 0.6)  # 30% to 90% based on training quality
    
    # Find similar animals from training
    similar_examples = []
    for example in training_examples:
        if hasattr(example, 'data') and example.data:
            user_category = example.data.get('category')
            if user_category:
                similar_examples.append({
                    'animal': example.label,
                    'category': user_category,
                    'was_correct': example.was_correct
                })
    
    # Generate reasoning steps
    reasoning_steps = []
    supporting_examples = []
    
    # Step 1: Analyze what I've learned
    if training_examples:
        step1 = f"I've been trained on {training_quality['total_examples']} animals, and my trainer got {training_quality['correct_examples']} of them right ({training_quality['overall_score']:.1%} accuracy)."
        reasoning_steps.append({
            'step': 1,
            'title': 'Analyzing my training data',
            'description': step1,
            'confidence_impact': training_quality['overall_score']
        })
    
    # Step 2: Look for similar animals
    category_examples = {}
    for example in similar_examples[:10]:  # Recent 10 examples
        category = example['category']
        if category not in category_examples:
            category_examples[category] = []
        category_examples[category].append(example)
        supporting_examples.append(example)
    
    if category_examples:
        most_common_category = max(category_examples.keys(), key=lambda k: len(category_examples[k]))
        step2 = f"Looking at animals I've learned, I see {len(category_examples.get(most_common_category, []))} examples in the '{most_common_category}' category."
        reasoning_steps.append({
            'step': 2,
            'title': 'Finding similar patterns',
            'description': step2,
            'examples': category_examples.get(most_common_category, [])[:3]
        })
    
    # Step 3: Make prediction based on training quality
    if correct_category and random.random() < base_accuracy:
        # Correct prediction
        prediction = correct_category
        confidence = min(0.95, base_accuracy + random.uniform(0.0, 0.1))
        is_correct = True
        
        step3 = f"Based on my training, I'm {confidence:.1%} confident that {item} belongs in the '{prediction}' category."
        if training_quality['overall_score'] < 0.5:
            step3 += " However, my training data had some inconsistencies, so I might be wrong."
    else:
        # Incorrect prediction (due to poor training)
        categories = list(animal_categories.keys())
        if correct_category and correct_category in categories:
            categories.remove(correct_category)
        prediction = random.choice(categories) if categories else 'unknown'
        confidence = random.uniform(0.3, 0.6)
        is_correct = False
        
        step3 = f"My training data was inconsistent ({training_quality['overall_score']:.1%} accuracy), so I'm making my best guess: {item} is a '{prediction}', but I'm only {confidence:.1%} confident."
    
    reasoning_steps.append({
        'step': 3,
        'title': 'Making my prediction',
        'description': step3,
        'prediction': prediction,
        'confidence': confidence
    })
    
    # Confidence explanation
    confidence_explanation = f"My confidence is {confidence:.1%} because my training data was {training_quality['overall_score']:.1%} accurate. "
    if training_quality['overall_score'] > 0.8:
        confidence_explanation += "My trainer did an excellent job teaching me!"
    elif training_quality['overall_score'] > 0.6:
        confidence_explanation += "My trainer did a good job, but there were some mistakes in my training."
    else:
        confidence_explanation += "My training had many errors, so I'm not very confident in my predictions."
    
    # Visual patterns (simulated)
    visual_patterns = {
        'size': 'medium' if 'elephant' not in item else 'large',
        'habitat': 'land' if prediction == 'mammals' else ('air' if prediction == 'birds' else 'water'),
        'features': {
            'mammals': ['fur', 'warm-blooded', 'live birth'],
            'birds': ['feathers', 'wings', 'lay eggs'],
            'fish': ['scales', 'gills', 'swim']
        }.get(prediction, [])
    }
    
    return {
        'prediction': prediction,
        'confidence': round(confidence, 2),
        'is_correct': is_correct,
        'explanation': f"Based on my training, I think {item} is a {prediction}!",
        'reasoning_steps': reasoning_steps,
        'supporting_examples': supporting_examples,
        'visual_patterns': visual_patterns,
        'training_quality_score': training_quality['overall_score'],
        'confidence_explanation': confidence_explanation
    }


class TestingPhaseView(TemplateView):
    """Testing phase where AI demonstrates what it learned"""
    template_name = 'robotic_buddy/testing_phase.html'
    
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
        
        # Get recent training session
        training_session = self.buddy.training_sessions.filter(
            status='training'
        ).order_by('-started_at').first()
        
        if training_session:
            training_examples = training_session.examples.filter(is_training_example=True)
            training_count = training_examples.count()
        else:
            training_count = 0
        
        context.update({
            'buddy': self.buddy,
            'training_count': training_count,
            'page_title': f'Testing {self.buddy.name}\'s Learning'
        })
        return context


class LearningExplanationView(TemplateView):
    """Show how the AI learned step-by-step"""
    template_name = 'robotic_buddy/learning_explanation.html'
    
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
        
        # Get recent training session and examples
        training_session = self.buddy.training_sessions.order_by('-started_at').first()
        
        if training_session:
            training_examples = training_session.examples.filter(is_training_example=True)
            test_examples = training_session.examples.filter(is_training_example=False)
            
            # Calculate visual patterns for learning explanation
            visual_patterns = {
                'total_examples': training_examples.count(),
                'categories_learned': list(set([ex.data.get('category', 'unknown') for ex in training_examples if ex.data])),
                'learning_progression': []
            }
        else:
            training_examples = []
            test_examples = []
            visual_patterns = {'total_examples': 0, 'categories_learned': [], 'learning_progression': []}
        
        context.update({
            'buddy': self.buddy,
            'training_examples': training_examples,
            'test_examples': test_examples,
            'visual_patterns': visual_patterns,
            'page_title': f'How {self.buddy.name} Learned'
        })
        return context
