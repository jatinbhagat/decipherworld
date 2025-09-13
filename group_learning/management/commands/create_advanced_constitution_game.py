from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from group_learning.models import Game, ConstitutionQuestion, ConstitutionOption, GameLearningModule


class Command(BaseCommand):
    help = 'Create Advanced Constitution Challenge game with 16 questions and 64 options'

    def handle(self, *args, **options):
        self.stdout.write("🏛️ Creating Advanced Constitution Challenge Game...")
        
        try:
            with transaction.atomic():
                # Create Advanced Constitution Game
                game, created = Game.objects.get_or_create(
                    title="Advanced Constitution Challenge",
                    defaults={
                        'subtitle': 'Advanced Governance and Constitutional Analysis (Grades 9-12)',
                        'game_type': 'constitution_challenge',
                        'description': 'Test your advanced understanding of constitutional principles, governance systems, and democratic institutions through complex scenarios and comparative analysis.',
                        'context': 'Dive deep into advanced constitutional concepts including federalism, judicial review, electoral systems, and emergency powers. Compare Indian constitutional provisions with other major democracies.',
                        'min_players': 2,
                        'max_players': 8,
                        'estimated_duration': 45,
                        'target_age_min': 14,
                        'target_age_max': 18,
                        'difficulty_level': 3,  # Advanced
                        'introduction_text': 'Welcome to the Advanced Constitution Challenge! You will face complex governance scenarios that test your understanding of constitutional principles, democratic institutions, and comparative government systems. Each decision will shape your nation\'s development and democratic health.',
                        'is_active': True
                    }
                )
                
                if created:
                    self.stdout.write(f"✅ Created Advanced Constitution Game (ID: {game.id})")
                else:
                    self.stdout.write(f"✅ Advanced Constitution Game already exists (ID: {game.id})")
                    # Clear existing questions to avoid UNIQUE constraint errors on re-run
                    existing_questions = ConstitutionQuestion.objects.filter(game=game).count()
                    if existing_questions > 0:
                        self.stdout.write(f"🔄 Clearing {existing_questions} existing questions for clean setup...")
                        ConstitutionQuestion.objects.filter(game=game).delete()
                
                # Create 16 Advanced Questions with 4 difficult options each
                questions_data = [
                    {
                        'order': 1,
                        'category': 'leadership',
                        'question_text': 'A constitutional crisis emerges when the elected President and Prime Minister belong to different political parties and disagree on a major policy decision. How should this be resolved?',
                        'scenario_context': 'In your advanced democracy, the head of state and head of government have conflicting views on emergency economic measures during a financial crisis.',
                        'options': [
                            ('A', 'The President should override the PM as the ceremonial head of state', -2, 'This creates constitutional imbalance and undermines parliamentary democracy', 'Authoritarianism over democratic governance'),
                            ('B', 'The Prime Minister should make the decision as head of government with parliamentary support', 3, 'Correct constitutional principle - PM leads government with legislative mandate', 'Parliamentary supremacy with democratic accountability'),
                            ('C', 'Both should compromise through extended negotiations regardless of time sensitivity', 1, 'Compromise is good but may delay crucial decisions during crisis', 'Collaborative governance with potential inefficiency'),
                            ('D', 'The Supreme Court should intervene and make the policy decision', -1, 'Judicial overreach - courts interpret law, not make policy', 'Judicial activism beyond constitutional limits')
                        ]
                    },
                    {
                        'order': 2,
                        'category': 'leadership',
                        'question_text': 'Your country is considering changing from a parliamentary to a presidential system of government. What should be the primary consideration in this decision?',
                        'scenario_context': 'Citizens are debating whether to adopt a system like the USA (presidential) or keep the current system like India/UK (parliamentary).',
                        'options': [
                            ('A', 'Choose presidential system for stronger executive leadership', 0, 'Presidential systems provide clear leadership but may reduce legislative oversight', 'Executive strength with reduced checks and balances'),
                            ('B', 'Keep parliamentary system to maintain legislative supremacy', 2, 'Parliamentary systems ensure government accountability to elected representatives', 'Legislative oversight with collective responsibility'),
                            ('C', 'Create a hybrid system combining both presidential and parliamentary features', 1, 'Innovation is good but hybrid systems can create confusion and deadlock', 'Constitutional experimentation with complexity risks'),
                            ('D', 'Let the most popular leader decide which system works best', -3, 'This undermines constitutional democracy and creates potential for authoritarianism', 'Personality-based governance over institutional democracy')
                        ]
                    },
                    {
                        'order': 3,
                        'category': 'rules',
                        'question_text': 'Parliament wants to pass a constitutional amendment that limits judicial review powers. How should your democracy handle this proposal?',
                        'scenario_context': 'The legislature argues that courts are overstepping their bounds, while judiciary claims they must protect constitutional rights.',
                        'options': [
                            ('A', 'Support the amendment - elected representatives should have final say', -1, 'While democratic, this could undermine checks and balances essential to constitutional democracy', 'Legislative supremacy undermining judicial independence'),
                            ('B', 'Reject the amendment - judicial review is essential for constitutional protection', 2, 'Correct balance - judicial review protects constitutional principles from majority tyranny', 'Constitutional safeguards protecting minority rights'),
                            ('C', 'Modify the amendment to clarify judicial review limits without eliminating it', 3, 'Best approach - defines boundaries while preserving essential checks and balances', 'Balanced constitutional framework with clear institutional roles'),
                            ('D', 'Hold a referendum and let citizens decide directly', 0, 'Democratic input is valuable but complex constitutional issues need informed deliberation', 'Direct democracy on complex constitutional matters')
                        ]
                    },
                    {
                        'order': 4,
                        'category': 'rules',
                        'question_text': 'A proposed law would require all political parties to have internal democratic elections for leadership positions. How should this be evaluated?',
                        'scenario_context': 'Some parties resist, claiming organizational autonomy, while reformers argue democracy must start within parties themselves.',
                        'options': [
                            ('A', 'Mandatory internal democracy for all parties receiving public funding', 3, 'Excellent approach - ensures democratic principles extend to political organizations with public support', 'Democratic accountability throughout the political system'),
                            ('B', 'No regulation - parties should organize themselves as they choose', -2, 'Party autonomy is important but undemocratic parties can undermine overall democracy', 'Organizational freedom potentially undermining democratic culture'),
                            ('C', 'Voluntary guidelines with incentives for democratic party structures', 1, 'Positive encouragement but may not be sufficient to ensure democratic practices', 'Soft regulation with limited enforcement'),
                            ('D', 'Different rules for different sized parties based on their influence', 0, 'Pragmatic but creates unequal standards that could favor larger parties', 'Tiered regulation with potential bias toward established parties')
                        ]
                    },
                    {
                        'order': 5,
                        'category': 'rights',
                        'question_text': 'During a pandemic, the government restricts freedom of assembly but religious groups claim this violates their fundamental rights. How should courts balance these competing claims?',
                        'scenario_context': 'Public health experts support restrictions while religious leaders argue their constitutional rights are being violated disproportionately.',
                        'options': [
                            ('A', 'Public health always trumps individual rights during emergencies', -2, 'Too absolute - rights need protection even during crises, with proportional restrictions', 'State power over individual liberty without adequate safeguards'),
                            ('B', 'Religious freedom is absolute and cannot be restricted under any circumstances', -3, 'Dangerous precedent - no rights are absolute when they threaten others\' right to life', 'Absolute rights claims ignoring collective welfare'),
                            ('C', 'Apply strict scrutiny: restrictions must be necessary, proportional, and temporary', 3, 'Correct constitutional approach - balances rights protection with legitimate state interests', 'Proportional constitutional balancing with judicial oversight'),
                            ('D', 'Let each state/region decide based on their specific circumstances', 1, 'Federalism has value but constitutional rights should have uniform protection', 'Decentralized approach with potential for unequal rights protection')
                        ]
                    },
                    {
                        'order': 6,
                        'category': 'rights',
                        'question_text': 'A social media platform refuses to remove hate speech, claiming free speech protections. The government threatens to shut down the platform. What\'s the best constitutional approach?',
                        'scenario_context': 'Citizens are divided - some demand action against hate speech while others fear censorship and government overreach.',
                        'options': [
                            ('A', 'Government should shut down platforms that don\'t comply with hate speech laws', -1, 'Too heavy-handed - could lead to broader censorship and stifle legitimate expression', 'State censorship potentially exceeding reasonable bounds'),
                            ('B', 'Free speech is absolute - no restrictions on any online content', -3, 'Ignores real harm from hate speech and society\'s need for civil discourse', 'Absolute free speech ignoring harmful consequences'),
                            ('C', 'Establish clear legal standards for hate speech with transparent judicial review', 3, 'Best approach - balances free expression with protection from harmful speech through due process', 'Constitutional balance with procedural safeguards'),
                            ('D', 'Let platform users self-regulate through community guidelines and reporting', 0, 'Private regulation has value but may not adequately address serious hate speech', 'Self-regulation with limited accountability for harmful content')
                        ]
                    }
                ]
                
                # Continue with remaining questions...
                questions_data.extend([
                    {
                        'order': 7,
                        'category': 'justice',
                        'question_text': 'The Supreme Court is considering whether to overturn a decades-old precedent that many now consider outdated. How should they approach this decision?',
                        'scenario_context': 'Legal scholars are divided on whether constitutional interpretation should evolve with changing times or remain anchored to original meanings.',
                        'options': [
                            ('A', 'Overturn outdated precedents freely to keep constitution current with modern values', -1, 'Too much judicial activism could undermine legal stability and democratic lawmaking', 'Judicial activism potentially undermining legislative democracy'),
                            ('B', 'Never overturn established precedents - legal consistency is paramount', -2, 'Too rigid - some precedents may genuinely violate constitutional principles', 'Legal formalism ignoring constitutional evolution'),
                            ('C', 'Overturn only when precedent clearly contradicts constitutional text and principles', 3, 'Balanced approach - preserves legal stability while allowing correction of constitutional errors', 'Principled constitutional interpretation balancing stability and accuracy'),
                            ('D', 'Let parliament override court decisions through simple majority legislation', -2, 'Undermines judicial independence and constitutional supremacy', 'Legislative override of constitutional interpretation')
                        ]
                    },
                    {
                        'order': 8,
                        'category': 'justice',
                        'question_text': 'Lower courts are inconsistently interpreting a constitutional provision, creating confusion. The Supreme Court has not yet ruled on the issue. What should happen?',
                        'scenario_context': 'Citizens in different regions are receiving different treatment under the law due to varying court interpretations of constitutional rights.',
                        'options': [
                            ('A', 'Supreme Court should immediately take up any case involving constitutional inconsistency', 2, 'Good priority for ensuring uniform constitutional rights, though court capacity is limited', 'Constitutional uniformity through expedited supreme court review'),
                            ('B', 'Lower courts should continue interpreting independently until natural appeals process', 0, 'Respects judicial process but allows continued inequality in constitutional protection', 'Procedural correctness with temporary inequality'),
                            ('C', 'Create a special constitutional council to provide guidance on interpretations', 1, 'Innovation could help but might undermine judicial independence and court authority', 'Institutional innovation with potential constitutional complications'),
                            ('D', 'Parliament should clarify the constitutional provision through legislative amendment', 3, 'Best long-term solution - democratic clarification of constitutional meaning through proper process', 'Democratic constitutional clarification through amendment process')
                        ]
                    }
                ])
                
                # Add remaining 8 questions to complete 16 total
                remaining_questions = [
                    {
                        'order': 9,
                        'category': 'participation',
                        'question_text': 'Voter turnout is declining, especially among young citizens. What constitutional or systemic reform would best address this democratic deficit?',
                        'scenario_context': 'Political scientists worry about democratic legitimacy when large portions of eligible citizens don\'t participate in elections.',
                        'options': [
                            ('A', 'Make voting compulsory with fines for non-participation like Australia', 1, 'Increases turnout but may not improve quality of democratic participation', 'Mandatory participation with potential for uninformed voting'),
                            ('B', 'Lower voting age and expand civic education in schools', 3, 'Addresses root causes by building democratic culture and expanding participation', 'Democratic education and inclusive participation'),
                            ('C', 'Offer financial incentives for voting such as tax credits', 0, 'May increase turnout but could distort democratic process with monetary motivations', 'Economic incentives for democratic participation'),
                            ('D', 'Restrict voting to those who pass basic civic knowledge tests', -3, 'Completely undermines democratic equality - creates barriers similar to historical poll taxes', 'Anti-democratic exclusion based on knowledge requirements')
                        ]
                    },
                    {
                        'order': 10,
                        'category': 'participation',
                        'question_text': 'Social media algorithms are creating echo chambers that polarize political views. What should democratic governments do about this challenge?',
                        'scenario_context': 'Research shows citizens are increasingly exposed only to information that confirms their existing beliefs, undermining democratic dialogue.',
                        'options': [
                            ('A', 'Regulate algorithms to ensure diverse viewpoint exposure', 2, 'Addresses the problem but raises questions about government control over information flow', 'Government regulation of information diversity'),
                            ('B', 'Strengthen media literacy education and critical thinking skills', 3, 'Best long-term solution - empowers citizens to navigate information environment effectively', 'Democratic education for informed citizenship'),
                            ('C', 'Break up large social media companies to reduce their influence', 1, 'May help competition but doesn\'t directly address algorithm bias issues', 'Antitrust approach to information concentration'),
                            ('D', 'Government should create its own social media platform with balanced content', -2, 'Risks government propaganda and doesn\'t address underlying polarization issues', 'State-controlled media in democratic society')
                        ]
                    }
                ]
                
                questions_data.extend(remaining_questions)
                
                # Continue with more questions to reach 16 total
                final_questions = [
                    {
                        'order': 11,
                        'category': 'checks',
                        'question_text': 'The executive branch claims parliamentary oversight is interfering with efficient governance during a national crisis. How should this tension be resolved?',
                        'scenario_context': 'The government needs to act quickly during an emergency, but parliament insists on maintaining its oversight role.',
                        'options': [
                            ('A', 'Suspend parliamentary oversight during officially declared emergencies', -3, 'Extremely dangerous - removes democratic accountability precisely when it\'s most needed', 'Emergency powers without legislative oversight'),
                            ('B', 'Maintain full parliamentary oversight regardless of circumstances', 1, 'Good for democracy but may slow necessary emergency responses', 'Legislative oversight potentially impeding crisis response'),
                            ('C', 'Create streamlined oversight procedures for emergency situations', 3, 'Best balance - maintains democratic accountability while allowing efficient crisis response', 'Adaptive democratic institutions for emergency governance'),
                            ('D', 'Let the courts decide what level of oversight is appropriate during crises', 2, 'Judicial mediation is valuable but may not be fast enough during acute emergencies', 'Judicial balancing of emergency powers and democratic oversight')
                        ]
                    },
                    {
                        'order': 12,
                        'category': 'checks',
                        'question_text': 'An independent audit reveals significant irregularities in government spending, but the ruling party has a strong majority in parliament. What should happen next?',
                        'scenario_context': 'The opposition demands investigation while the government claims the audit is politically motivated. Public trust in institutions is at stake.',
                        'options': [
                            ('A', 'Parliamentary majority should vote to dismiss the audit findings', -3, 'Completely undermines accountability - majority rule cannot ignore evidence of wrongdoing', 'Majoritarian dismissal of institutional oversight'),
                            ('B', 'Create an independent investigation commission with cross-party representation', 3, 'Best approach - ensures accountability while maintaining legitimacy through broad representation', 'Independent oversight with democratic legitimacy'),
                            ('C', 'Let the courts handle it entirely as a legal matter', 2, 'Judicial review is important but parliament has constitutional duty for financial oversight', 'Judicial oversight of government accountability'),
                            ('D', 'Hold immediate elections to let voters decide on the government\'s accountability', 0, 'Electoral accountability is valuable but specific corruption issues need institutional response', 'Electoral judgment on government accountability')
                        ]
                    },
                    {
                        'order': 13,
                        'category': 'leadership',
                        'question_text': 'A charismatic political leader enjoys massive popular support but is advocating policies that would weaken democratic institutions. How should the system respond?',
                        'scenario_context': 'The leader argues they have a democratic mandate to reform institutions, while critics warn about authoritarian tendencies.',
                        'options': [
                            ('A', 'Popular mandate justifies any institutional changes the leader wants', -3, 'This is how democracies die - popularity cannot justify undermining democratic safeguards', 'Populist authoritarianism disguised as democratic mandate'),
                            ('B', 'Constitutional institutions must resist regardless of popular support', 2, 'Correct principle but needs careful implementation to maintain democratic legitimacy', 'Constitutional safeguards against majoritarian authoritarianism'),
                            ('C', 'Strengthen civic education about democratic norms and institutional importance', 3, 'Best long-term response - builds democratic culture to resist authoritarian appeals', 'Democratic education as safeguard against authoritarianism'),
                            ('D', 'Other political parties should form coalitions to block all reforms', -1, 'Blanket opposition may be undemocratic and could strengthen authoritarian narrative', 'Opposition coalitions potentially undermining legitimate governance')
                        ]
                    },
                    {
                        'order': 14,
                        'category': 'rules',
                        'question_text': 'International bodies are pressuring your country to adopt specific constitutional changes to protect minority rights. How should the nation respond?',
                        'scenario_context': 'International organizations threaten economic consequences if constitutional reforms are not implemented, creating tension between sovereignty and international standards.',
                        'options': [
                            ('A', 'Reject international pressure completely - constitutional sovereignty is paramount', -2, 'While sovereignty is important, isolating from international human rights norms can be problematic', 'National sovereignty over international human rights standards'),
                            ('B', 'Adopt all recommended changes immediately to avoid international consequences', -1, 'Too hasty - constitutional changes need domestic democratic deliberation', 'International pressure overriding domestic democratic process'),
                            ('C', 'Engage in dialogue and negotiate reforms that respect both sovereignty and human rights', 3, 'Best approach - balances international standards with democratic self-determination', 'Diplomatic engagement balancing sovereignty and human rights'),
                            ('D', 'Hold a national referendum on whether to accept international demands', 2, 'Democratic input is valuable though complex constitutional issues may need expert analysis', 'Direct democracy on constitutional human rights issues')
                        ]
                    },
                    {
                        'order': 15,
                        'category': 'participation',
                        'question_text': 'Technology now allows for real-time citizen input on legislation through digital platforms. Should this replace traditional representative democracy?',
                        'scenario_context': 'Advocates argue digital democracy is more responsive, while critics worry about populism and the complexity of governing.',
                        'options': [
                            ('A', 'Fully replace representatives with digital direct democracy', -3, 'Dangerous - eliminates deliberation, expertise, and protection of minority interests', 'Digital populism replacing representative democracy'),
                            ('B', 'Keep representative system unchanged - traditional democracy works best', 0, 'Conservative approach that may ignore beneficial technological enhancements', 'Traditional democracy resisting technological innovation'),
                            ('C', 'Integrate digital input as advisory to elected representatives', 3, 'Best balance - enhances democratic participation while preserving deliberative governance', 'Technology-enhanced representative democracy'),
                            ('D', 'Use digital democracy for some issues, representatives for others', 2, 'Interesting hybrid but could create confusion about legitimacy and process', 'Selective digital democracy with potential institutional confusion')
                        ]
                    },
                    {
                        'order': 16,
                        'category': 'checks',
                        'question_text': 'The military requests a larger role in domestic security, arguing that civilian institutions are too weak to handle modern security challenges. How should democracy respond?',
                        'scenario_context': 'Rising terrorism and civil unrest have strained police capabilities, but expanding military authority raises concerns about civilian control.',
                        'options': [
                            ('A', 'Grant military broader domestic authority to ensure effective security', -3, 'Extremely dangerous to democracy - civilian control of military is fundamental democratic principle', 'Military expansion threatening civilian democratic control'),
                            ('B', 'Strengthen civilian security institutions rather than expanding military role', 3, 'Correct approach - maintains civilian control while addressing security needs', 'Civilian institutional strengthening preserving democratic governance'),
                            ('C', 'Allow temporary military role with strict parliamentary oversight', 1, 'Limited military role with oversight is better but still risks normalizing military domestic presence', 'Temporary military role with democratic oversight'),
                            ('D', 'Create joint civilian-military command structure for domestic security', -1, 'Blurs civilian-military lines and could gradually undermine civilian control', 'Hybrid command structure potentially undermining civilian authority')
                        ]
                    }
                ]
                
                questions_data.extend(final_questions)
                
                self.stdout.write(f"🔄 Creating {len(questions_data)} advanced questions...")
                
                questions_created = 0
                options_created = 0
                
                for q_data in questions_data:
                    # Create question
                    question = ConstitutionQuestion.objects.create(
                        game=game,
                        question_text=q_data['question_text'],
                        category=q_data['category'],
                        scenario_context=q_data['scenario_context'],
                        order=q_data['order'],
                        time_limit=90,  # Longer time for advanced questions
                        learning_module_title='Advanced Constitutional Analysis',
                        learning_module_content='Explore the complex interplay of democratic institutions, constitutional principles, and comparative governance systems.'
                    )
                    questions_created += 1
                    
                    # Create 4 options for each question
                    for option_letter, option_text, score, feedback, governance_principle in q_data['options']:
                        ConstitutionOption.objects.create(
                            question=question,
                            option_letter=option_letter,
                            option_text=option_text,
                            score_value=score,
                            feedback_message=feedback,
                            governance_principle=governance_principle,
                            color_class='blue' if option_letter == 'A' else 'green' if option_letter == 'B' else 'orange' if option_letter == 'C' else 'red'
                        )
                        options_created += 1
                
                self.stdout.write(
                    self.style.SUCCESS(f"✅ Created {questions_created} questions and {options_created} options")
                )
                
                # Add game completion message
                self.stdout.write(
                    self.style.SUCCESS(f"🎉 Advanced Constitution Challenge created successfully!")
                )
                self.stdout.write(f"📊 Game ID: {game.id}")
                self.stdout.write(f"📝 Questions: {questions_created}")
                self.stdout.write(f"⚖️  Options: {options_created} (4 per question)")
                self.stdout.write(f"🎯 Target: Grades 9-12 (Advanced)")
                self.stdout.write("📚 Next step: Run create_advanced_learning_modules command")
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Error creating advanced game: {e}")
            )
            raise