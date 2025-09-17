from django.core.management.base import BaseCommand
from cyber_city.models import CyberbullyChallenge

class Command(BaseCommand):
    help = 'Populate Cyberbully Crisis challenges for Mission 2'

    def handle(self, *args, **options):
        # Check if challenges already exist
        if CyberbullyChallenge.objects.exists():
            self.stdout.write(
                self.style.WARNING('Cyberbully challenges already exist. Skipping.')
            )
            return

        challenges = [
            {
                'challenge_number': 1,
                'title': 'Welcome to Cyber Street!',
                'background_story': 'Bully Bots stomp in, posting graffiti above happy citizens.',
                'option_a': 'You\'re awesome at this game!',
                'option_a_type': 'friendly',
                'option_b': 'Nobody likes you, just quit already.',
                'option_b_type': 'bully',
                'option_c': 'Good luck on your project!',
                'option_c_type': 'friendly',
                'correct_answer': 'B',
                'explanation': 'The message "Nobody likes you, just quit already" is mean and hurtful. It\'s designed to make someone feel bad about themselves, which is bullying behavior.',
                'mentor_tip': 'Great job! You protected Cyber City from meanness. Reporting helps stop bullies in their tracks.',
                'mentor_voice_text': 'Excellent work! You spotted the bully message and helped keep our community safe. Remember, reporting bullying helps protect everyone!'
            },
            {
                'challenge_number': 2,
                'title': 'Group Chat Challenge',
                'background_story': 'Projected group chat doors, avatars gathered in a virtual plaza.',
                'option_a': 'You seriously think anyone cares about your art? LOL.',
                'option_a_type': 'bully',
                'option_b': 'Wow, that game was tough. Good job, everyone!',
                'option_b_type': 'friendly',
                'option_c': 'Check out this cat meme, it\'s hilarious!',
                'option_c_type': 'friendly',
                'correct_answer': 'A',
                'explanation': 'Making fun of someone\'s creative work and saying "nobody cares" is hurtful and dismissive. This kind of comment can really hurt someone\'s feelings and discourage them from sharing their talents.',
                'mentor_tip': 'Right choice! Hurtful comments about someone\'s interests aren\'t jokes—they\'re bullying.',
                'mentor_voice_text': 'Perfect! You recognized that making fun of someone\'s art is mean and hurtful. Art is for everyone, and we should encourage creativity!'
            },
            {
                'challenge_number': 3,
                'title': 'The Sneaky Excluder',
                'background_story': 'Avatar group selfie projected above a party scene.',
                'option_a': 'Let\'s invite everyone except Jamie—they\'re too weird.',
                'option_a_type': 'bully',
                'option_b': 'Here\'s the invite list!',
                'option_b_type': 'friendly',
                'option_c': 'Can\'t wait for the party!',
                'option_c_type': 'friendly',
                'correct_answer': 'A',
                'explanation': 'Deliberately excluding someone and calling them "weird" is a form of social bullying. Even if it seems subtle, leaving people out on purpose because you think they\'re different is mean and hurtful.',
                'mentor_tip': 'Perfect! Leaving people out on purpose is cruel—even if it seems subtle.',
                'mentor_voice_text': 'Excellent spotting! Excluding someone just because they\'re different is a sneaky form of bullying. Everyone deserves to be included!'
            },
            {
                'challenge_number': 4,
                'title': 'Creative Work Teasing',
                'background_story': 'Poetry contest—holograms of creative entries float above a stage.',
                'option_a': 'Your poem made me laugh... in a good way! Loved it.',
                'option_a_type': 'friendly',
                'option_b': 'Everyone saw your poem, it was the worst I\'ve read!',
                'option_b_type': 'bully',
                'option_c': 'Thanks for sharing your poem.',
                'option_c_type': 'friendly',
                'correct_answer': 'B',
                'explanation': 'Publicly saying someone\'s creative work is "the worst" is mean and designed to embarrass them. This kind of harsh criticism can really hurt someone\'s confidence and make them afraid to share their creativity.',
                'mentor_tip': 'Bullies sometimes attack creative work—good for you, calling it out!',
                'mentor_voice_text': 'Great job! You protected someone\'s creativity from a mean comment. Creative expression should be encouraged, not torn down!'
            },
            {
                'challenge_number': 5,
                'title': 'Joke or Bullying?',
                'background_story': 'Gaming arcade scene, leaderboard up in lights.',
                'option_a': 'Guess who tripped again today?',
                'option_a_type': 'bully',
                'option_b': 'Let\'s play at 6pm as usual!',
                'option_b_type': 'friendly',
                'option_c': 'Congrats on your new high score, Sam!',
                'option_c_type': 'friendly',
                'correct_answer': 'A',
                'explanation': 'Making fun of someone for tripping and drawing attention to their embarrassing moment is teasing that hurts. Even if someone calls it a "joke," if it makes the person feel bad or embarrassed, it\'s actually bullying.',
                'mentor_tip': 'Teasing that embarrasses can feel like bullying—thank you for helping friends feel safe.',
                'mentor_voice_text': 'Perfect! You understood that teasing someone about embarrassing moments isn\'t funny - it\'s hurtful. You\'re a true protector of kindness!'
            }
        ]

        for challenge_data in challenges:
            challenge, created = CyberbullyChallenge.objects.get_or_create(
                challenge_number=challenge_data['challenge_number'],
                defaults=challenge_data
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Created challenge {challenge.challenge_number}: {challenge.title}')
                )

        self.stdout.write(
            self.style.SUCCESS(f'Successfully populated {len(challenges)} cyberbully challenges!')
        )