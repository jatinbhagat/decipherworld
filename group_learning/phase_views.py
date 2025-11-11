# Phase-based Design Thinking Views
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import TemplateView, View
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.urls import reverse

from .models import DesignThinkingSession, DesignTeam, SimplifiedPhaseInput, DesignMission


class BasePhaseView(TemplateView):
    """
    Base view for all Design Thinking phases with common logic
    """
    phase_type = None  # Override in subclasses ('intro', 'empathy', 'define', etc.)
    next_phase = None  # Override in subclasses 
    template_name = None  # Override in subclasses
    
    def dispatch(self, request, *args, **kwargs):
        """Initialize common data and check access permissions"""
        self.session_code = kwargs.get('session_code')
        
        # Get team from session (check cookies/session)
        self.team = self._get_team_from_session(request)
        self.session = get_object_or_404(DesignThinkingSession, session_code=self.session_code)
        
        if not self.team:
            messages.error(request, 'Please join a team first.')
            return redirect('group_learning:simplified_join_session', session_code=self.session_code)
        
        # Check if this phase is already submitted (prevent re-submission)
        if self.is_phase_submitted():
            messages.info(request, f'{self.get_phase_display()} phase already completed.')
            return redirect('group_learning:student_entry', session_code=self.session_code)
            
        # Check if previous phases are completed (strict order)
        if not self.can_access_phase():
            messages.warning(request, 'Please complete previous phases first.')
            return redirect('group_learning:student_entry', session_code=self.session_code)
            
        return super().dispatch(request, *args, **kwargs)
    
    def _get_team_from_session(self, request):
        """Get team from session cookies"""
        team_id = request.session.get(f'team_id_{self.session_code}')
        if team_id:
            try:
                return DesignTeam.objects.get(id=team_id, session__session_code=self.session_code)
            except DesignTeam.DoesNotExist:
                pass
        return None
    
    def is_phase_submitted(self):
        """Check if this phase is already submitted by the team"""
        return SimplifiedPhaseInput.objects.filter(
            team=self.team,
            session=self.session,
            phase_type=self.phase_type
        ).exists()
    
    def can_access_phase(self):
        """Check if previous phases are completed (strict progression)"""
        if self.phase_type == 'intro':
            return True  # Can always access intro
            
        # Define phase order
        phase_order = ['intro', 'empathy', 'define', 'ideate', 'prototype', 'testing']
        current_index = phase_order.index(self.phase_type)
        
        # Check all previous phases are completed
        for i in range(current_index):
            previous_phase = phase_order[i]
            if not SimplifiedPhaseInput.objects.filter(
                team=self.team,
                session=self.session,
                phase_type=previous_phase
            ).exists():
                return False
                
        return True
    
    def get_phase_display(self):
        """Get human-readable phase name"""
        phase_names = {
            'intro': 'Introduction',
            'empathy': 'Empathy',
            'define': 'Define',
            'ideate': 'Ideate', 
            'prototype': 'Prototype',
            'testing': 'Testing'
        }
        return phase_names.get(self.phase_type, self.phase_type.title())
    
    def get_mission_for_phase(self):
        """Get the appropriate mission for this phase type"""
        # Map phase types to mission types
        phase_to_mission = {
            'intro': 'kickoff',
            'empathy': 'empathy',
            'define': 'define',
            'ideate': 'ideate',
            'prototype': 'prototype',
            'testing': 'showcase'  # Use showcase for testing phase
        }
        
        mission_type = phase_to_mission.get(self.phase_type)
        if not mission_type:
            raise ValidationError(f"No mission type defined for phase: {self.phase_type}")
        
        # Get mission from session's design game
        try:
            mission = DesignMission.objects.filter(
                game=self.session.design_game,
                mission_type=mission_type
            ).first()
            
            if not mission:
                raise ValidationError(f"No mission found for type: {mission_type}")
                
            return mission
        except Exception as e:
            raise ValidationError(f"Error getting mission: {str(e)}")
    
    def get_context_data(self, **kwargs):
        """Add common context for all phases"""
        context = super().get_context_data(**kwargs)
        context.update({
            'session': self.session,
            'team': self.team,
            'phase_type': self.phase_type,
            'phase_display': self.get_phase_display(),
            'session_code': self.session_code,
        })
        return context
    
    def post(self, request, *args, **kwargs):
        """Handle phase submission - override in subclasses"""
        try:
            # Save phase data - implement in subclasses
            self.save_phase_data(request.POST)
            
            messages.success(request, f'{self.get_phase_display()} completed successfully!')
            
            # Redirect to next phase
            if self.next_phase:
                return redirect(f'group_learning:{self.next_phase}', session_code=self.session_code)
            else:
                return redirect('group_learning:completion_phase', session_code=self.session_code)
                
        except Exception as e:
            messages.error(request, f'Error submitting {self.get_phase_display()}: {str(e)}')
            return self.get(request, *args, **kwargs)
    
    def save_phase_data(self, post_data):
        """Save phase-specific data - implement in subclasses"""
        raise NotImplementedError("Subclasses must implement save_phase_data method")


