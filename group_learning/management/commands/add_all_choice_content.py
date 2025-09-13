from django.core.management.base import BaseCommand
from group_learning.models import ConstitutionQuestion, ConstitutionOption


class Command(BaseCommand):
    help = 'Add choice-specific dynamic content to ALL Constitution Game options'

    def handle(self, *args, **options):
        self.stdout.write('Adding choice-specific content to ALL Constitution options...')

        # Content for ALL remaining questions - simple and score-aligned
        all_content = {
            # Q4: People's freedoms
            'freedoms_all': {
                'governance_impact': "Your choice ensures equal freedoms for all citizens regardless of background. This creates a strong democratic foundation with protected individual rights.",
                'score_reasoning': f"Governance score increased by +2 points because universal freedoms strengthen democracy and protect all citizens equally.",
                'country_state_changes': "Cities develop diverse communities and civil rights institutions. Economic growth benefits from inclusive policies that attract talent.",
                'societal_impact': "Society becomes more tolerant and diverse. All citizens feel protected and valued, leading to greater social harmony."
            },
            'freedoms_selective': {
                'governance_impact': "Your choice creates unequal freedoms based on loyalty, dividing society into privileged and oppressed groups. This undermines democratic principles.",
                'score_reasoning': f"Governance score decreased by -3 points because selective freedoms violate equal rights and create authoritarian governance.",
                'country_state_changes': "Cities develop segregated areas. Economic development suffers as discrimination reduces productivity and innovation.",
                'societal_impact': "Society becomes divided and fearful. Non-favored groups face oppression while social tensions increase dramatically."
            },
            'freedoms_removable': {
                'governance_impact': "Your choice makes freedoms dependent on leadership whims, creating uncertainty and fear among citizens about their basic rights.",
                'score_reasoning': f"Governance score decreased by -2 points because uncertain rights undermine rule of law and democratic stability.",
                'country_state_changes': "Cities see uneven development as policy uncertainty discourages long-term investment and planning.",
                'societal_impact': "Citizens live in constant fear of losing rights. Self-expression decreases while anxiety about government actions increases."
            },

            # Q5: Criticism of government
            'criticism_punish': {
                'governance_impact': "Your choice to punish criticism creates authoritarian rule where dissent is suppressed and democracy is eliminated.",
                'score_reasoning': f"Governance score decreased by -3 points because punishing criticism destroys free speech and democratic accountability.",
                'country_state_changes': "Cities develop surveillance infrastructure and restricted public spaces. Economic innovation suffers from lack of open debate.",
                'societal_impact': "Citizens become fearful and silent. Innovation and progress decline as people cannot freely discuss problems or solutions."
            },
            'criticism_allowed': {
                'governance_impact': "Your choice protects free speech even when critical, strengthening democratic accountability and government transparency.",
                'score_reasoning': f"Governance score increased by +2 points because free speech enables democratic oversight and improves governance quality.",
                'country_state_changes': "Cities develop vibrant public forums and media centers. Transparent governance attracts investment and skilled residents.",
                'societal_impact': "Citizens become more engaged and informed. Democratic culture flourishes as people can freely discuss and improve their society."
            },
            'criticism_positive_only': {
                'governance_impact': "Your choice allows only positive speech, limiting democratic debate and hiding government problems from public scrutiny.",
                'score_reasoning': f"Governance score decreased by -2 points because restricting criticism prevents democratic accountability and problem-solving.",
                'country_state_changes': "Cities develop censorship systems and limited media. Problems go unaddressed due to lack of open discussion.",
                'societal_impact': "Citizens become less informed about real issues. Society cannot improve as problems are hidden rather than solved."
            },

            # Q6: Group disagreements
            'majority_wins': {
                'governance_impact': "Your choice of majority rule without minority protection can lead to tyranny of the majority and discrimination against smaller groups.",
                'score_reasoning': f"Governance score decreased by -2 points because ignoring minority rights undermines democratic protection of all citizens.",
                'country_state_changes': "Cities develop unequal facilities favoring majority groups. Minority communities face neglect and underdevelopment.",
                'societal_impact': "Minority groups feel excluded and oppressed. Social tensions rise as different groups compete rather than cooperate."
            },
            'minority_protected': {
                'governance_impact': "Your choice protects minority rights while allowing majority decisions, creating balanced democracy that serves all citizens fairly.",
                'score_reasoning': f"Governance score increased by +2 points because minority protection ensures democratic equality and prevents oppression.",
                'country_state_changes': "Cities develop inclusive facilities serving all communities. Diverse development benefits from multiple perspectives.",
                'societal_impact': "All groups feel valued and protected. Social harmony increases as fair compromise builds trust between communities."
            },
            'leaders_ignore': {
                'governance_impact': "Your choice to ignore citizen disagreements shows unresponsive leadership that disconnects government from people's needs.",
                'score_reasoning': f"Governance score decreased by -1 point because ignoring citizen concerns reduces democratic responsiveness and legitimacy.",
                'country_state_changes': "Cities see uneven development as leaders make decisions without community input or understanding local needs.",
                'societal_impact': "Citizens lose trust in government. Civic engagement decreases as people feel their voices don't matter."
            },

            # Q7: Citizen duties
            'no_citizen_duties': {
                'governance_impact': "Your choice eliminates citizen responsibilities, creating one-sided relationship where government serves but citizens don't contribute.",
                'score_reasoning': f"Governance score decreased by -2 points because lack of civic duty undermines democratic participation and social responsibility.",
                'country_state_changes': "Cities struggle with maintenance and development as government lacks citizen support and participation.",
                'societal_impact': "Citizens become entitled and disconnected. Community spirit weakens as people expect benefits without contributing."
            },
            'balanced_duties': {
                'governance_impact': "Your choice balances citizen rights with responsibilities, creating strong democracy where people both benefit from and contribute to society.",
                'score_reasoning': f"Governance score increased by +2 points because balanced civic duties strengthen democratic participation and social contract.",
                'country_state_changes': "Cities thrive as citizens actively participate in development. Public infrastructure improves through citizen cooperation.",
                'societal_impact': "Citizens feel invested in their community. Strong civic culture develops as people understand their role in society."
            },
            'selfish_duties': {
                'governance_impact': "Your choice encourages selfish behavior, weakening social bonds and making collective action for common good nearly impossible.",
                'score_reasoning': f"Governance score decreased by -1 point because selfish civic approach undermines community cooperation and democratic values.",
                'country_state_changes': "Cities see uneven development as citizens only help areas that benefit them personally, neglecting common needs.",
                'societal_impact': "Society becomes fragmented and competitive. Community cooperation decreases while social tensions increase."
            },

            # Q8: Respect for national symbols  
            'respect_symbols': {
                'governance_impact': "Your choice emphasizes citizen duties toward national symbols and property, building patriotic culture and shared responsibility.",
                'score_reasoning': "Governance score increased by +2 points because civic responsibility and respect for public property strengthen democratic institutions.",
                'country_state_changes': "Cities maintain well-preserved public spaces and monuments. National pride drives community investment and care.",
                'societal_impact': "Citizens develop shared identity and pride. Community responsibility increases as people care for common spaces and symbols."
            },
            'only_rights': {
                'governance_impact': "Your choice eliminates civic duties, creating imbalanced democracy where citizens demand benefits without contributing to society.",
                'score_reasoning': "Governance score decreased by -2 points because rights without duties undermines democratic responsibility and social contract.",
                'country_state_changes': "Cities struggle with maintenance and vandalism. Public property deteriorates without citizen care and responsibility.",
                'societal_impact': "Citizens become entitled and irresponsible. Community bonds weaken as people take without giving back."
            },
            'leaders_only_responsible': {
                'governance_impact': "Your choice places all responsibility on leaders while freeing citizens from duties, creating passive democracy without citizen engagement.",
                'score_reasoning': "Governance score decreased by -1 point because citizen disengagement reduces democratic participation and government effectiveness.",
                'country_state_changes': "Cities depend entirely on government resources. Development slows as leaders lack citizen support and involvement.",
                'societal_impact': "Citizens become disconnected from governance. Democratic culture weakens as people don't feel responsible for their community."
            },

            # Q9: Power division
            'power_concentrated': {
                'governance_impact': "Your choice concentrates all power in one group, eliminating checks and balances that prevent abuse of authority.",
                'score_reasoning': "Governance score decreased by -3 points because concentrated power destroys democratic separation of powers and enables tyranny.",
                'country_state_changes': "Cities develop under single authority control. Development becomes unpredictable as one group controls all decisions.",
                'societal_impact': "Citizens lose protection from government abuse. Fear increases as no independent institutions can protect their rights."
            },
            'power_separated': {
                'governance_impact': "Your choice creates separation of powers with different groups for laws, enforcement, and justice, preventing any one group from becoming too powerful.",
                'score_reasoning': "Governance score increased by +2 points because separation of powers creates checks and balances essential for democratic governance.",
                'country_state_changes': "Cities develop balanced institutions. Stable governance with accountability attracts investment and skilled residents.",
                'societal_impact': "Citizens enjoy protection from government abuse. Democratic culture strengthens as institutions check each other's power."
            },
            'judges_follow_orders': {
                'governance_impact': "Your choice makes judges follow leader orders, destroying judicial independence and eliminating protection from unfair laws.",
                'score_reasoning': "Governance score decreased by -2 points because dependent judges cannot protect citizens from government abuse or unfair laws.",
                'country_state_changes': "Cities lack independent legal protection. Arbitrary decisions create uncertainty for businesses and residents.",
                'societal_impact': "Citizens lose legal protection from government abuse. Justice becomes partisan while rule of law disappears."
            },

            # Q10: Oversight of leaders
            'trust_leaders_fully': {
                'governance_impact': "Your choice eliminates oversight of leaders, allowing unchecked power that historically leads to corruption and abuse.",
                'score_reasoning': "Governance score decreased by -3 points because lack of oversight enables corruption and destroys democratic accountability.",
                'country_state_changes': "Cities see unequal development favoring leader preferences. Corruption reduces economic efficiency and fairness.",
                'societal_impact': "Citizens become vulnerable to leader abuse. Corruption increases while trust in government decreases over time."
            },
            'judicial_review': {
                'governance_impact': "Your choice establishes judicial review where independent judges can check unfair laws, protecting citizens from government abuse.",
                'score_reasoning': "Governance score increased by +2 points because judicial oversight prevents government abuse and protects constitutional rights.",
                'country_state_changes': "Cities develop under rule of law protection. Predictable legal framework attracts investment and honest businesses.",
                'societal_impact': "Citizens feel protected from unfair laws. Trust in government increases as independent courts ensure justice."
            },
            'citizen_protest_later': {
                'governance_impact': "Your choice relies on after-the-fact protests, allowing damage before citizens can respond to unfair government actions.",
                'score_reasoning': "Governance score remained at +0 points because delayed response neither prevents abuse nor provides reliable protection.",
                'country_state_changes': "Cities experience periodic unrest and uncertainty. Development suffers from unpredictable government-citizen conflicts.",
                'societal_impact': "Citizens face uncertainty and potential conflict. Social stability decreases as problems are addressed through confrontation."
            },

            # Q11: Changing rules
            'leaders_change_anything': {
                'governance_impact': "Your choice allows leaders to change any rule anytime, creating unpredictable governance where citizens have no stable protections.",
                'score_reasoning': "Governance score decreased by -2 points because arbitrary rule changes destroy legal stability and democratic predictability.",
                'country_state_changes': "Cities face constant policy uncertainty. Businesses and residents cannot plan as rules change without warning.",
                'societal_impact': "Citizens live in uncertainty about their rights and protections. Social stability decreases due to constant rule changes."
            },
            'unanimous_required': {
                'governance_impact': "Your choice requires unanimous agreement for any change, potentially paralyzing government and preventing necessary improvements.",
                'score_reasoning': "Governance score decreased by -1 point because unanimous requirements can prevent necessary democratic improvements and adaptation.",
                'country_state_changes': "Cities struggle to adapt to changing needs. Development stagnates as essential updates become impossible.",
                'societal_impact': "Citizens may suffer from outdated laws that cannot be improved. Democratic progress slows due to decision paralysis."
            },
            'special_process': {
                'governance_impact': "Your choice creates a thoughtful amendment process with discussion and checks, balancing stability with necessary democratic evolution.",
                'score_reasoning': "Governance score increased by +2 points because structured amendment processes enable democratic improvement while maintaining stability.",
                'country_state_changes': "Cities benefit from thoughtful policy evolution. Stable yet adaptable governance attracts long-term investment.",
                'societal_impact': "Citizens enjoy stable rights that can improve over time. Democratic culture strengthens through inclusive change processes."
            },

            # Q12: Country organization  
            'central_only': {
                'governance_impact': "Your choice centralizes all decisions in one government, potentially disconnecting leadership from local needs and reducing efficiency.",
                'score_reasoning': "Governance score decreased by -2 points because over-centralization reduces local responsiveness and democratic participation.",
                'country_state_changes': "Cities develop uniformly but may not address local needs. Central planning may miss regional opportunities.",
                'societal_impact': "Citizens feel disconnected from distant government. Local culture and needs may be ignored by central authorities."
            },
            'federal_system': {
                'governance_impact': "Your choice creates federal system with shared responsibilities, balancing national unity with local autonomy and participation.",
                'score_reasoning': "Governance score increased by +2 points because federalism enables both national coordination and local democratic participation.",
                'country_state_changes': "Cities develop according to local needs while maintaining national standards. Diverse development reflects regional strengths.",
                'societal_impact': "Citizens participate at multiple government levels. Local culture flourishes while national unity is maintained."
            },
            'village_only': {
                'governance_impact': "Your choice eliminates higher coordination, potentially creating chaos as villages cannot address national issues or coordinate effectively.",
                'score_reasoning': "Governance score decreased by -1 point because lack of coordination prevents addressing national challenges and interstate cooperation.",
                'country_state_changes': "Cities develop inconsistently without coordination. National infrastructure and standards become impossible to maintain.",
                'societal_impact': "Citizens may benefit locally but suffer from lack of national cooperation. Interstate problems remain unsolved."
            },

            # Q13: Future planning principles
            'survival_only': {
                'governance_impact': "Your choice focuses only on immediate survival, preventing long-term planning that builds strong democratic institutions and prosperity.",
                'score_reasoning': "Governance score decreased by -2 points because short-term focus prevents building stable democratic institutions and sustainable development.",
                'country_state_changes': "Cities develop haphazardly without long-term planning. Infrastructure and institutions remain weak and temporary.",
                'societal_impact': "Citizens face constant crisis without building toward better future. Society cannot progress beyond immediate survival."
            },
            'comprehensive_goals': {
                'governance_impact': "Your choice includes social goals like education and poverty reduction, building comprehensive democracy that serves all citizen needs.",
                'score_reasoning': "Governance score increased by +2 points because comprehensive planning strengthens democratic institutions and social welfare.",
                'country_state_changes': "Cities develop with education centers and social infrastructure. Long-term planning attracts investment and skilled residents.",
                'societal_impact': "Citizens benefit from education and reduced inequality. Strong social foundation enables democratic participation and prosperity."
            },
            'money_only': {
                'governance_impact': "Your choice prioritizes economic growth over democratic values, potentially creating wealth inequality and weak democratic institutions.",
                'score_reasoning': "Governance score decreased by -1 point because ignoring social welfare and democracy weakens long-term governance stability.",
                'country_state_changes': "Cities may see economic growth but lack social infrastructure. Development benefits some while excluding others.",
                'societal_impact': "Citizens face increased inequality and reduced democratic participation. Social tensions grow as wealth concentrates."
            },

            # Q14: Constitutional promises
            'belongs_to_some': {
                'governance_impact': "Your choice declares the country belongs only to some groups, creating exclusionary nationalism that divides rather than unites citizens.",
                'score_reasoning': "Governance score decreased by -3 points because exclusionary constitution violates democratic equality and creates systematic discrimination.",
                'country_state_changes': "Cities develop segregated communities. Economic development suffers as discrimination reduces talent and cooperation.",
                'societal_impact': "Excluded groups face systematic oppression. Social harmony breaks down as constitution creates first and second-class citizens."
            },
            'democratic_values': {
                'governance_impact': "Your choice promises democracy, justice, liberty and equality, establishing strong foundation for inclusive democratic governance.",
                'score_reasoning': "Governance score increased by +3 points because constitutional commitment to democratic values creates strongest foundation for good governance.",
                'country_state_changes': "Cities develop as inclusive communities. Strong democratic foundation attracts international investment and cooperation.",
                'societal_impact': "All citizens enjoy equal rights and opportunities. Democratic culture flourishes as constitution protects everyone equally."
            },
            'growth_only': {
                'governance_impact': "Your choice focuses only on economic growth, ignoring democratic values that ensure growth benefits all citizens fairly.",
                'score_reasoning': "Governance score decreased by -1 point because growth without democratic values can create inequality and weak institutions.",
                'country_state_changes': "Cities may grow economically but lack democratic infrastructure. Development may be rapid but unstable.",
                'societal_impact': "Citizens may see economic opportunity but lack democratic protections. Growth may not be shared fairly across society."
            },

            # Q15: Religion and government  
            'support_one_religion': {
                'governance_impact': "Your choice makes government support only one religion, violating religious freedom and creating discrimination against other faiths.",
                'score_reasoning': "Governance score decreased by -3 points because religious favoritism violates democratic equality and freedom of religion.",
                'country_state_changes': "Cities develop religious divisions and segregation. Economic development suffers as religious minorities face discrimination.",
                'societal_impact': "Religious minorities face persecution and exclusion. Social harmony breaks down as government creates religious hierarchy."
            },
            'treat_equally': {
                'governance_impact': "Your choice ensures government treats all religions equally while staying neutral, protecting religious freedom for everyone.",
                'score_reasoning': "Governance score increased by +2 points because religious equality and government neutrality strengthen democratic freedom and inclusion.",
                'country_state_changes': "Cities develop diverse religious communities. Religious freedom attracts diverse populations and promotes tolerance.",
                'societal_impact': "All citizens enjoy religious freedom and equal treatment. Society becomes more tolerant and diverse through religious equality."
            },
            'religion_controls_politics': {
                'governance_impact': "Your choice allows religion to control political decisions, mixing religious and government authority in ways that reduce democratic governance.",
                'score_reasoning': "Governance score decreased by -2 points because religious control of politics reduces democratic decision-making and religious freedom.",
                'country_state_changes': "Cities develop under religious authority rather than democratic governance. Policy reflects religious rather than citizen preferences.",
                'societal_impact': "Citizens of different faiths lose equal political participation. Democratic culture weakens as religious authority replaces citizen sovereignty."
            },

            # Q16: Economic inequality
            'reduce_inequality': {
                'governance_impact': "Your choice commits government to reducing inequality and ensuring basic needs, strengthening democratic participation through economic inclusion.",
                'score_reasoning': "Governance score increased by +2 points because addressing inequality strengthens democracy by enabling all citizens to participate fully.",
                'country_state_changes': "Cities develop with reduced inequality and better public services. Inclusive growth creates more stable and prosperous communities.",
                'societal_impact': "Citizens gain equal opportunity and reduced poverty. Democratic participation increases as economic security enables civic engagement."
            },
            'not_government_job': {
                'governance_impact': "Your choice eliminates government responsibility for citizen welfare, potentially creating extreme inequality that undermines democratic participation.",
                'score_reasoning': "Governance score decreased by -2 points because ignoring inequality can create conditions that undermine democratic equality and participation.",
                'country_state_changes': "Cities develop with extreme inequality. Poor areas lack development while wealth concentrates in limited areas.",
                'societal_impact': "Poor citizens cannot participate equally in democracy. Social tensions increase as inequality creates different classes of citizenship."
            },
            'rich_decide_charity': {
                'governance_impact': "Your choice makes social welfare depend on wealthy people's voluntary charity, creating unstable and potentially discriminatory welfare system.",
                'score_reasoning': "Governance score decreased by -1 point because charity-dependent welfare cannot ensure democratic equality or reliable social support.",
                'country_state_changes': "Cities see uneven development depending on wealthy donors' preferences. Public welfare becomes unpredictable and limited.",
                'societal_impact': "Poor citizens depend on wealthy people's generosity rather than democratic rights. Social stability depends on private charity rather than public policy."
            }
        }

        # Add content based on option text patterns
        questions = ConstitutionQuestion.objects.all().order_by('id')
        updated_count = 0

        for question in questions:
            self.stdout.write(f"Processing Q{question.id}: {question.question_text[:50]}...")
            
            options = question.options.all()
            for option in options:
                if option.governance_impact:  # Skip if already has content
                    continue
                    
                option_text_lower = option.option_text.lower()
                content_key = None
                
                # Question 4: Freedoms
                if 'everyone should have freedom' in option_text_lower:
                    content_key = 'freedoms_all'
                elif 'only certain groups get freedoms' in option_text_lower:
                    content_key = 'freedoms_selective'
                elif 'taken away anytime' in option_text_lower:
                    content_key = 'freedoms_removable'
                
                # Question 5: Criticism
                elif 'punished for speaking against' in option_text_lower:
                    content_key = 'criticism_punish'
                elif 'allowed to speak, even if leaders' in option_text_lower:
                    content_key = 'criticism_allowed'
                elif 'only positive speech' in option_text_lower:
                    content_key = 'criticism_positive_only'
                
                # Question 6: Group disagreements
                elif 'bigger group always wins' in option_text_lower:
                    content_key = 'majority_wins'
                elif 'minority group also gets protected' in option_text_lower:
                    content_key = 'minority_protected'
                elif 'ignore the conflict' in option_text_lower:
                    content_key = 'leaders_ignore'
                
                # Question 7: Citizen duties
                elif 'nothing. only the government should' in option_text_lower:
                    content_key = 'no_citizen_duties'
                elif 'obey laws and pay taxes' in option_text_lower:
                    content_key = 'balanced_duties'
                elif 'only if it benefits them personally' in option_text_lower:
                    content_key = 'selfish_duties'
                
                # Question 8: National symbols
                elif 'respect national symbols' in option_text_lower:
                    content_key = 'respect_symbols'
                elif 'only rights, no duties' in option_text_lower:
                    content_key = 'only_rights'
                elif 'leaders alone must take care' in option_text_lower:
                    content_key = 'leaders_only_responsible'
                
                # Question 9: Power division
                elif 'one group of leaders makes laws, enforces them, and judges' in option_text_lower:
                    content_key = 'power_concentrated'
                elif 'different groups—one makes laws, one enforces them, one interprets' in option_text_lower:
                    content_key = 'power_separated'
                elif 'judges just follow orders from them' in option_text_lower:
                    content_key = 'judges_follow_orders'
                
                # Question 10: Leader oversight
                elif 'nobody. leaders should be fully trusted' in option_text_lower:
                    content_key = 'trust_leaders_fully'
                elif 'group of judges who can review and stop unfair laws' in option_text_lower:
                    content_key = 'judicial_review'
                elif 'citizens protest later if something goes wrong' in option_text_lower:
                    content_key = 'citizen_protest_later'
                
                # Question 11: Changing rules
                elif 'leaders can change anything whenever they want' in option_text_lower:
                    content_key = 'leaders_change_anything'
                elif 'citizens must all agree every time' in option_text_lower:
                    content_key = 'unanimous_required'
                elif 'special process with discussion and checks before changes' in option_text_lower:
                    content_key = 'special_process'
                
                # Question 12: Country organization
                elif 'only one central government decides everything' in option_text_lower:
                    content_key = 'central_only'
                elif 'central, regional (states), and local bodies share' in option_text_lower:
                    content_key = 'federal_system'
                elif 'every village should make all decisions without any higher' in option_text_lower:
                    content_key = 'village_only'
                
                # Question 13: Future planning
                elif 'focus only on today\'s survival, forget future' in option_text_lower:
                    content_key = 'survival_only'
                elif 'include goals like free education, reducing poverty' in option_text_lower:
                    content_key = 'comprehensive_goals'
                elif 'only talk about economic growth, nothing else' in option_text_lower:
                    content_key = 'money_only'
                
                # Question 14: Constitutional promises
                elif 'country belongs to some groups' in option_text_lower:
                    content_key = 'belongs_to_some'
                elif 'promise democracy, justice, liberty, equality' in option_text_lower:
                    content_key = 'democratic_values'
                elif 'only talk about economic growth' in option_text_lower:
                    content_key = 'growth_only'
                
                # Question 15: Religion
                elif 'support only one religion' in option_text_lower:
                    content_key = 'support_one_religion'
                elif 'treat all religions equally' in option_text_lower:
                    content_key = 'treat_equally'
                elif 'allow religion to control political' in option_text_lower:
                    content_key = 'religion_controls_politics'
                
                # Question 16: Economic inequality
                elif 'work to reduce inequality and ensure' in option_text_lower:
                    content_key = 'reduce_inequality'
                elif 'not the government\'s job; poor people are on their own' in option_text_lower:
                    content_key = 'not_government_job'
                elif 'only rich people decide on charity' in option_text_lower:
                    content_key = 'rich_decide_charity'
                
                # Add content if we found a match
                if content_key and content_key in all_content:
                    content = all_content[content_key]
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
        
        # Show statistics
        total_options = ConstitutionOption.objects.count()
        options_with_content = ConstitutionOption.objects.exclude(governance_impact='').count()
        
        self.stdout.write(f"Statistics:")
        self.stdout.write(f"  Total options: {total_options}")
        self.stdout.write(f"  Options with dynamic content: {options_with_content}")
        self.stdout.write(f"  Coverage: {(options_with_content/total_options)*100:.1f}%")