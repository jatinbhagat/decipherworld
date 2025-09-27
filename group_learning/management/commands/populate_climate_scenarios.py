from django.core.management.base import BaseCommand
from group_learning.models import (
    ClimateGame, ClimateScenario, ClimateQuestion, ClimateOption
)


class Command(BaseCommand):
    help = 'Populate climate game scenarios and questions'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Creating Climate Crisis India game...'))
        
        # Create the main climate game
        climate_game, created = ClimateGame.objects.get_or_create(
            title="Climate Crisis India",
            defaults={
                'subtitle': "Navigate India's climate challenges through role-based decision making",
                'game_type': 'environmental',
                'description': "A 5-round multiplayer simulation where students play as Government Officials, Business Owners, Farmers, Urban Citizens, and NGO Workers to navigate real climate challenges across Delhi, Mumbai, Chennai, migration crises, and national elections.",
                'context': "India faces mounting climate challenges from air pollution in Delhi to floods in Mumbai, water scarcity in Chennai, climate migration, and the need for national policy coordination. This game simulates the complex trade-offs faced by different stakeholders.",
                'min_players': 5,
                'max_players': 100,
                'estimated_duration': 45,
                'difficulty_level': 3,
                'target_age_min': 14,
                'target_age_max': 18,
                'is_active': True
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created climate game: {climate_game.title}'))
        else:
            self.stdout.write(self.style.WARNING(f'Climate game already exists: {climate_game.title}'))

        # Define all scenarios and their questions
        scenarios_data = [
            {
                'round_number': 1,
                'title': 'Delhi Air Pollution Crisis',
                'context_description': 'Delhi chokes under severe air pollution. AQI levels reach 500+ (hazardous). Schools close, flights diverted. The smog crisis demands immediate action from all stakeholders.',
                'news_quotes': [
                    '"Delhi air quality hits emergency levels, visibility drops to 50 meters" - Times of India',
                    '"Children hospitalized as pollution soars beyond safe limits" - NDTV',
                    '"Farmers burn stubble as winter approaches, adding to Delhi smog" - Hindu'
                ],
                'potential_consequences': [
                    'Public health emergency with respiratory diseases spiking',
                    'Economic disruption as outdoor activities shut down',
                    'Social tensions between urban residents and rural farmers'
                ],
                'questions': [
                    {
                        'role': 'government',
                        'question_text': 'As a Government Official, Delhi\'s air quality has reached emergency levels. What is your immediate response?',
                        'options': [
                            ('a', 'Enforce bans on vehicles/construction', 'Delhi\'s economy may slow, day laborers lose jobs, protests erupt.'),
                            ('b', '"Odd-even" traffic + partial bans', 'Reduces congestion modestly, blamed as half-measure, public angry at inconvenience.'),
                            ('c', 'Blame stubble burning, launch inquiry', 'Buys time, but rural-urban resentment rises, media exposes inaction.'),
                            ('d', 'Incentives for e-vehicles/clean industries, delay real enforcement', 'Attractive to business, but public outcry for immediate results.')
                        ]
                    },
                    {
                        'role': 'business',
                        'question_text': 'As a Business Owner, the pollution crisis is affecting your operations and workers. How do you respond?',
                        'options': [
                            ('a', 'Fund remote work, suspend delivery fleet', 'Production halts, jobs cut, survive media praise, stockholders unhappy.'),
                            ('b', 'Lobby for relaxed norms', 'Short-term gains, but risk deeper anger from citizens/NGOs if air worsens.'),
                            ('c', 'PR campaign, tree planting', 'Looks green, but staff/middle managers privately angry about no real action.'),
                            ('d', 'Give away masks, fund smog clinics, blame agri sector', 'Deflects blame, but farmer protests target factories next.')
                        ]
                    },
                    {
                        'role': 'farmer',
                        'question_text': 'As a Farmer, you need to clear crop residue but are blamed for Delhi\'s smog. What do you do?',
                        'options': [
                            ('a', 'Join subsidy for non-burning', 'Reduces air pollution, but must pay for labor/tools, and neighbors may not join—risk crop loss.'),
                            ('b', 'Burn crop residue', 'Saves on labor/money, but could be fined, and city anger increases—threat of legal action.'),
                            ('c', 'Protest in Delhi for compensation', 'Draws media, but crops left neglected—family suffers, risk political detention.'),
                            ('d', 'Seek NGO\'s help for tech', 'May get support, but process is slow and irregular, may miss sowing window.')
                        ]
                    },
                    {
                        'role': 'urban_citizen',
                        'question_text': 'As an Urban Citizen, you and your family are suffering from the toxic air. How do you respond?',
                        'options': [
                            ('a', 'Petition MLA, participate in citizen jury', 'Long, tedious process, may alienate neighborhood, but could start real change.'),
                            ('b', 'Buy expensive air purifiers, stay indoors', 'Family\'s health improves but prices soar, poor neighbors left out, guilt rises.'),
                            ('c', 'Organize "No Car Week"', 'Saves air but disrupts businesses, sparks public argument, can go viral—may become a model.'),
                            ('d', 'Blame farmers online', 'Instant relief, but inflames rural-urban divide—could lead to counter-protests, loss of food supply confidence.')
                        ]
                    },
                    {
                        'role': 'ngo_worker',
                        'question_text': 'As an NGO Worker, you need to address both immediate health impacts and long-term solutions. What\'s your approach?',
                        'options': [
                            ('a', 'Large-scale awareness campaign', 'Broad impact, but resources stretched thin, risk burnout/no tangible solution.'),
                            ('b', 'Pressure government for "green" subsidies to farmers', 'If not carefully targeted, scams/fraud possible, budget overruns.'),
                            ('c', 'Partner with business for green corridors', 'PR value, but could be accused of greenwashing.'),
                            ('d', 'Mediate between camps', 'Risk that both sides see you as biased, slow progress, but sometimes foster real breakthrough.')
                        ]
                    }
                ]
            },
            {
                'round_number': 2,
                'title': 'Mumbai Floods',
                'context_description': 'Unprecedented monsoon rains flood Mumbai. The financial capital comes to a standstill as streets turn into rivers, trains stop, and lives are lost.',
                'news_quotes': [
                    '"Mumbai under water: Record rainfall brings city to standstill" - Indian Express',
                    '"Hundreds stranded as local trains suspended across Mumbai" - Mumbai Mirror',
                    '"Climate change intensifies urban flooding across coastal cities" - Down to Earth'
                ],
                'potential_consequences': [
                    'Economic losses as India\'s financial capital shuts down',
                    'Loss of life and property in vulnerable slum areas',
                    'Infrastructure damage requiring massive reconstruction'
                ],
                'questions': [
                    {
                        'role': 'government',
                        'question_text': 'As a Government Official, Mumbai is flooding and rescue operations are critical. How do you deploy resources?',
                        'options': [
                            ('a', 'Mobilize emergency funds', 'Roads/recovery speed up, but other services (education/health) lose funding.'),
                            ('b', 'Only prioritize economic districts', 'Business recovers, but poor die/homes lost—future instability.'),
                            ('c', 'Appeal to national govt/blame opposition', 'Delays, press covers "blame game," rescue lags.'),
                            ('d', 'Mobilize volunteers for city reforestation', 'Long-term impact, but short-term people furious; morale boost for youth.')
                        ]
                    },
                    {
                        'role': 'business',
                        'question_text': 'As a Business Owner, flooding has disrupted your operations and threatened your workforce. What\'s your priority?',
                        'options': [
                            ('a', 'Sustainable factory drainage investment', 'Major upfront cost, but sets new sector standard—may get media love.'),
                            ('b', 'Compensation demand', 'Buys short-term time, but risks collapse if aid delayed.'),
                            ('c', 'Lobby for quick reopen, ignore root causes', 'Restarts profit, but if new floods occur, heavy blame.'),
                            ('d', 'Clean up city, demand green tax credit', 'Helps society, but may anger other businesses that can\'t afford it.')
                        ]
                    },
                    {
                        'role': 'farmer',
                        'question_text': 'As a Farmer, your crops are flooded and roads to markets are damaged. How do you cope?',
                        'options': [
                            ('a', 'Road repair threats', 'Could backfire, slow restoration as police intervene.'),
                            ('b', 'Fire-sale crops', 'Prevents rot, but makes community food affordable; big personal financial pain.'),
                            ('c', 'Donate to urban relief', 'Feels good, but increases family hardship, earns city sympathy.'),
                            ('d', 'Enter urban farming', 'New skills, harder to adapt, but more resilient if city collaborates.')
                        ]
                    },
                    {
                        'role': 'urban_citizen',
                        'question_text': 'As an Urban Citizen, your neighborhood is flooded and emergency services are overwhelmed. What do you do?',
                        'options': [
                            ('a', 'Volunteer for rescue', 'Direct help, but personal risks, delayed work/school.'),
                            ('b', 'Social media pressure', 'Guilty satisfaction, may get quick response, also easy to be ignored.'),
                            ('c', 'Move to unaffected area', 'Safer, but community bonds weaken, "elite" perception increases.'),
                            ('d', 'Organize local business–citizen supply drives', 'Success if coordinated, if not, chaos/blame.')
                        ]
                    },
                    {
                        'role': 'ngo_worker',
                        'question_text': 'As an NGO Worker, immediate relief is needed but you also see systemic urban planning failures. Where do you focus?',
                        'options': [
                            ('a', 'Direct rescue & relief', 'Frontline effort, but burnout/high risk to staff, limited to short term.'),
                            ('b', 'Document, advocate for change', 'Good for policy but can seem aloof/ineffective.'),
                            ('c', 'Partner with businesses', 'Could multiply impact, but risk company hijack for PR.'),
                            ('d', 'Petition for nature-based solutions', 'Slow, but if enough buy-in, sets new paradigm; may lose immediate trust.')
                        ]
                    }
                ]
            },
            {
                'round_number': 3,
                'title': 'Chennai Water Shortage',
                'context_description': 'Chennai faces Day Zero - reservoirs dry up, groundwater depleted. The IT capital struggles as millions line up for water tankers while industries shut down.',
                'news_quotes': [
                    '"Chennai\'s Day Zero: Major reservoirs hit dead storage level" - The Hindu',
                    '"IT companies relocate employees as water crisis deepens" - Economic Times',
                    '"Groundwater levels at all-time low across Tamil Nadu" - India Today'
                ],
                'potential_consequences': [
                    'Mass migration from the city as water runs out',
                    'Industrial shutdown and economic collapse',
                    'Social unrest and conflicts over water distribution'
                ],
                'questions': [
                    {
                        'role': 'government',
                        'question_text': 'As a Government Official, Chennai is running out of water and you must ration what\'s left. How do you allocate it?',
                        'options': [
                            ('a', 'Limit water for factories + farms', 'Immediate shortage anger/protests, long-term supply stabilizes.'),
                            ('b', 'Hire private tankers', 'Quick fix, but costs skyrocket, scams flourish, deepening crisis.'),
                            ('c', 'Rainwater harvesting campaign', 'Takes years, but if citizens join now, shows true leadership.'),
                            ('d', 'Blame other regions', 'Reduces pressure on city managers, but stokes inter-state tensions, courts involved.')
                        ]
                    },
                    {
                        'role': 'business',
                        'question_text': 'As a Business Owner, water shortage threatens your operations. How do you adapt your business?',
                        'options': [
                            ('a', 'Recycle/reduce water, shut lines', 'Staff protests, upskilling needed, risk revenue.'),
                            ('b', 'Pay for tankers, raise prices', 'Keep running, but public outrage over "water mafia."'),
                            ('c', 'Partner with NGOs for community effort', 'Cost shares, new bonds, if not managed, leads to blame game.'),
                            ('d', 'Demand priority access', 'Government may support, but can provoke riots/negative media.')
                        ]
                    },
                    {
                        'role': 'farmer',
                        'question_text': 'As a Farmer, your wells are dry and crops are failing. How do you survive this drought?',
                        'options': [
                            ('a', 'Shift crops', 'Risky, needs new investments, may inspire others, or backfire if market rejects.'),
                            ('b', 'Insist on water priority', 'Could succeed if urban businesses support; otherwise, painted as selfish.'),
                            ('c', 'Drill illegal wells', 'Immediate fix, but environmental disaster risk, government clampdown.'),
                            ('d', 'Join shared food-infrastructure', 'New sales channel, may lose influence with traditional buyers.')
                        ]
                    },
                    {
                        'role': 'urban_citizen',
                        'question_text': 'As an Urban Citizen, water is rationed and your family\'s daily life is disrupted. How do you respond?',
                        'options': [
                            ('a', 'Water rationing at home', 'Quality of life drops, bills go down, neighbors may disagree/resent changes.'),
                            ('b', 'Hoard water', 'Short-term safety, worsens crisis for all.'),
                            ('c', 'Community water management', 'Only works if trust; risk of argument; success brings praise.'),
                            ('d', 'Mass protest', 'Gets attention, can get violent, pressure mounts for hasty solutions over lasting ones.')
                        ]
                    },
                    {
                        'role': 'ngo_worker',
                        'question_text': 'As an NGO Worker, you see both immediate water needs and long-term mismanagement. Where do you intervene?',
                        'options': [
                            ('a', 'Education effort', 'Slow results, staff burnout, but generational change.'),
                            ('b', 'Pressure for farm/corporate limits', 'Rural/city blowback likely, but structural shifts possible.'),
                            ('c', 'Coordinate water trains', 'Success hinges on business/farm cooperation, may be sabotaged.'),
                            ('d', 'Lobby for big projects', 'If successful, legacy project; if not, massive wasted funds.')
                        ]
                    }
                ]
            },
            {
                'round_number': 4,
                'title': 'Migration & Heatwave',
                'context_description': 'Record-breaking heatwaves trigger mass migration to cities. Rural areas become uninhabitable while urban infrastructure buckles under the influx of climate refugees.',
                'news_quotes': [
                    '"Temperature hits 50°C: Mass migration from rural areas begins" - NDTV',
                    '"Climate refugees overwhelm urban infrastructure" - Indian Express',
                    '"Agricultural collapse forces farmers to abandon ancestral lands" - Down to Earth'
                ],
                'potential_consequences': [
                    'Urban infrastructure collapse under migrant pressure',
                    'Social tensions between locals and migrants',
                    'Complete abandonment of rural agricultural areas'
                ],
                'questions': [
                    {
                        'role': 'government',
                        'question_text': 'As a Government Official, millions are migrating to cities due to extreme heat. How do you manage this crisis?',
                        'options': [
                            ('a', 'Massive job schemes', 'Budget strain, could boost youth morale.'),
                            ('b', 'Demolish informal settlements', 'Frees land, triggers unrest/negative global headlines.'),
                            ('c', 'Tax breaks for businesses hiring migrants', 'If not monitored, may enable abuse.'),
                            ('d', 'Border restrictions', 'Less stress, but black market for entry rises, suffering increases.')
                        ]
                    },
                    {
                        'role': 'business',
                        'question_text': 'As a Business Owner, desperate migrants are seeking work while urban residents feel threatened. How do you manage your workforce?',
                        'options': [
                            ('a', 'Hire & upskill migrants', 'Reputation grows, training costs spike, competition with urban poor.'),
                            ('b', 'Cheap labor, cut benefits', 'Savings, protests/unrest likely, possible legal suits.'),
                            ('c', 'Lobby for wage supports', 'Slows layoffs, government may balk.'),
                            ('d', 'Ignore, automate more jobs', 'Short-term savings, long-term instability.')
                        ]
                    },
                    {
                        'role': 'farmer',
                        'question_text': 'As a Farmer, extreme heat makes farming impossible and you consider leaving your ancestral land. What do you do?',
                        'options': [
                            ('a', 'Cooperate on land', 'Higher yields, social capital gains, needs deep trust.'),
                            ('b', 'Lease to corporates', 'Guaranteed income, could lose local power.'),
                            ('c', 'Switch to livestock', 'Drought-resilient, new disease/expertise risks.'),
                            ('d', 'Migrate', 'Hope for better income, risk of exploitation.')
                        ]
                    },
                    {
                        'role': 'urban_citizen',
                        'question_text': 'As an Urban Citizen, climate migrants are arriving in your neighborhood. Services are stretched and tensions are rising. How do you respond?',
                        'options': [
                            ('a', 'Volunteer, support migrants', 'Builds goodwill, stretches personal time/resources.'),
                            ('b', 'Lobby for tough policy', 'City stabilizes but hardens social divides—can backfire at election.'),
                            ('c', 'Community kitchens', 'Spreads goodwill, high energy needed, theft risk.'),
                            ('d', 'Protest cost/rent hikes', 'Visible, but root causes remain unsolved.')
                        ]
                    },
                    {
                        'role': 'ngo_worker',
                        'question_text': 'As an NGO Worker, you witness both the humanitarian crisis and structural inequalities. How do you help?',
                        'options': [
                            ('a', 'Skills-up programs', 'Can transform lives, but slow impact.'),
                            ('b', 'Advocate for inclusive city planning', 'If blocked, gets nowhere; if not, legacy change.'),
                            ('c', 'Industry partnerships', 'Growth, but criticized by hardline activists.'),
                            ('d', 'Human rights monitor', 'Policy change possible, may create government pushback.')
                        ]
                    }
                ]
            },
            {
                'round_number': 5,
                'title': 'National Election/Policy',
                'context_description': 'National elections approach as climate disasters mount. Parties promise solutions while society demands action. The future of India\'s climate response hangs in the balance.',
                'news_quotes': [
                    '"Climate change becomes key election issue for first time" - Times of India',
                    '"Voters demand concrete action on environmental disasters" - Hindu',
                    '"Young voters prioritize climate policy in election surveys" - Indian Express'
                ],
                'potential_consequences': [
                    'Political deadlock preventing climate action',
                    'Policy reversals undermining progress made',
                    'Social fragmentation along climate action lines'
                ],
                'questions': [
                    {
                        'role': 'government',
                        'question_text': 'As a Government Official, elections are approaching and climate policy is a major issue. What\'s your electoral strategy?',
                        'options': [
                            ('a', 'Big climate promises', 'Win global praise, opposition claws at "anti-poor" image.'),
                            ('b', 'Focus on economy, scale back climate', 'Short-term applause, risk long-term instability/health crises.'),
                            ('c', 'Cross-sector panel', 'Process takes time, if done, wins huge trust; if rushed, fails.'),
                            ('d', 'Blame rivals', 'No vision, but can win populist votes.')
                        ]
                    },
                    {
                        'role': 'business',
                        'question_text': 'As a Business Owner, new climate policies could reshape your industry. How do you influence the electoral outcome?',
                        'options': [
                            ('a', 'Invest in green tech', 'Expenses now, long-term leader.'),
                            ('b', 'Fund rollback campaigns', 'Win quick stability, risk climate activist backlash/boycott.'),
                            ('c', 'Push climate council', 'If cross-sector, stabilizes economy/environment; if not, gets diluted.'),
                            ('d', 'Do nothing', 'Survive short term, risk falling behind as rules change.')
                        ]
                    },
                    {
                        'role': 'farmer',
                        'question_text': 'As a Farmer, climate policies will directly affect your livelihood and agricultural practices. How do you make your voice heard?',
                        'options': [
                            ('a', 'Climate-farm lobby', 'If united, gain leverage; if divided, ignored.'),
                            ('b', 'Demand cash', 'If met, instant relief, long-term unsustainable.'),
                            ('c', 'Support eco parties', 'Win if parties are real; if not, feel betrayed.'),
                            ('d', 'Supply strike', 'Cripples city, but angers customers, threats escalate.')
                        ]
                    },
                    {
                        'role': 'urban_citizen',
                        'question_text': 'As an Urban Citizen, you\'ve experienced climate impacts firsthand. How do you use your vote to drive change?',
                        'options': [
                            ('a', 'Canvass climate candidates', 'Builds momentum, risk resistance from status quo.'),
                            ('b', 'Economic protest', 'Louder voice, risks dividing climate community.'),
                            ('c', 'Urban-rural campaign', 'If successful, major empathy; else, infighting.'),
                            ('d', 'Demand freebies', 'Short-term joy, long-term harm, increases mistrust.')
                        ]
                    },
                    {
                        'role': 'ngo_worker',
                        'question_text': 'As an NGO Worker, this election could determine India\'s climate future. How do you maximize impact?',
                        'options': [
                            ('a', 'Grand coalition', 'Huge impact if everyone buys in; nightmare if someone breaks trust.'),
                            ('b', 'Resilience pilots', 'Can inspire, but small scale.'),
                            ('c', 'Monitor all pledges', 'Transparency, may get ignored, but builds data for future.'),
                            ('d', 'Media blitz', 'Quick fame, fades post-election unless foundation is solid.')
                        ]
                    }
                ]
            }
        ]

        # Create scenarios and questions
        for scenario_data in scenarios_data:
            scenario, created = ClimateScenario.objects.get_or_create(
                game=climate_game,
                round_number=scenario_data['round_number'],
                defaults={
                    'title': scenario_data['title'],
                    'context_description': scenario_data['context_description'],
                    'news_quotes': scenario_data['news_quotes'],
                    'potential_consequences': scenario_data['potential_consequences'],
                }
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created scenario: {scenario.title}'))
            else:
                self.stdout.write(self.style.WARNING(f'Scenario already exists: {scenario.title}'))

            # Create questions for each role
            for question_data in scenario_data['questions']:
                question, created = ClimateQuestion.objects.get_or_create(
                    scenario=scenario,
                    role=question_data['role'],
                    defaults={
                        'question_text': question_data['question_text']
                    }
                )
                
                if created:
                    self.stdout.write(f'  Created question for {question_data["role"]}')

                # Create options for each question
                for option_letter, option_text, consequence in question_data['options']:
                    option, created = ClimateOption.objects.get_or_create(
                        question=question,
                        option_letter=option_letter,
                        defaults={
                            'option_text': option_text,
                            'immediate_consequence': consequence,
                            'outcome_logic': self.get_outcome_logic(scenario_data['round_number'], question_data['role'], option_letter)
                        }
                    )
                    
                    if created:
                        self.stdout.write(f'    Created option {option_letter.upper()}: {option_text[:50]}...')

        self.stdout.write(self.style.SUCCESS('Climate game scenarios populated successfully!'))
        self.stdout.write(self.style.SUCCESS(f'Total scenarios: {ClimateScenario.objects.count()}'))
        self.stdout.write(self.style.SUCCESS(f'Total questions: {ClimateQuestion.objects.count()}'))
        self.stdout.write(self.style.SUCCESS(f'Total options: {ClimateOption.objects.count()}'))

    def get_outcome_logic(self, round_number, role, option_letter):
        """
        Define outcome logic for each option based on round, role, and choice
        Returns dict with meter impact values (-20 to +20)
        """
        # Base outcome logic - this is a simplified version
        # In a full implementation, this would be more sophisticated
        
        outcome_templates = {
            # Round 1: Delhi Air Pollution
            1: {
                'government': {
                    'a': {'climate_resilience': 15, 'gdp': -10, 'public_morale': -5, 'environmental_health': 20},
                    'b': {'climate_resilience': 5, 'gdp': -3, 'public_morale': -8, 'environmental_health': 8},
                    'c': {'climate_resilience': -5, 'gdp': 2, 'public_morale': -12, 'environmental_health': -2},
                    'd': {'climate_resilience': 3, 'gdp': 8, 'public_morale': -10, 'environmental_health': -5}
                },
                'business': {
                    'a': {'climate_resilience': 10, 'gdp': -15, 'public_morale': 8, 'environmental_health': 12},
                    'b': {'climate_resilience': -8, 'gdp': 12, 'public_morale': -15, 'environmental_health': -10},
                    'c': {'climate_resilience': 2, 'gdp': 5, 'public_morale': -5, 'environmental_health': 3},
                    'd': {'climate_resilience': -3, 'gdp': 8, 'public_morale': -10, 'environmental_health': -8}
                },
                'farmer': {
                    'a': {'climate_resilience': 12, 'gdp': -5, 'public_morale': 10, 'environmental_health': 15},
                    'b': {'climate_resilience': -15, 'gdp': 8, 'public_morale': -12, 'environmental_health': -20},
                    'c': {'climate_resilience': 0, 'gdp': -8, 'public_morale': -5, 'environmental_health': 0},
                    'd': {'climate_resilience': 5, 'gdp': -3, 'public_morale': 3, 'environmental_health': 8}
                },
                'urban_citizen': {
                    'a': {'climate_resilience': 8, 'gdp': 0, 'public_morale': 12, 'environmental_health': 5},
                    'b': {'climate_resilience': 2, 'gdp': 5, 'public_morale': -8, 'environmental_health': 3},
                    'c': {'climate_resilience': 10, 'gdp': -5, 'public_morale': 8, 'environmental_health': 12},
                    'd': {'climate_resilience': -5, 'gdp': 0, 'public_morale': -15, 'environmental_health': -3}
                },
                'ngo_worker': {
                    'a': {'climate_resilience': 5, 'gdp': -2, 'public_morale': 8, 'environmental_health': 10},
                    'b': {'climate_resilience': 8, 'gdp': 3, 'public_morale': 5, 'environmental_health': 12},
                    'c': {'climate_resilience': 3, 'gdp': 8, 'public_morale': -3, 'environmental_health': 5},
                    'd': {'climate_resilience': 12, 'gdp': -5, 'public_morale': 15, 'environmental_health': 8}
                }
            },
            # Similar patterns for other rounds - abbreviated for brevity
            2: {  # Mumbai Floods
                'government': {
                    'a': {'climate_resilience': 12, 'gdp': -8, 'public_morale': 10, 'environmental_health': 8},
                    'b': {'climate_resilience': -5, 'gdp': 15, 'public_morale': -15, 'environmental_health': -3},
                    'c': {'climate_resilience': -8, 'gdp': -5, 'public_morale': -12, 'environmental_health': -5},
                    'd': {'climate_resilience': 8, 'gdp': -3, 'public_morale': 12, 'environmental_health': 15}
                }
                # ... (other roles would have similar structure)
            }
            # ... (rounds 3, 4, 5 would follow similar patterns)
        }
        
        # Return outcome for specific round/role/option, or default values
        try:
            return outcome_templates.get(round_number, {}).get(role, {}).get(option_letter, {
                'climate_resilience': 0, 'gdp': 0, 'public_morale': 0, 'environmental_health': 0
            })
        except:
            return {'climate_resilience': 0, 'gdp': 0, 'public_morale': 0, 'environmental_health': 0}