class StudentEntryView(View):
    """
    Smart routing view that redirects to the next unsubmitted phase
    """
    def get(self, request, session_code):
        # Get team from session
        team_id = request.session.get(f'team_id_{session_code}')
        if not team_id:
            return redirect('group_learning:simplified_join_session', session_code=session_code)
            
        try:
            team = DesignTeam.objects.get(id=team_id, session__session_code=session_code)
            session = DesignThinkingSession.objects.get(session_code=session_code)
        except (DesignTeam.DoesNotExist, DesignThinkingSession.DoesNotExist):
            messages.error(request, 'Session or team not found.')
            return redirect('group_learning:simplified_create_session')
        
        # Check which phases are completed
        completed_phases = set(
            SimplifiedPhaseInput.objects.filter(
                team=team, 
                session=session
            ).values_list('phase_type', flat=True)
        )
        
        # Determine next unsubmitted phase
        phase_order = ['intro', 'empathy', 'define', 'ideate', 'prototype', 'testing']
        
        for phase in phase_order:
            if phase not in completed_phases:
                return redirect(f'group_learning:{phase}_phase', session_code=session_code)
        
        # All phases complete
        return redirect('group_learning:completion_phase', session_code=session_code)


class IntroPhaseView(BasePhaseView):
    """Introduction phase with game overview"""
    phase_type = 'intro'
    next_phase = 'empathy_phase'
    template_name = 'group_learning/design_thinking/missions/kickoff.html'
    
    def save_phase_data(self, post_data):
        """Mark intro as completed"""
        mission = self.get_mission_for_phase()
        SimplifiedPhaseInput.objects.create(
            team=self.team,
            mission=mission,
            session=self.session,
            phase_type=self.phase_type,
            student_name=self.team.team_name,
            student_session_id=f"team_{self.team.id}",
            input_type='checkbox',
            input_label='Introduction Completed',
            selected_value='true',
            input_order=1
        )


class EmpathyPhaseView(BasePhaseView):
    """Empathy phase - understanding classroom problems"""
    phase_type = 'empathy'
    next_phase = 'define_phase'
    template_name = 'group_learning/design_thinking/missions/empathy.html'
    
    def save_phase_data(self, post_data):
        """Save selected pain points"""
        selected_problems = post_data.getlist('pain_points')
        
        if not selected_problems:
            raise ValidationError('Please select at least one problem.')
            
        # Save selected problems
        mission = self.get_mission_for_phase()
        for i, problem in enumerate(selected_problems, 1):
            SimplifiedPhaseInput.objects.create(
                team=self.team,
                mission=mission,
                session=self.session,
                phase_type=self.phase_type,
                student_name=self.team.team_name,
                student_session_id=f"team_{self.team.id}",
                input_type='checkbox',
                input_label='Selected Classroom Problem',
                selected_value=problem,
                input_order=i
            )


class DefinePhaseView(BasePhaseView):
    """Define phase - creating problem statement"""
    phase_type = 'define'
    next_phase = 'ideate_phase'
    template_name = 'group_learning/design_thinking/missions/define.html'
    
    def save_phase_data(self, post_data):
        """Save problem definition inputs"""
        problem_statement = post_data.get('problem_statement', '').strip()
        target_audience = post_data.get('target_audience', '').strip()
        cause = post_data.get('cause', '').strip()
        action = post_data.get('action', '').strip()
        
        if not all([problem_statement, target_audience, cause, action]):
            raise ValidationError('Please complete all fields.')
            
        # Save all define inputs
        inputs = [
            ('Problem Statement', problem_statement),
            ('Target Audience', target_audience), 
            ('Root Cause', cause),
            ('Proposed Action', action)
        ]
        
        mission = self.get_mission_for_phase()
        for i, (label, value) in enumerate(inputs, 1):
            SimplifiedPhaseInput.objects.create(
                team=self.team,
                mission=mission,
                session=self.session,
                phase_type=self.phase_type,
                student_name=self.team.team_name,
                student_session_id=f"team_{self.team.id}",
                input_type='text_medium',
                input_label=label,
                selected_value=value,
                input_order=i
            )


