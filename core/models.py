from django.db import models


class Course(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class DemoRequest(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    school = models.CharField(max_length=200)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.school}"


class SchoolDemoRequest(models.Model):
    PRODUCT_CHOICES = [
        ('entrepreneurship', 'Entrepreneurship Course'),
        ('ai_course', 'AI Course for Students'),
        ('financial_literacy', 'Financial Literacy Course'),
        ('climate_change', 'Climate Change Course'),
        ('teacher_training', 'AI Training for Teachers'),
    ]
    
    school_name = models.CharField(max_length=200, verbose_name="School Name")
    contact_person = models.CharField(max_length=100, verbose_name="Contact Person Name")
    email = models.EmailField(verbose_name="Email Address")
    phone = models.CharField(max_length=20, blank=True, verbose_name="Phone Number")
    city = models.CharField(max_length=100, verbose_name="City")
    student_count = models.PositiveIntegerField(verbose_name="Number of Students")
    
    # Product selections (multiple choice)
    interested_products = models.JSONField(
        default=list, 
        verbose_name="Products of Interest",
        help_text="Selected products the school is interested in"
    )
    
    additional_requirements = models.TextField(
        blank=True, 
        verbose_name="Additional Requirements",
        help_text="Any specific requirements or questions"
    )
    
    preferred_demo_time = models.CharField(
        max_length=100, 
        blank=True,
        verbose_name="Preferred Demo Time"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    is_contacted = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = "School Demo Request"
        verbose_name_plural = "School Demo Requests"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.school_name} - {self.contact_person}"
    
    def get_products_display(self):
        """Return formatted list of interested products"""
        product_dict = dict(self.PRODUCT_CHOICES)
        return [product_dict.get(product, product) for product in self.interested_products]


class GameReview(models.Model):
    """Unified review model for all games across the platform"""
    
    GAME_CHOICES = [
        ('password_fortress', 'Password Fortress'),
        ('cyberbully_crisis', 'Cyberbully Crisis'),
        ('robotic_buddy', 'Robotic Buddy'),
        ('animal_classification', 'Animal Classification'),
        ('emotion_recognition', 'Emotion Recognition'),
        ('group_learning', 'Group Learning'),
        ('constitution_basic', 'Constitution Basic'),
        ('constitution_advanced', 'Constitution Advanced'),
        ('financial_literacy', 'Financial Literacy'),
        ('entrepreneurship', 'Entrepreneurship'),
    ]
    
    RATING_CHOICES = [
        (1, '1 Star - Not Good'),
        (2, '2 Stars - Okay'),
        (3, '3 Stars - Good'),
        (4, '4 Stars - Great'),
        (5, '5 Stars - Amazing'),
    ]
    
    # Game identification
    game_type = models.CharField(max_length=50, choices=GAME_CHOICES)
    session_id = models.CharField(max_length=100, blank=True, null=True, help_text="Game session identifier")
    
    # User info (optional for privacy)
    player_name = models.CharField(max_length=100, blank=True, null=True)
    player_age = models.PositiveIntegerField(blank=True, null=True)
    
    # Review data
    rating = models.PositiveIntegerField(choices=RATING_CHOICES, help_text="Rating is mandatory")
    review_text = models.TextField(blank=True, null=True, help_text="Review text is optional")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    
    class Meta:
        verbose_name = "Game Review"
        verbose_name_plural = "Game Reviews"
        ordering = ['-created_at']
        # Prevent duplicate reviews for same session
        unique_together = ['game_type', 'session_id']
    
    def __str__(self):
        game_name = dict(self.GAME_CHOICES).get(self.game_type, self.game_type)
        return f"{game_name} - {self.rating} stars"
    
    def get_rating_display_emoji(self):
        """Return emoji representation of rating"""
        emoji_map = {1: '⭐', 2: '⭐⭐', 3: '⭐⭐⭐', 4: '⭐⭐⭐⭐', 5: '⭐⭐⭐⭐⭐'}
        return emoji_map.get(self.rating, '⭐')
    
    def get_game_display(self):
        """Return human-readable game name"""
        return dict(self.GAME_CHOICES).get(self.game_type, self.game_type)