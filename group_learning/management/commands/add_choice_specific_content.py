from django.core.management.base import BaseCommand
from group_learning.models import ConstitutionQuestion, ConstitutionOption


class Command(BaseCommand):
    help = 'Add choice-specific dynamic content to Constitution Game options'

    def handle(self, *args, **options):
        self.stdout.write('Adding choice-specific content to Constitution options...')

        # Sample content for Constitution Game scenarios based on actual option text
        choice_content_examples = {
            # Leadership Structure Options
            'wise_leader': {
                'governance_impact': "Your choice of a single wise leader creates centralized decision-making with potential for quick, decisive action. However, this concentrates power and may limit diverse perspectives in governance.",
                'score_reasoning': "Governance score decreased by -2 points because single-leader systems, while efficient, reduce democratic participation and create risks of power abuse without proper checks and balances.",
                'country_state_changes': "The capital develops impressive government buildings and efficient administrative systems. However, citizen participation infrastructure remains limited as power flows from the top down.",
                'societal_impact': "Citizens may benefit from quick decisions but lose direct voice in governance. Society becomes more hierarchical with reduced political freedoms and civic engagement."
            },
            'council_chosen': {
                'governance_impact': "Your choice of a council of chosen people creates collaborative leadership with shared decision-making. This balances efficiency with broader representation in governance.",
                'score_reasoning': "Governance score increased by +3 points because council-based governance provides checks and balances while maintaining efficient decision-making through selected representatives.",
                'country_state_changes': "Council chambers and administrative buildings develop in the capital. Cities see steady growth as consistent policy-making creates stable business environment.",
                'societal_impact': "Citizens benefit from more balanced governance while selected council members represent different community interests. Democratic culture develops through representative participation."
            },
            'all_citizens': {
                'governance_impact': "Your choice for all citizens to participate together creates maximum democratic participation but may slow decision-making. Every citizen has direct voice in shaping the nation's future.",
                'score_reasoning': "Governance score increased by +5 points because direct citizen participation maximizes democratic legitimacy and ensures government truly represents the people's will.",
                'country_state_changes': "Community centers and digital voting infrastructure flourish. Cities develop strong civic infrastructure as citizen engagement drives local development.",
                'societal_impact': "Social cohesion strengthens as all citizens have equal voice. Civic education and political awareness increase, creating an informed and engaged society."
            },
            # Election Methods
            'free_elections': {
                'governance_impact': "Your choice of free, fair elections establishes democratic accountability and peaceful transfer of power. Leaders must earn and maintain public trust through their performance.",
                'score_reasoning': "Governance score increased by +4 points because democratic elections ensure leaders are accountable to citizens and create legitimacy through popular mandate.",
                'country_state_changes': "Electoral infrastructure and voting centers develop nationwide. Cities grow as democratic stability attracts investment and skilled citizens.",
                'societal_impact': "Citizens develop democratic culture and civic responsibility. Political participation increases while peaceful transitions of power strengthen social stability."
            },
            'hereditary_rule': {
                'governance_impact': "Your choice of hereditary rule where leaders appoint family creates dynastic power structures that may lack merit-based selection and democratic accountability.",
                'score_reasoning': "Governance score decreased by -4 points because hereditary systems undermine merit-based leadership and democratic principles of earned authority.",
                'country_state_changes': "Royal palaces and dynastic monuments dominate the capital. Economic development depends on royal favor rather than market forces or democratic planning.",
                'societal_impact': "Society becomes stratified with royal families at the top. Social mobility decreases while traditional hierarchies strengthen, potentially creating inequality."
            },
            'military_rule': {
                'governance_impact': "Your choice of military or strongest group leadership creates authoritarian governance focused on order and control rather than democratic participation.",
                'score_reasoning': "Governance score decreased by -5 points because military rule eliminates democratic processes and concentrates power in non-elected institutions.",
                'country_state_changes': "Military installations and security infrastructure dominate urban development. Economic growth may occur but lacks civilian oversight and democratic planning.",
                'societal_impact': "Citizens lose political freedoms while military values dominate society. Dissent is suppressed and civic participation is replaced by state control."
            },
            # Rights Protection
            'constitutional_rights': {
                'governance_impact': "Your choice of constitutional rights creates strong legal framework protecting individual freedoms and limiting government power through written guarantees.",
                'score_reasoning': "Governance score increased by +5 points because constitutional rights provide fundamental protections and establish rule of law that limits arbitrary government action.",
                'country_state_changes': "Supreme Court buildings and legal institutions develop. Cities attract international businesses and residents due to predictable legal protections.",
                'societal_impact': "Citizens enjoy protected freedoms of speech, religion, and equality. Minority groups feel secure while diverse communities flourish under legal protections."
            },
            'leader_decides': {
                'governance_impact': "Your choice to let leaders decide rights case-by-case creates flexible but unpredictable governance where citizen protections depend on current leadership preferences.",
                'score_reasoning': "Governance score decreased by -3 points because arbitrary rights decisions undermine rule of law and create uncertainty about citizen protections.",
                'country_state_changes': "Government buildings focus on administrative power rather than legal institutions. Economic development faces uncertainty due to unpredictable policy environment.",
                'societal_impact': "Citizens face uncertainty about their rights and freedoms. Social anxiety increases as protections depend on leadership whims rather than established law."
            },
            'supporter_rights': {
                'governance_impact': "Your choice to limit rights to government supporters creates partisan governance that discriminates based on political loyalty rather than equal citizenship.",
                'score_reasoning': "Governance score decreased by -6 points because discriminatory rights systems violate democratic principles of equal treatment and create authoritarian governance.",
                'country_state_changes': "Government buildings serve surveillance and control functions. Economic development suffers as discrimination reduces talent pool and innovation.",
                'societal_impact': "Society becomes deeply divided between supporters and non-supporters. Social cohesion breaks down while fear and political persecution increase."
            }
        }

        # Find constitution questions and add content to their options
        questions = ConstitutionQuestion.objects.all()
        updated_count = 0

        for question in questions:
            self.stdout.write(f"Processing question: {question.question_text[:50]}...")
            
            options = question.options.all()
            for option in options:
                # Determine content type based on option text keywords
                option_text_lower = option.option_text.lower()
                content_key = None
                
                # Leadership structure patterns
                if any(phrase in option_text_lower for phrase in ['one wise leader', 'wise leader']):
                    content_key = 'wise_leader'
                elif any(phrase in option_text_lower for phrase in ['council of chosen', 'chosen people']):
                    content_key = 'council_chosen'
                elif any(phrase in option_text_lower for phrase in ['all citizens together', 'citizens together']):
                    content_key = 'all_citizens'
                
                # Election method patterns
                elif any(phrase in option_text_lower for phrase in ['free, fair elections', 'citizens through free']):
                    content_key = 'free_elections'
                elif any(phrase in option_text_lower for phrase in ['appoint their children', 'relatives as rulers', 'children or relatives']):
                    content_key = 'hereditary_rule'
                elif any(phrase in option_text_lower for phrase in ['military', 'strongest group']):
                    content_key = 'military_rule'
                
                # Rights protection patterns
                elif any(phrase in option_text_lower for phrase in ['list of rights in the rulebook', 'rights in the rulebook']):
                    content_key = 'constitutional_rights'
                elif any(phrase in option_text_lower for phrase in ['let leaders decide', 'leaders decide what']):
                    content_key = 'leader_decides'
                elif any(phrase in option_text_lower for phrase in ['only for groups who support', 'support the government']):
                    content_key = 'supporter_rights'
                
                # Add content if we found a match and option doesn't already have content
                if content_key and not option.governance_impact:
                    content = choice_content_examples[content_key]
                    option.governance_impact = content['governance_impact']
                    option.score_reasoning = content['score_reasoning']
                    option.country_state_changes = content['country_state_changes']
                    option.societal_impact = content['societal_impact']
                    option.save()
                    updated_count += 1
                    self.stdout.write(f"  ✅ Added {content_key} content to option {option.option_letter}")

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully updated {updated_count} constitution options with choice-specific content!'
            )
        )
        
        # Show some statistics
        total_options = ConstitutionOption.objects.count()
        options_with_content = ConstitutionOption.objects.exclude(governance_impact='').count()
        
        self.stdout.write(f"Statistics:")
        self.stdout.write(f"  Total options: {total_options}")
        self.stdout.write(f"  Options with dynamic content: {options_with_content}")
        self.stdout.write(f"  Coverage: {(options_with_content/total_options)*100:.1f}%")