class IdeatePhaseView(BasePhaseView):
    """Ideate phase - generating solution ideas"""
    phase_type = 'ideate'
    next_phase = 'prototype_phase'
    template_name = 'group_learning/design_thinking/missions/ideate.html'
    
    def save_phase_data(self, post_data):
        """Save generated ideas"""
        ideas = []
        for i in range(1, 11):  # Up to 10 ideas
            idea = post_data.get(f'idea_{i}', '').strip()
            if idea:
                ideas.append(idea)
        
        if len(ideas) < 3:
            raise ValidationError('Please provide at least 3 ideas.')
            
        # Save all ideas
        mission = self.get_mission_for_phase()
        for i, idea in enumerate(ideas, 1):
            SimplifiedPhaseInput.objects.create(
                team=self.team,
                mission=mission,
                session=self.session,
                phase_type=self.phase_type,
                student_name=self.team.team_name,
                student_session_id=f"team_{self.team.id}",
                input_type='text_medium',
                input_label=f'Solution Idea #{i}',
                selected_value=idea,
                input_order=i
            )


class PrototypePhaseView(BasePhaseView):
    """Prototype phase - building solutions"""
    phase_type = 'prototype'
    next_phase = 'testing_phase'
    template_name = 'group_learning/design_thinking/missions/prototype.html'
    
    def save_phase_data(self, post_data):
        """Save prototype information"""
        description = post_data.get('description', '').strip()
        created = post_data.get('prototype_created') == 'on'
        tested = post_data.get('prototype_tested') == 'on'
        
        if not description or not created or not tested:
            raise ValidationError('Please complete the prototype description and mark both checkboxes.')
            
        # Save prototype data
        inputs = [
            ('Prototype Description', description),
            ('Prototype Created', 'Yes' if created else 'No'),
            ('Prototype Tested', 'Yes' if tested else 'No')
        ]
        
        mission = self.get_mission_for_phase()
        for i, (label, value) in enumerate(inputs, 1):
            SimplifiedPhaseInput.objects.create(
                team=self.team,
                mission=mission,
                session=self.session,
                phase_type=self.phase_type,
                student_name=self.team.team_name,
                student_session_id=f"team_{self.team.id}",
                input_type='text_medium' if i == 1 else 'checkbox',
                input_label=label,
                selected_value=value,
                input_order=i
            )


class TestingPhaseView(BasePhaseView):
    """Testing phase - getting feedback and presenting solution"""
    phase_type = 'testing'
    next_phase = None  # Last phase
    template_name = 'group_learning/design_thinking/missions/showcase.html'
    
    def save_phase_data(self, post_data):
        """Save testing and feedback data"""
        feedback = post_data.get('feedback', '').strip()
        
        # Save feedback
        mission = self.get_mission_for_phase()
        SimplifiedPhaseInput.objects.create(
            team=self.team,
            mission=mission,
            session=self.session,
            phase_type=self.phase_type,
            student_name=self.team.team_name,
            student_session_id=f"team_{self.team.id}",
            input_type='text_medium',
            input_label='Testing Feedback',
            selected_value=feedback or 'No feedback provided',
            input_order=1
        )


class CompletionView(TemplateView):
    """Completion screen showing success"""
    template_name = 'phases/completion.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        session_code = kwargs.get('session_code')
        
        # Get team and session info
        team_id = self.request.session.get(f'team_id_{session_code}')
        if team_id:
            try:
                team = DesignTeam.objects.get(id=team_id, session__session_code=session_code)
                session = DesignThinkingSession.objects.get(session_code=session_code)
                
                context.update({
                    'session': session,
                    'team': team,
                    'session_code': session_code,
                })
            except (DesignTeam.DoesNotExist, DesignThinkingSession.DoesNotExist):
                pass
                
        return context