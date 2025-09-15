from django.core.management.base import BaseCommand
from cyber_city.models import SecurityChallenge, CyberBadge


class Command(BaseCommand):
    help = 'Load cybersecurity challenges and badges for Cyber City Protection Squad'

    def handle(self, *args, **options):
        self.stdout.write('Loading Cyber City Protection Squad challenges...')
        
        # Clear existing challenges
        SecurityChallenge.objects.all().delete()
        CyberBadge.objects.all().delete()
        
        # Create security challenges
        challenges = [
            {
                'challenge_number': 1,
                'title': 'Password Fortress: The First Line',
                'question_text': 'A student wants to create a secure password for their school email account. Which password provides the BEST security?',
                'option_a': 'password123',
                'option_b': 'MyDog2024!',
                'option_c': 'Tr@il$Bl@ze2024!Secur3',
                'correct_answer': 'C',
                'explanation': 'Strong passwords should be long (12+ characters), contain a mix of uppercase, lowercase, numbers, and special characters, and avoid common words. Option C meets all these criteria with 19 characters and complex patterns.',
                'tessa_tip': 'Remember the golden rule: Length + Complexity = Security! Think of a passphrase with numbers and symbols mixed in. A strong password is your first shield against cyber attackers!'
            },
            {
                'challenge_number': 2,
                'title': 'Two-Factor Fortress: Double Protection',
                'question_text': 'Emma receives a text message with a 6-digit code after entering her password. What security feature is she using, and why is it important?',
                'option_a': 'Password recovery - it helps her remember her password',
                'option_b': 'Two-Factor Authentication (2FA) - it adds an extra layer of security',
                'option_c': 'Account verification - it confirms her email address',
                'correct_answer': 'B',
                'explanation': 'Two-Factor Authentication (2FA) requires something you know (password) AND something you have (phone/device). Even if hackers steal your password, they cannot access your account without the second factor.',
                'tessa_tip': 'Think of 2FA like a bank vault - you need both the key AND the combination! Always enable 2FA on important accounts like email, social media, and banking. It is 99.9% effective against automated attacks!'
            },
            {
                'challenge_number': 3,
                'title': 'Phishing Trap: Spot the Fake',
                'question_text': 'Alex receives an email claiming to be from his bank, asking him to click a link and update his password immediately due to "suspicious activity." What should Alex do?',
                'option_a': 'Click the link immediately to secure his account',
                'option_b': 'Call his bank directly using the number on his bank card to verify',
                'option_c': 'Forward the email to friends to warn them',
                'correct_answer': 'B',
                'explanation': 'This is a classic phishing attempt. Legitimate banks never ask for sensitive information via email or require immediate action through email links. Always verify by contacting the organization directly through official channels.',
                'tessa_tip': 'When in doubt, verify the route! Phishing emails create urgency to make you act without thinking. Real banks will never pressure you through email. Trust your instincts - if it feels suspicious, it probably is!'
            },
            {
                'challenge_number': 4,
                'title': 'Public WiFi: Hidden Dangers',
                'question_text': 'Sarah is at a coffee shop and needs to check her online banking. She sees two WiFi networks: "CoffeeShop_Guest" (password protected) and "Free_WiFi_Here" (open network). What is the SAFEST approach?',
                'option_a': 'Use "Free_WiFi_Here" since it connects faster',
                'option_b': 'Use "CoffeeShop_Guest" and access banking through the mobile app',
                'option_c': 'Wait and use her mobile data or home WiFi for banking',
                'correct_answer': 'C',
                'explanation': 'Public WiFi networks, even password-protected ones, can be intercepted by hackers. Banking and other sensitive activities should only be done on trusted, private networks or secure mobile data connections.',
                'tessa_tip': 'Remember: Public WiFi = Public Risk! Hackers can intercept data on public networks easily. For sensitive activities like banking, shopping, or accessing personal accounts, always use your mobile data or wait for a secure, private connection!'
            },
            {
                'challenge_number': 5,
                'title': 'Social Engineering: The Human Hack',
                'question_text': 'Tom receives a phone call from someone claiming to be from IT support, saying there is a security issue with his school account. The caller asks for his username and password to "fix the problem immediately." How should Tom respond?',
                'option_a': 'Provide the information since IT needs to fix the security issue',
                'option_b': 'Hang up and contact the school IT department directly to verify',
                'option_c': 'Ask the caller to email him the request instead',
                'correct_answer': 'B',
                'explanation': 'This is social engineering - manipulating people to reveal confidential information. Legitimate IT departments never ask for passwords over the phone. Always verify by contacting the organization through official channels.',
                'tessa_tip': 'Social engineers exploit trust and urgency! Remember: No legitimate organization will ever ask for your password over the phone or email. When someone calls claiming to need your credentials, it is always a red flag. Verify independently!'
            }
        ]
        
        for challenge_data in challenges:
            SecurityChallenge.objects.create(**challenge_data)
            self.stdout.write(f'Created challenge {challenge_data["challenge_number"]}: {challenge_data["title"]}')
        
        # Create cyber badges
        badges = [
            {
                'badge_id': 'perfect_defender',
                'name': 'Perfect Defender',
                'description': 'Completed all challenges without any wrong answers',
                'icon': '🛡️',
                'unlock_condition': 'Answer all 5 challenges correctly on first try'
            },
            {
                'badge_id': 'cyber_speedster',
                'name': 'Cyber Speedster',
                'description': 'Completed 3 or more challenges quickly',
                'icon': '⚡',
                'unlock_condition': 'Complete 3+ challenges'
            },
            {
                'badge_id': 'password_master',
                'name': 'Password Master',
                'description': 'Successfully completed the Password Fortress mission',
                'icon': '🔐',
                'unlock_condition': 'Complete all 5 cybersecurity challenges'
            },
            {
                'badge_id': 'security_expert',
                'name': 'Security Expert',
                'description': 'Achieved perfect score in cybersecurity knowledge',
                'icon': '🎯',
                'unlock_condition': 'Score 500 points (perfect score)'
            },
            {
                'badge_id': 'city_protector',
                'name': 'City Protector',
                'description': 'Restored Cyber City security level to 100%',
                'icon': '🏙️',
                'unlock_condition': 'Complete mission and reach 100% city security'
            }
        ]
        
        for badge_data in badges:
            CyberBadge.objects.create(**badge_data)
            self.stdout.write(f'Created badge: {badge_data["name"]} {badge_data["icon"]}')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully loaded {len(challenges)} challenges and {len(badges)} badges for Cyber City Protection Squad!'
            )
        )