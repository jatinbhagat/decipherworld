from django.core.management.base import BaseCommand
from django.db import transaction
from group_learning.models import Game, ConstitutionOption, GameLearningModule


class Command(BaseCommand):
    help = 'Create 64 choice-specific learning modules for Advanced Constitution Challenge'

    def handle(self, *args, **options):
        self.stdout.write("📚 Creating Advanced Learning Modules with Comparative Analysis...")
        
        try:
            # Get the Advanced Constitution Game
            try:
                game = Game.objects.get(title="Advanced Constitution Challenge")
                self.stdout.write(f"✅ Found Advanced Constitution Game (ID: {game.id})")
            except Game.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR("❌ Advanced Constitution Game not found. Run create_advanced_constitution_game first.")
                )
                return
            
            with transaction.atomic():
                # Clear existing learning modules for this game type
                GameLearningModule.objects.filter(game_type='constitution_challenge', trigger_condition='option_based').delete()
                
                # Get all options for the advanced game
                options = ConstitutionOption.objects.filter(question__game=game).order_by('question__order', 'option_letter')
                
                self.stdout.write(f"🔄 Creating learning modules for {options.count()} options...")
                
                modules_created = 0
                
                for option in options:
                    question = option.question
                    
                    # Create comprehensive learning module for each choice
                    module_title = f"Choice Analysis: {option.option_letter} - {option.governance_principle}"
                    
                    # Generate comparative analysis content based on the question and option
                    principle_explanation, key_takeaways, comparative_analysis, constitution_explanation = self._generate_content(
                        question, option
                    )
                    
                    # Create the learning module
                    GameLearningModule.objects.create(
                        title=module_title,
                        game_type='constitution_challenge',
                        principle_explanation=principle_explanation,
                        key_takeaways=key_takeaways,
                        historical_context=comparative_analysis,
                        real_world_example=self._get_real_world_example(option),
                        
                        # Enhanced fields for advanced game
                        action_impact_title="Impact of Your Constitutional Choice",
                        governance_impact=option.feedback_message,
                        score_reasoning=f"Score: {option.score_value:+d} - {self._get_score_reasoning(option.score_value)}",
                        country_state_changes=self._get_country_changes(option.score_value),
                        societal_impact=self._get_societal_impact(option),
                        
                        # Constitution teaching section
                        constitution_topic_title="Comparative Constitutional Analysis",
                        constitution_chapter=self._map_category_to_chapter(question.category),
                        constitution_principle=option.governance_principle,
                        constitution_explanation=constitution_explanation,
                        constitution_article_reference=self._get_article_reference(question.category),
                        historical_constitutional_context=self._get_historical_context(question.category),
                        
                        # Trigger configuration - specific to this option
                        trigger_condition='option_based',
                        trigger_option=option,
                        
                        # Display settings
                        display_timing='instant',
                        is_enabled=True
                    )
                    
                    modules_created += 1
                
                self.stdout.write(
                    self.style.SUCCESS(f"✅ Created {modules_created} choice-specific learning modules")
                )
                
                self.stdout.write(
                    self.style.SUCCESS("🎉 Advanced Learning Modules completed!")
                )
                self.stdout.write(f"📚 Total modules: {modules_created}")
                self.stdout.write("🌍 Each module includes comparative analysis with other democracies")
                self.stdout.write("🧠 Advanced constitutional concepts and real-world implications")
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Error creating learning modules: {e}")
            )
            raise

    def _generate_content(self, question, option):
        """Generate comprehensive content for each option"""
        
        # Base content varies by question category and option
        category = question.category
        option_letter = option.option_letter
        score = option.score_value
        
        if category == 'leadership':
            principle_explanation = f"Leadership in constitutional democracies requires balancing executive efficiency with democratic accountability. The choice '{option.governance_principle}' reflects a specific approach to resolving tensions between effective governance and institutional checks."
            
            key_takeaways = f"• Executive power must be exercised within constitutional limits\n• Democratic legitimacy comes from electoral mandate and legislative support\n• Crisis situations test but should not break constitutional norms\n• Comparative analysis: Presidential vs Parliamentary systems handle executive power differently"
            
            comparative_analysis = f"Comparing democratic systems: The USA (presidential), UK (parliamentary), France (semi-presidential), and India (parliamentary) each handle executive-legislative tensions differently. Your choice aligns with the approach typically seen in {self._get_system_comparison(score)} systems."
            
            constitution_explanation = "India's parliamentary system ensures the Prime Minister remains accountable to the Lok Sabha, while the President acts as a constitutional head. This differs from the US presidential system where executive power is more concentrated but checked by Congress."
            
        elif category == 'rules':
            principle_explanation = f"Constitutional rule-making involves balancing majority will with minority rights and institutional integrity. '{option.governance_principle}' represents a particular philosophy about how democratic rules should be created and enforced."
            
            key_takeaways = f"• Constitutional rules require special procedures for changes\n• Legislative supremacy must be balanced with constitutional supremacy\n• International standards influence but don't override domestic democratic processes\n• Comparative insight: Different democracies handle rule-making authority differently"
            
            comparative_analysis = f"Global perspective: Germany's Basic Law includes 'eternity clauses' that cannot be amended, while the UK relies on parliamentary sovereignty. India's Constitution allows amendments but with varying procedures for different provisions. Your choice reflects the {self._get_amendment_philosophy(score)} approach to constitutional change."
            
            constitution_explanation = "The Indian Constitution's amendment process (Article 368) requires different majorities for different types of changes, balancing flexibility with stability. This contrasts with countries like the USA (very rigid) or UK (very flexible)."
            
        elif category == 'rights':
            principle_explanation = f"Fundamental rights require careful balancing between individual liberty and collective welfare. '{option.governance_principle}' embodies a specific approach to resolving conflicts between competing rights and interests."
            
            key_takeaways = f"• Rights are not absolute but must be balanced against other rights and state interests\n• Proportionality principle guides rights restrictions\n• Emergency powers test the strength of rights protection\n• Global comparison: Rights enforcement varies significantly across democracies"
            
            comparative_analysis = f"International perspective: The European Court of Human Rights, US Supreme Court, and Indian Supreme Court apply different standards for rights protection. Your choice aligns with the {self._get_rights_philosophy(score)} tradition of rights interpretation."
            
            constitution_explanation = "Part III of the Indian Constitution guarantees fundamental rights with built-in limitations ('reasonable restrictions'). This approach balances individual freedom with social harmony, similar to the European approach but different from the more absolute American First Amendment tradition."
            
        elif category == 'justice':
            principle_explanation = f"Judicial independence and constitutional interpretation are cornerstone of democratic governance. '{option.governance_principle}' represents a particular view of how courts should function in a constitutional democracy."
            
            key_takeaways = f"• Judicial independence requires institutional and financial autonomy\n• Constitutional interpretation methods vary (originalist vs living document)\n• Precedent provides legal stability but must allow for correction\n• Comparative analysis: Different Supreme Courts have varying approaches to constitutional review"
            
            comparative_analysis = f"Comparative judicial review: The US Supreme Court (strong review), UK Supreme Court (limited review), German Constitutional Court (specialized review), and Indian Supreme Court (comprehensive review) each approach constitutional interpretation differently. Your choice reflects the {self._get_judicial_philosophy(score)} school of thought."
            
            constitution_explanation = "The Indian Supreme Court has developed unique doctrines like the 'basic structure' doctrine, preventing amendments that destroy the Constitution's core features. This judicial innovation goes beyond American or European models."
            
        elif category == 'participation':
            principle_explanation = f"Democratic participation requires both institutional mechanisms and cultural foundations. '{option.governance_principle}' represents a specific approach to enhancing citizen engagement in democratic governance."
            
            key_takeaways = f"• Voting is fundamental but not the only form of democratic participation\n• Digital technology creates new opportunities and challenges for democracy\n• Civic education is essential for informed democratic participation\n• Comparative insight: Different democracies use varying mechanisms to encourage participation"
            
            comparative_analysis = f"Global participation models: Australia (compulsory voting), Switzerland (extensive direct democracy), Nordic countries (high voluntary turnout), and India (massive electoral participation despite challenges) each encourage democratic participation differently. Your choice aligns with the {self._get_participation_model(score)} approach."
            
            constitution_explanation = "India's Constitution ensures universal adult suffrage (Article 326) and has evolved to include innovations like electronic voting machines and extensive election commission powers, creating a unique model of mass democratic participation."
            
        elif category == 'checks':
            principle_explanation = f"Checks and balances prevent the concentration of power while ensuring effective governance. '{option.governance_principle}' reflects a particular understanding of how institutional accountability should work."
            
            key_takeaways = f"• Separation of powers prevents tyranny but requires coordination\n• Accountability mechanisms must be independent and effective\n• Emergency powers test the strength of democratic checks\n• Comparative perspective: Different democracies structure accountability differently"
            
            comparative_analysis = f"Institutional design comparison: The US (rigid separation), UK (flexible Westminster system), Germany (federalism with strong courts), and India (parliamentary with strong judiciary) each structure checks and balances differently. Your choice reflects the {self._get_accountability_model(score)} tradition."
            
            constitution_explanation = "India's system combines parliamentary governance with strong judicial review and independent institutions like the Election Commission and Comptroller and Auditor General, creating multiple accountability mechanisms."
            
        else:
            # Default content
            principle_explanation = f"Constitutional governance requires balancing competing values and interests. '{option.governance_principle}' represents one approach to resolving these complex democratic challenges."
            key_takeaways = "• Democratic governance involves complex trade-offs\n• Constitutional principles guide decision-making\n• Comparative analysis enriches understanding\n• Context matters in constitutional interpretation"
            comparative_analysis = "Different democratic systems approach these challenges in various ways, reflecting their historical experiences and cultural contexts."
            constitution_explanation = "The Indian Constitution provides a framework for addressing these governance challenges through its comprehensive structure and institutional design."
        
        return principle_explanation, key_takeaways, comparative_analysis, constitution_explanation

    def _get_system_comparison(self, score):
        """Get system comparison based on score"""
        if score >= 2:
            return "well-balanced parliamentary"
        elif score >= 0:
            return "hybrid or reformed"
        else:
            return "centralized or authoritarian"

    def _get_amendment_philosophy(self, score):
        """Get constitutional amendment philosophy based on score"""
        if score >= 2:
            return "balanced constitutional change"
        elif score >= 0:
            return "moderate reform"
        else:
            return "destabilizing change"

    def _get_rights_philosophy(self, score):
        """Get rights philosophy based on score"""
        if score >= 2:
            return "proportional rights protection"
        elif score >= 0:
            return "moderate balancing"
        else:
            return "rights-restrictive"

    def _get_judicial_philosophy(self, score):
        """Get judicial philosophy based on score"""
        if score >= 2:
            return "principled constitutional review"
        elif score >= 0:
            return "moderate judicial restraint"
        else:
            return "politicized judicial"

    def _get_participation_model(self, score):
        """Get participation model based on score"""
        if score >= 2:
            return "enhanced democratic participation"
        elif score >= 0:
            return "traditional electoral"
        else:
            return "restricted participation"

    def _get_accountability_model(self, score):
        """Get accountability model based on score"""
        if score >= 2:
            return "strong institutional accountability"
        elif score >= 0:
            return "moderate oversight"
        else:
            return "weak accountability"

    def _get_real_world_example(self, option):
        """Generate real-world examples based on option"""
        score = option.score_value
        category = option.question.category
        
        if score >= 2:
            examples = {
                'leadership': 'Examples: Germany\'s stable coalition governments, New Zealand\'s MMP system fostering collaboration.',
                'rules': 'Examples: Canada\'s Charter of Rights and Freedoms, South Africa\'s progressive constitutional reform.',
                'rights': 'Examples: European Court of Human Rights proportionality doctrine, Indian Supreme Court\'s reasonableness test.',
                'justice': 'Examples: German Constitutional Court\'s methodical approach, Indian basic structure doctrine.',
                'participation': 'Examples: Estonia\'s e-governance innovations, Taiwan\'s digital democracy experiments.',
                'checks': 'Examples: Brazilian institutional framework post-1988, South Korea\'s democratic institutions.'
            }
        elif score >= 0:
            examples = {
                'leadership': 'Examples: France\'s semi-presidential system, Italy\'s coalition politics.',
                'rules': 'Examples: Australia\'s federal constitutional system, Japan\'s post-war constitutional stability.',
                'rights': 'Examples: UK\'s Human Rights Act implementation, Canadian notwithstanding clause.',
                'justice': 'Examples: UK Supreme Court\'s measured approach, Australian High Court precedents.',
                'participation': 'Examples: Swiss direct democracy traditions, Irish citizens\' assemblies.',
                'checks': 'Examples: Dutch consensus democracy, Belgian complex institutional arrangements.'
            }
        else:
            examples = {
                'leadership': 'Warning: Similar approaches seen in Venezuela\'s concentration of power, Hungary\'s democratic backsliding.',
                'rules': 'Caution: Echoes of Poland\'s judicial reforms, Turkey\'s constitutional changes.',
                'rights': 'Concern: Patterns seen in authoritarian restrictions during COVID-19 across multiple countries.',
                'justice': 'Warning: Similar to court-packing attempts in various democracies undergoing stress.',
                'participation': 'Alert: Reminiscent of voter suppression tactics, restrictions on civil society.',
                'checks': 'Danger: Parallels with democratic erosion in several countries over the past decade.'
            }
        
        return examples.get(category, 'Constitutional choices have real-world consequences for democratic governance.')

    def _get_score_reasoning(self, score):
        """Get score reasoning explanation"""
        if score >= 3:
            return "Excellent constitutional choice that strengthens democratic governance"
        elif score >= 2:
            return "Good approach that supports democratic principles"
        elif score >= 1:
            return "Reasonable option with some democratic benefits"
        elif score >= 0:
            return "Neutral choice with mixed implications for democracy"
        elif score >= -1:
            return "Concerning approach that may weaken democratic institutions"
        elif score >= -2:
            return "Poor choice that undermines democratic governance"
        else:
            return "Dangerous decision that threatens constitutional democracy"

    def _get_country_changes(self, score):
        """Get country state changes based on score"""
        if score >= 2:
            return "Strong democratic institutions lead to economic growth, social cohesion, and international respect. Cities flourish with good governance, transparent institutions, and citizen trust."
        elif score >= 0:
            return "Moderate governance improvements create steady development with some challenges. Cities see gradual improvement in services and civic engagement."
        else:
            return "Poor governance choices lead to institutional weakness, economic problems, and social unrest. Cities experience decline in services and citizen confidence."

    def _get_societal_impact(self, option):
        """Get societal impact based on option characteristics"""
        score = option.score_value
        principle = option.governance_principle.lower()
        
        if 'democratic' in principle and score > 0:
            return "Citizens feel empowered and protected when democratic principles are upheld. Strong institutions create trust and social harmony."
        elif 'rights' in principle and score > 0:
            return "Protection of rights creates a secure society where all citizens can flourish regardless of their background or beliefs."
        elif 'account' in principle and score > 0:
            return "Accountable governance builds public trust and encourages civic participation, creating a virtuous cycle of democratic engagement."
        elif score < 0:
            return "Weak or authoritarian choices erode social trust, increase inequality, and may lead to civil unrest or democratic backsliding."
        else:
            return "Mixed approaches create uncertainty but may provide valuable lessons for future constitutional development."

    def _map_category_to_chapter(self, category):
        """Map question categories to constitution chapters"""
        mapping = {
            'leadership': 'government_branches',
            'rules': 'making',
            'rights': 'rights_duties',
            'justice': 'government_branches',
            'participation': 'features',
            'checks': 'government_branches'
        }
        return mapping.get(category, 'features')

    def _get_article_reference(self, category):
        """Get relevant constitutional articles"""
        references = {
            'leadership': 'Articles 52-78: Executive Power and Presidential/PM roles',
            'rules': 'Article 368: Amendment procedure and constitutional change',
            'rights': 'Articles 12-35: Fundamental Rights and reasonable restrictions',
            'justice': 'Articles 124-147: Supreme Court and High Courts',
            'participation': 'Articles 325-326: Elections and universal suffrage',
            'checks': 'Articles 74-75: Council of Ministers and parliamentary accountability'
        }
        return references.get(category, 'Constitution of India: Framework for democratic governance')

    def _get_historical_context(self, category):
        """Get historical constitutional context"""
        contexts = {
            'leadership': 'The Indian Constitution chose a parliamentary system over a presidential one, influenced by British traditions but adapted for Indian conditions and diversity.',
            'rules': 'The Constituent Assembly debates reveal careful consideration of amendment procedures, balancing flexibility with stability based on global constitutional experiences.',
            'rights': 'Fundamental Rights in the Indian Constitution drew from various sources including the US Bill of Rights, but were adapted to Indian social conditions and the need for affirmative action.',
            'justice': 'The Supreme Court\'s role evolved through landmark cases, with the basic structure doctrine representing a uniquely Indian contribution to constitutional law.',
            'participation': 'Universal adult suffrage was a bold choice for a largely illiterate society in 1950, reflecting the founders\' faith in democratic participation.',
            'checks': 'The Constitution created multiple accountability mechanisms, learning from both British parliamentary traditions and American separation of powers.'
        }
        return contexts.get(category, 'The Indian Constitution represents a synthesis of global constitutional wisdom adapted to Indian conditions and aspirations.')