#!/usr/bin/env python3
"""
Production script to update Advanced Constitution Challenge questions.
Run this on the production server with: python manage.py shell < update_advanced_questions_production.py
"""

import os
import django
from django.db import transaction
from django.utils import timezone

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'decipherworld.settings.production')
django.setup()

from group_learning.models import Game, ConstitutionQuestion, ConstitutionOption

print("🏛️ Updating Advanced Constitution Challenge Questions on Production...")

try:
    with transaction.atomic():
        # Get the Advanced Constitution Game
        game = Game.objects.filter(
            title="Advanced Constitution Challenge",
            game_type='constitution_challenge',
            is_active=True
        ).first()
        
        if not game:
            print("❌ Advanced Constitution Game not found!")
            exit(1)
        
        print(f"✅ Found Advanced Constitution Game (ID: {game.id})")
        
        # Clear existing questions
        existing_count = ConstitutionQuestion.objects.filter(game=game).count()
        if existing_count > 0:
            print(f"🔄 Clearing {existing_count} existing questions...")
            ConstitutionQuestion.objects.filter(game=game).delete()
        
        # Create sophisticated questions
        questions_data = [
            {
                'order': 1,
                'category': 'governance',
                'question_text': 'Your emerging nation faces a constitutional crisis: the legislature passes a popular but constitutionally questionable emergency powers bill. As the constitutional architect, how should authority be structured to prevent such dilemmas?',
                'scenario_context': 'A natural disaster has struck, and public sentiment supports bypassing normal constitutional procedures for faster relief distribution.',
                'options': [
                    {'letter': 'A', 'text': 'Establish a unitary system where elected officials can act decisively during crises without procedural delays', 'score': -1, 'reasoning': 'Efficient but risks constitutional erosion'},
                    {'letter': 'B', 'text': 'Create a constitutional framework with emergency provisions that maintain checks and balances even during crises', 'score': 3, 'reasoning': 'Balances efficiency with constitutional protection'},
                    {'letter': 'C', 'text': 'Institute absolute popular sovereignty where public referenda can override constitutional limitations during emergencies', 'score': -3, 'reasoning': 'Democratic but enables tyranny of majority'},
                    {'letter': 'D', 'text': 'Design a technocratic system where constitutional experts make decisions during crises, bypassing political processes', 'score': 1, 'reasoning': 'Rational but lacks democratic legitimacy'}
                ]
            },
            {
                'order': 2,
                'category': 'democracy',
                'question_text': 'Your nation must design its electoral system. Recent global experiences show different democratic outcomes based on electoral design. Which approach best ensures both legitimacy and effective governance?',
                'scenario_context': 'Neighboring countries have experienced political instability due to electoral system flaws, and international observers are watching your constitutional choices.',
                'options': [
                    {'letter': 'A', 'text': 'Proportional representation ensuring every vote counts equally, even if it leads to coalition governments', 'score': 1, 'reasoning': 'Fair representation but potential instability'},
                    {'letter': 'B', 'text': 'First-past-the-post system providing clear mandates and strong governments, accepting some vote inequality', 'score': -1, 'reasoning': 'Stable but can ignore minority voices'},
                    {'letter': 'C', 'text': 'Mixed electoral system combining constituency representation with proportional allocation to balance stability and fairness', 'score': 3, 'reasoning': 'Optimal balance of representation and governance'},
                    {'letter': 'D', 'text': 'Meritocratic selection where candidates must pass competency tests before public voting', 'score': -3, 'reasoning': 'Competent but undermines democratic equality'}
                ]
            },
            {
                'order': 3,
                'category': 'rights',
                'question_text': 'Your constitution must address the tension between individual rights and collective security. How should fundamental rights be structured when they conflict with public safety imperatives?',
                'scenario_context': 'Recent terrorist attacks in the region have created public pressure for stronger security measures that may infringe on civil liberties.',
                'options': [
                    {'letter': 'A', 'text': 'Establish absolute rights that cannot be suspended under any circumstances, prioritizing individual dignity', 'score': -1, 'reasoning': 'Principled but potentially impractical in genuine emergencies'},
                    {'letter': 'B', 'text': 'Create a constitutional framework where rights can be temporarily limited through parliamentary supermajority with judicial review', 'score': 3, 'reasoning': 'Balanced approach with democratic and judicial safeguards'},
                    {'letter': 'C', 'text': 'Allow executive suspension of rights during declared emergencies, subject to periodic legislative review', 'score': -3, 'reasoning': 'Efficient but risks authoritarian abuse'},
                    {'letter': 'D', 'text': 'Institute public referenda to decide when rights should be limited for collective security', 'score': 1, 'reasoning': 'Democratic but majority might oppress minorities'}
                ]
            },
            {
                'order': 4,
                'category': 'freedom',
                'question_text': 'Digital age challenges require constitutional adaptation. How should your nation balance freedom of expression with responsibilities in the era of social media and misinformation?',
                'scenario_context': 'Fake news and hate speech online have led to real-world violence, while citizens demand both safety and free expression.',
                'options': [
                    {'letter': 'A', 'text': 'Establish government content regulation agencies to ensure responsible speech while maintaining essential freedoms', 'score': -3, 'reasoning': 'Protective but enables government censorship'},
                    {'letter': 'B', 'text': 'Create constitutional free speech guarantees with narrow exceptions for direct incitement to violence, relying on education over restriction', 'score': 3, 'reasoning': 'Principled approach balancing freedom with minimal necessary restrictions'},
                    {'letter': 'C', 'text': 'Allow private platform self-regulation with government oversight, balancing market freedom with public responsibility', 'score': 1, 'reasoning': 'Pragmatic but inconsistent enforcement'},
                    {'letter': 'D', 'text': 'Mandate truth verification requirements for public communications, prioritizing accuracy over unrestricted expression', 'score': -1, 'reasoning': 'Well-intentioned but who determines truth?'}
                ]
            },
            {
                'order': 5,
                'category': 'dissent',
                'question_text': 'Your government faces sustained public criticism over economic policies. Constitutional provisions must address how democratic systems should handle persistent opposition and criticism.',
                'scenario_context': 'Opposition groups organize continuous protests and criticism campaigns that some argue destabilize governance and investor confidence.',
                'options': [
                    {'letter': 'A', 'text': 'Protect all peaceful criticism as essential democratic feedback, even when it challenges government stability', 'score': 3, 'reasoning': 'Upholds democratic principles of accountability'},
                    {'letter': 'B', 'text': 'Allow criticism but regulate protest timing and locations to balance dissent with public order and economic stability', 'score': 1, 'reasoning': 'Reasonable balance but risks restricting legitimate dissent'},
                    {'letter': 'C', 'text': 'Prohibit destructive criticism that undermines national development, focusing on constructive dialogue', 'score': -3, 'reasoning': 'Stability-focused but defines criticism subjectively'},
                    {'letter': 'D', 'text': 'Establish cooling-off periods during economic crises where criticism is discouraged for national unity', 'score': -1, 'reasoning': 'Crisis management but suspends democratic accountability'}
                ]
            },
            {
                'order': 6,
                'category': 'minority_rights',
                'question_text': 'Your diverse nation must constitutionally address competing group demands. How should the constitution handle situations where majority democratic decisions conflict with minority group rights?',
                'scenario_context': 'A religious minority seeks constitutional protection for their practices, while the majority supports laws that would restrict these practices.',
                'options': [
                    {'letter': 'A', 'text': 'Institute majoritarian democracy where constitutional majority votes determine all policies, including minority issues', 'score': -3, 'reasoning': 'Democratic but enables tyranny of majority'},
                    {'letter': 'B', 'text': 'Create constitutional minority rights protections that cannot be overridden by majority vote, with judicial enforcement', 'score': 3, 'reasoning': 'Protects vulnerable groups while maintaining democratic framework'},
                    {'letter': 'C', 'text': 'Establish proportional representation in all decisions, ensuring minority voices are always heard before majority rules', 'score': 1, 'reasoning': 'Inclusive but may complicate decision-making'},
                    {'letter': 'D', 'text': 'Design separate spheres of autonomy where minorities self-govern in specific areas while majority rules in common areas', 'score': -1, 'reasoning': 'Practical but risks fragmenting national unity'}
                ]
            },
            {
                'order': 7,
                'category': 'civic_duty',
                'question_text': 'Your constitution must define the relationship between citizen rights and responsibilities in a modern democratic state. How should constitutional obligations be structured?',
                'scenario_context': 'Citizens enjoy extensive rights but civic participation is declining, and some argue this threatens democratic sustainability.',
                'options': [
                    {'letter': 'A', 'text': 'Mandate civic participation through constitutional requirements like voting, jury service, and community engagement', 'score': -1, 'reasoning': 'Promotes engagement but coerces participation'},
                    {'letter': 'B', 'text': 'Establish voluntary civic duties with incentives, respecting individual choice while encouraging participation', 'score': 3, 'reasoning': 'Balances civic health with personal freedom'},
                    {'letter': 'C', 'text': 'Focus solely on negative rights (freedoms from interference) without imposing positive duties on citizens', 'score': 1, 'reasoning': 'Libertarian but may weaken civic bonds'},
                    {'letter': 'D', 'text': 'Create hierarchical citizenship with enhanced rights for those fulfilling greater civic responsibilities', 'score': -3, 'reasoning': 'Incentivizes engagement but creates unequal citizenship'}
                ]
            },
            {
                'order': 8,
                'category': 'national_symbols',
                'question_text': 'National symbols and heritage require constitutional treatment in your pluralistic society. How should the constitution address respect for national symbols while accommodating diverse beliefs?',
                'scenario_context': 'Some citizens view flag burning as legitimate protest, while others see it as unpatriotic disrespect requiring constitutional prohibition.',
                'options': [
                    {'letter': 'A', 'text': 'Protect symbolic speech as fundamental expression, allowing flag burning and similar acts as legitimate protest forms', 'score': 1, 'reasoning': 'Upholds free expression but may offend patriotic sentiment'},
                    {'letter': 'B', 'text': 'Balance symbolic protection with expression rights, prohibiting destruction while allowing verbal criticism of symbols', 'score': 3, 'reasoning': 'Reasonable compromise protecting both expression and national symbols'},
                    {'letter': 'C', 'text': 'Mandate constitutional respect for national symbols as essential for national unity and identity', 'score': -1, 'reasoning': 'Promotes unity but restricts expression rights'},
                    {'letter': 'D', 'text': 'Allow majority communities to determine symbol respect requirements through local democratic processes', 'score': -3, 'reasoning': 'Democratic but creates inconsistent rights across regions'}
                ]
            },
            {
                'order': 9,
                'category': 'separation_of_powers',
                'question_text': 'Your constitutional design must address modern governance complexity. How should powers be separated to ensure both effectiveness and accountability in contemporary government?',
                'scenario_context': 'Traditional separation faces challenges from complex policy issues requiring expertise, speed, and coordination across branches.',
                'options': [
                    {'letter': 'A', 'text': 'Maintain strict separation with limited inter-branch cooperation, prioritizing accountability over efficiency', 'score': 1, 'reasoning': 'Prevents abuse but may hinder effective governance'},
                    {'letter': 'B', 'text': 'Design flexible separation allowing cooperative governance while maintaining core checks and balances', 'score': 3, 'reasoning': 'Adapts to modern needs while preserving constitutional safeguards'},
                    {'letter': 'C', 'text': 'Create specialized technocratic branches for complex issues, separating expertise from politics', 'score': -1, 'reasoning': 'Improves expertise but weakens democratic accountability'},
                    {'letter': 'D', 'text': 'Centralize authority in elected executive for decisive action, with post-hoc legislative and judicial review', 'score': -3, 'reasoning': 'Enables quick decisions but risks executive overreach'}
                ]
            },
            {
                'order': 10,
                'category': 'judicial_review',
                'question_text': 'Constitutional interpretation requires institutional design. How should your nation structure judicial authority to balance legal expertise with democratic legitimacy?',
                'scenario_context': 'Courts must interpret constitutional meaning, but critics argue unelected judges shouldn\'t override democratic decisions.',
                'options': [
                    {'letter': 'A', 'text': 'Establish strong judicial review with life tenure, ensuring independence from political pressure in constitutional interpretation', 'score': 1, 'reasoning': 'Protects rule of law but may lack democratic accountability'},
                    {'letter': 'B', 'text': 'Create constitutional courts with democratic appointment processes and term limits, balancing expertise with accountability', 'score': 3, 'reasoning': 'Optimal balance of independence and democratic legitimacy'},
                    {'letter': 'C', 'text': 'Allow parliamentary override of judicial decisions through supermajority votes, maintaining legislative supremacy', 'score': -1, 'reasoning': 'Democratic but may weaken constitutional protection'},
                    {'letter': 'D', 'text': 'Submit controversial constitutional interpretations to popular referenda, ensuring direct democratic input', 'score': -3, 'reasoning': 'Democratic but complex legal issues unsuitable for mass voting'}
                ]
            },
            {
                'order': 11,
                'category': 'constitutional_amendment',
                'question_text': 'Constitutional adaptation requires amendment procedures. How should your constitution balance stability with necessary evolution in changing circumstances?',
                'scenario_context': 'Society faces new challenges like climate change and artificial intelligence that weren\'t anticipated by constitutional framers.',
                'options': [
                    {'letter': 'A', 'text': 'Require broad consensus through multiple supermajorities and time delays, ensuring stability over quick adaptation', 'score': 1, 'reasoning': 'Prevents hasty changes but may impede necessary updates'},
                    {'letter': 'B', 'text': 'Design graduated amendment procedures with different requirements based on the constitutional provision\'s importance', 'score': 3, 'reasoning': 'Balances stability with adaptability appropriately'},
                    {'letter': 'C', 'text': 'Allow simple legislative majorities to amend constitution, ensuring democratic responsiveness to changing needs', 'score': -3, 'reasoning': 'Responsive but undermines constitutional stability'},
                    {'letter': 'D', 'text': 'Prohibit amendments to core constitutional principles while allowing procedural updates through easier processes', 'score': -1, 'reasoning': 'Protects fundamentals but who defines core principles?'}
                ]
            },
            {
                'order': 12,
                'category': 'federalism',
                'question_text': 'Your large, diverse nation requires governance structure. How should constitutional federalism address the tension between national unity and local autonomy?',
                'scenario_context': 'Different regions have varying economic development, cultural practices, and political preferences, creating demands for both unity and autonomy.',
                'options': [
                    {'letter': 'A', 'text': 'Establish asymmetric federalism allowing different regions varying degrees of autonomy based on their specific needs', 'score': -1, 'reasoning': 'Flexible but creates unequal citizenship across regions'},
                    {'letter': 'B', 'text': 'Create uniform federal system with equal state powers and clear division of responsibilities between levels', 'score': 3, 'reasoning': 'Provides clarity and equality while respecting diversity'},
                    {'letter': 'C', 'text': 'Design confederate system with minimal central authority, maximizing local self-governance', 'score': 1, 'reasoning': 'Respects local autonomy but may weaken national capacity'},
                    {'letter': 'D', 'text': 'Maintain unitary system with devolved administration, ensuring national consistency while allowing local implementation', 'score': -3, 'reasoning': 'Ensures unity but suppresses legitimate regional differences'}
                ]
            },
            {
                'order': 13,
                'category': 'social_justice',
                'question_text': 'Your constitution must address societal inequalities. How should constitutional provisions balance individual merit with collective social justice imperatives?',
                'scenario_context': 'Historical discrimination has created persistent inequalities, but preferential policies face criticism for potentially undermining merit-based opportunities.',
                'options': [
                    {'letter': 'A', 'text': 'Mandate equality of opportunity only, ensuring fair competition while accepting unequal outcomes based on merit', 'score': -1, 'reasoning': 'Fair process but ignores structural disadvantages'},
                    {'letter': 'B', 'text': 'Establish temporary affirmative measures with sunset clauses, addressing historical injustices while working toward merit-based society', 'score': 3, 'reasoning': 'Balances justice with long-term fairness'},
                    {'letter': 'C', 'text': 'Constitutionally guarantee equality of outcomes through permanent redistribution and quotas', 'score': -3, 'reasoning': 'Addresses inequality but may undermine incentives and merit'},
                    {'letter': 'D', 'text': 'Focus on universal social programs benefiting all citizens equally, avoiding group-specific preferences', 'score': 1, 'reasoning': 'Inclusive but may not address specific historical injustices'}
                ]
            },
            {
                'order': 14,
                'category': 'preamble',
                'question_text': 'Your constitutional preamble must articulate national values and aspirations. Which formulation best captures the balance between idealism and practical governance?',
                'scenario_context': 'The preamble will guide constitutional interpretation and national identity, requiring careful balance between inspiring vision and achievable goals.',
                'options': [
                    {'letter': 'A', 'text': 'Declare aspirational goals like justice, liberty, equality, and fraternity without specific implementation timelines', 'score': 3, 'reasoning': 'Inspirational framework allowing flexible interpretation and implementation'},
                    {'letter': 'B', 'text': 'Focus on practical governance objectives like economic development, public order, and administrative efficiency', 'score': -1, 'reasoning': 'Practical but lacks moral inspiration and higher purpose'},
                    {'letter': 'C', 'text': 'Emphasize cultural and historical identity, prioritizing national heritage and traditional values', 'score': 1, 'reasoning': 'Builds identity but may exclude diverse populations'},
                    {'letter': 'D', 'text': 'Promise specific measurable outcomes like poverty elimination, universal education, and healthcare within set timeframes', 'score': -3, 'reasoning': 'Concrete but risks constitutional failure if goals prove unachievable'}
                ]
            },
            {
                'order': 15,
                'category': 'secularism',
                'question_text': 'Religious diversity requires constitutional accommodation. How should your secular state navigate the complex relationship between religion and governance in a pluralistic society?',
                'scenario_context': 'Multiple religious communities seek both protection for their practices and influence in public policy, while secular citizens want religion-free governance.',
                'options': [
                    {'letter': 'A', 'text': 'Maintain strict church-state separation, prohibiting all religious influence in public policy and government support for religious institutions', 'score': 1, 'reasoning': 'Clear separation but may alienate religious communities'},
                    {'letter': 'B', 'text': 'Practice principled distance - no official religion but engagement with religious communities on social issues while maintaining secular governance', 'score': 3, 'reasoning': 'Balances secular governance with religious accommodation'},
                    {'letter': 'C', 'text': 'Allow democratic processes to determine religious influence in public life, respecting majority religious preferences', 'score': -3, 'reasoning': 'Democratic but enables religious majority dominance'},
                    {'letter': 'D', 'text': 'Establish official multiculturalism with equal government support for all major religions and secular worldviews', 'score': -1, 'reasoning': 'Inclusive but complex to implement fairly'}
                ]
            },
            {
                'order': 16,
                'category': 'economic_justice',
                'question_text': 'Constitutional approaches to economic inequality require careful balance. How should your constitution address wealth disparities while maintaining economic dynamism?',
                'scenario_context': 'Growing inequality threatens social cohesion, but heavy redistribution might discourage investment and economic growth necessary for overall prosperity.',
                'options': [
                    {'letter': 'A', 'text': 'Guarantee maximum permissible wealth ratios and mandatory redistribution to ensure economic equality', 'score': -3, 'reasoning': 'Addresses inequality but may stifle economic growth and innovation'},
                    {'letter': 'B', 'text': 'Establish constitutional rights to basic necessities with progressive taxation funding universal social services', 'score': 3, 'reasoning': 'Ensures dignity while maintaining economic incentives'},
                    {'letter': 'C', 'text': 'Protect property rights and free markets, trusting economic growth to eventually benefit all citizens', 'score': -1, 'reasoning': 'Promotes growth but may perpetuate inequality'},
                    {'letter': 'D', 'text': 'Create cooperative economic sectors alongside private enterprise, diversifying economic organization', 'score': 1, 'reasoning': 'Innovative approach but uncertain practical outcomes'}
                ]
            }
        ]
        
        # Create questions and options
        for q_data in questions_data:
            question = ConstitutionQuestion.objects.create(
                game=game,
                order=q_data['order'],
                category=q_data['category'],
                question_text=q_data['question_text'],
                scenario_context=q_data['scenario_context'],
                is_active=True
            )
            
            for opt_data in q_data['options']:
                ConstitutionOption.objects.create(
                    question=question,
                    option_letter=opt_data['letter'],
                    option_text=opt_data['text'],
                    score_value=opt_data['score'],
                    score_reasoning=opt_data['reasoning'],
                    is_active=True
                )
            
            print(f"✅ Created sophisticated question {q_data['order']}: {q_data['category']}")
        
        print(f"🎉 Successfully created {len(questions_data)} sophisticated constitution questions!")
        print(f"📊 Scoring system: Each question has one +3, one -3, one +1, and one -1 option")
        print(f"🧠 Focus: Constitutional principles, democracy, secularism with nuanced scenarios")
        
except Exception as e:
    print(f"❌ Error: {str(e)}")
    raise e