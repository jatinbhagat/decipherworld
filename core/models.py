from django.db import models
from django.utils.html import mark_safe
from PIL import Image
import os


# Country codes for mobile number field
COUNTRY_CODES = [
    ('+1', '🇺🇸 United States (+1)'),
    ('+1', '🇨🇦 Canada (+1)'),
    ('+7', '🇷🇺 Russia (+7)'),
    ('+20', '🇪🇬 Egypt (+20)'),
    ('+27', '🇿🇦 South Africa (+27)'),
    ('+30', '🇬🇷 Greece (+30)'),
    ('+31', '🇳🇱 Netherlands (+31)'),
    ('+32', '🇧🇪 Belgium (+32)'),
    ('+33', '🇫🇷 France (+33)'),
    ('+34', '🇪🇸 Spain (+34)'),
    ('+36', '🇭🇺 Hungary (+36)'),
    ('+39', '🇮🇹 Italy (+39)'),
    ('+40', '🇷🇴 Romania (+40)'),
    ('+41', '🇨🇭 Switzerland (+41)'),
    ('+43', '🇦🇹 Austria (+43)'),
    ('+44', '🇬🇧 United Kingdom (+44)'),
    ('+45', '🇩🇰 Denmark (+45)'),
    ('+46', '🇸🇪 Sweden (+46)'),
    ('+47', '🇳🇴 Norway (+47)'),
    ('+48', '🇵🇱 Poland (+48)'),
    ('+49', '🇩🇪 Germany (+49)'),
    ('+51', '🇵🇪 Peru (+51)'),
    ('+52', '🇲🇽 Mexico (+52)'),
    ('+53', '🇨🇺 Cuba (+53)'),
    ('+54', '🇦🇷 Argentina (+54)'),
    ('+55', '🇧🇷 Brazil (+55)'),
    ('+56', '🇨🇱 Chile (+56)'),
    ('+57', '🇨🇴 Colombia (+57)'),
    ('+58', '🇻🇪 Venezuela (+58)'),
    ('+60', '🇲🇾 Malaysia (+60)'),
    ('+61', '🇦🇺 Australia (+61)'),
    ('+62', '🇮🇩 Indonesia (+62)'),
    ('+63', '🇵🇭 Philippines (+63)'),
    ('+64', '🇳🇿 New Zealand (+64)'),
    ('+65', '🇸🇬 Singapore (+65)'),
    ('+66', '🇹🇭 Thailand (+66)'),
    ('+81', '🇯🇵 Japan (+81)'),
    ('+82', '🇰🇷 South Korea (+82)'),
    ('+84', '🇻🇳 Vietnam (+84)'),
    ('+86', '🇨🇳 China (+86)'),
    ('+90', '🇹🇷 Turkey (+90)'),
    ('+91', '🇮🇳 India (+91)'),
    ('+92', '🇵🇰 Pakistan (+92)'),
    ('+93', '🇦🇫 Afghanistan (+93)'),
    ('+94', '🇱🇰 Sri Lanka (+94)'),
    ('+95', '🇲🇲 Myanmar (+95)'),
    ('+98', '🇮🇷 Iran (+98)'),
    ('+212', '🇲🇦 Morocco (+212)'),
    ('+213', '🇩🇿 Algeria (+213)'),
    ('+216', '🇹🇳 Tunisia (+216)'),
    ('+218', '🇱🇾 Libya (+218)'),
    ('+220', '🇬🇲 Gambia (+220)'),
    ('+221', '🇸🇳 Senegal (+221)'),
    ('+222', '🇲🇷 Mauritania (+222)'),
    ('+223', '🇲🇱 Mali (+223)'),
    ('+224', '🇬🇳 Guinea (+224)'),
    ('+225', '🇨🇮 Côte d\'Ivoire (+225)'),
    ('+226', '🇧🇫 Burkina Faso (+226)'),
    ('+227', '🇳🇪 Niger (+227)'),
    ('+228', '🇹🇬 Togo (+228)'),
    ('+229', '🇧🇯 Benin (+229)'),
    ('+230', '🇲🇺 Mauritius (+230)'),
    ('+231', '🇱🇷 Liberia (+231)'),
    ('+232', '🇸🇱 Sierra Leone (+232)'),
    ('+233', '🇬🇭 Ghana (+233)'),
    ('+234', '🇳🇬 Nigeria (+234)'),
    ('+235', '🇹🇩 Chad (+235)'),
    ('+236', '🇨🇫 Central African Republic (+236)'),
    ('+237', '🇨🇲 Cameroon (+237)'),
    ('+238', '🇨🇻 Cape Verde (+238)'),
    ('+239', '🇸🇹 São Tomé and Príncipe (+239)'),
    ('+240', '🇬🇶 Equatorial Guinea (+240)'),
    ('+241', '🇬🇦 Gabon (+241)'),
    ('+242', '🇨🇬 Republic of the Congo (+242)'),
    ('+243', '🇨🇩 Democratic Republic of the Congo (+243)'),
    ('+244', '🇦🇴 Angola (+244)'),
    ('+245', '🇬🇼 Guinea-Bissau (+245)'),
    ('+246', '🇮🇴 British Indian Ocean Territory (+246)'),
    ('+248', '🇸🇨 Seychelles (+248)'),
    ('+249', '🇸🇩 Sudan (+249)'),
    ('+250', '🇷🇼 Rwanda (+250)'),
    ('+251', '🇪🇹 Ethiopia (+251)'),
    ('+252', '🇸🇴 Somalia (+252)'),
    ('+253', '🇩🇯 Djibouti (+253)'),
    ('+254', '🇰🇪 Kenya (+254)'),
    ('+255', '🇹🇿 Tanzania (+255)'),
    ('+256', '🇺🇬 Uganda (+256)'),
    ('+257', '🇧🇮 Burundi (+257)'),
    ('+258', '🇲🇿 Mozambique (+258)'),
    ('+260', '🇿🇲 Zambia (+260)'),
    ('+261', '🇲🇬 Madagascar (+261)'),
    ('+262', '🇷🇪 Réunion (+262)'),
    ('+263', '🇿🇼 Zimbabwe (+263)'),
    ('+264', '🇳🇦 Namibia (+264)'),
    ('+265', '🇲🇼 Malawi (+265)'),
    ('+266', '🇱🇸 Lesotho (+266)'),
    ('+267', '🇧🇼 Botswana (+267)'),
    ('+268', '🇸🇿 Eswatini (+268)'),
    ('+269', '🇰🇲 Comoros (+269)'),
    ('+290', '🇸🇭 Saint Helena (+290)'),
    ('+291', '🇪🇷 Eritrea (+291)'),
    ('+297', '🇦🇼 Aruba (+297)'),
    ('+298', '🇫🇴 Faroe Islands (+298)'),
    ('+299', '🇬🇱 Greenland (+299)'),
    ('+350', '🇬🇮 Gibraltar (+350)'),
    ('+351', '🇵🇹 Portugal (+351)'),
    ('+352', '🇱🇺 Luxembourg (+352)'),
    ('+353', '🇮🇪 Ireland (+353)'),
    ('+354', '🇮🇸 Iceland (+354)'),
    ('+355', '🇦🇱 Albania (+355)'),
    ('+356', '🇲🇹 Malta (+356)'),
    ('+357', '🇨🇾 Cyprus (+357)'),
    ('+358', '🇫🇮 Finland (+358)'),
    ('+359', '🇧🇬 Bulgaria (+359)'),
    ('+370', '🇱🇹 Lithuania (+370)'),
    ('+371', '🇱🇻 Latvia (+371)'),
    ('+372', '🇪🇪 Estonia (+372)'),
    ('+373', '🇲🇩 Moldova (+373)'),
    ('+374', '🇦🇲 Armenia (+374)'),
    ('+375', '🇧🇾 Belarus (+375)'),
    ('+376', '🇦🇩 Andorra (+376)'),
    ('+377', '🇲🇨 Monaco (+377)'),
    ('+378', '🇸🇲 San Marino (+378)'),
    ('+380', '🇺🇦 Ukraine (+380)'),
    ('+381', '🇷🇸 Serbia (+381)'),
    ('+382', '🇲🇪 Montenegro (+382)'),
    ('+383', '🇽🇰 Kosovo (+383)'),
    ('+385', '🇭🇷 Croatia (+385)'),
    ('+386', '🇸🇮 Slovenia (+386)'),
    ('+387', '🇧🇦 Bosnia and Herzegovina (+387)'),
    ('+389', '🇲🇰 North Macedonia (+389)'),
    ('+420', '🇨🇿 Czech Republic (+420)'),
    ('+421', '🇸🇰 Slovakia (+421)'),
    ('+423', '🇱🇮 Liechtenstein (+423)'),
    ('+500', '🇫🇰 Falkland Islands (+500)'),
    ('+501', '🇧🇿 Belize (+501)'),
    ('+502', '🇬🇹 Guatemala (+502)'),
    ('+503', '🇸🇻 El Salvador (+503)'),
    ('+504', '🇭🇳 Honduras (+504)'),
    ('+505', '🇳🇮 Nicaragua (+505)'),
    ('+506', '🇨🇷 Costa Rica (+506)'),
    ('+507', '🇵🇦 Panama (+507)'),
    ('+508', '🇵🇲 Saint Pierre and Miquelon (+508)'),
    ('+509', '🇭🇹 Haiti (+509)'),
    ('+590', '🇬🇵 Guadeloupe (+590)'),
    ('+591', '🇧🇴 Bolivia (+591)'),
    ('+592', '🇬🇾 Guyana (+592)'),
    ('+593', '🇪🇨 Ecuador (+593)'),
    ('+594', '🇬🇫 French Guiana (+594)'),
    ('+595', '🇵🇾 Paraguay (+595)'),
    ('+596', '🇲🇶 Martinique (+596)'),
    ('+597', '🇸🇷 Suriname (+597)'),
    ('+598', '🇺🇾 Uruguay (+598)'),
    ('+599', '🇨🇼 Curaçao (+599)'),
    ('+670', '🇹🇱 East Timor (+670)'),
    ('+672', '🇦🇶 Antarctica (+672)'),
    ('+673', '🇧🇳 Brunei (+673)'),
    ('+674', '🇳🇷 Nauru (+674)'),
    ('+675', '🇵🇬 Papua New Guinea (+675)'),
    ('+676', '🇹🇴 Tonga (+676)'),
    ('+677', '🇸🇧 Solomon Islands (+677)'),
    ('+678', '🇻🇺 Vanuatu (+678)'),
    ('+679', '🇫🇯 Fiji (+679)'),
    ('+680', '🇵🇼 Palau (+680)'),
    ('+681', '🇼🇫 Wallis and Futuna (+681)'),
    ('+682', '🇨🇰 Cook Islands (+682)'),
    ('+683', '🇳🇺 Niue (+683)'),
    ('+684', '🇦🇸 American Samoa (+684)'),
    ('+685', '🇼🇸 Samoa (+685)'),
    ('+686', '🇰🇮 Kiribati (+686)'),
    ('+687', '🇳🇨 New Caledonia (+687)'),
    ('+688', '🇹🇻 Tuvalu (+688)'),
    ('+689', '🇵🇫 French Polynesia (+689)'),
    ('+690', '🇹🇰 Tokelau (+690)'),
    ('+691', '🇫🇲 Federated States of Micronesia (+691)'),
    ('+692', '🇲🇭 Marshall Islands (+692)'),
    ('+850', '🇰🇵 North Korea (+850)'),
    ('+852', '🇭🇰 Hong Kong (+852)'),
    ('+853', '🇲🇴 Macau (+853)'),
    ('+855', '🇰🇭 Cambodia (+855)'),
    ('+856', '🇱🇦 Laos (+856)'),
    ('+880', '🇧🇩 Bangladesh (+880)'),
    ('+886', '🇹🇼 Taiwan (+886)'),
    ('+960', '🇲🇻 Maldives (+960)'),
    ('+961', '🇱🇧 Lebanon (+961)'),
    ('+962', '🇯🇴 Jordan (+962)'),
    ('+963', '🇸🇾 Syria (+963)'),
    ('+964', '🇮🇶 Iraq (+964)'),
    ('+965', '🇰🇼 Kuwait (+965)'),
    ('+966', '🇸🇦 Saudi Arabia (+966)'),
    ('+967', '🇾🇪 Yemen (+967)'),
    ('+968', '🇴🇲 Oman (+968)'),
    ('+970', '🇵🇸 Palestine (+970)'),
    ('+971', '🇦🇪 United Arab Emirates (+971)'),
    ('+972', '🇮🇱 Israel (+972)'),
    ('+973', '🇧🇭 Bahrain (+973)'),
    ('+974', '🇶🇦 Qatar (+974)'),
    ('+975', '🇧🇹 Bhutan (+975)'),
    ('+976', '🇲🇳 Mongolia (+976)'),
    ('+977', '🇳🇵 Nepal (+977)'),
    ('+992', '🇹🇯 Tajikistan (+992)'),
    ('+993', '🇹🇲 Turkmenistan (+993)'),
    ('+994', '🇦🇿 Azerbaijan (+994)'),
    ('+995', '🇬🇪 Georgia (+995)'),
    ('+996', '🇰🇬 Kyrgyzstan (+996)'),
    ('+998', '🇺🇿 Uzbekistan (+998)'),
]


class Course(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    is_active = models.BooleanField(default=True, help_text="Whether this course is actively offered")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class DemoRequest(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    school = models.CharField(max_length=200)
    country_code = models.CharField(
        max_length=10, 
        choices=COUNTRY_CODES, 
        default='+91',
        verbose_name="Country Code",
        help_text="Select your country code"
    )
    mobile_number = models.CharField(
        max_length=15, 
        default="0000000000",
        verbose_name="Mobile Number",
        help_text="Enter mobile number without country code"
    )
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.school}"
    
    def get_full_mobile_number(self):
        """Return formatted mobile number with country code"""
        return f"{self.country_code} {self.mobile_number}"
    
    class Meta:
        verbose_name = "Demo Request"
        verbose_name_plural = "Demo Requests"


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
    country_code = models.CharField(
        max_length=10, 
        choices=COUNTRY_CODES, 
        default='+91',
        verbose_name="Country Code",
        help_text="Select your country code"
    )
    mobile_number = models.CharField(
        max_length=15, 
        default="0000000000",
        verbose_name="Mobile Number",
        help_text="Enter mobile number without country code"
    )
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
    
    def get_full_mobile_number(self):
        """Return formatted mobile number with country code"""
        return f"{self.country_code} {self.mobile_number}"
    
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


# Gallery Models
class PhotoCategory(models.Model):
    """Categories for organizing photos in the gallery"""
    name = models.CharField(max_length=100, help_text="Category name (e.g., School Events, Workshops)")
    description = models.TextField(blank=True, help_text="Optional description of this category")
    order = models.PositiveIntegerField(default=0, help_text="Order for display (lower numbers first)")
    is_active = models.BooleanField(default=True, help_text="Whether this category is visible")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Photo Category"
        verbose_name_plural = "Photo Categories"
        ordering = ['order', 'name']
    
    def __str__(self):
        return self.name


class PhotoGallery(models.Model):
    """Photo gallery items showcasing school success stories"""
    title = models.CharField(max_length=200, help_text="Photo title or caption")
    image = models.ImageField(
        upload_to='gallery/photos/', 
        help_text="Upload high-quality image (recommended: 1200x800px or larger)"
    )
    thumbnail = models.ImageField(
        upload_to='gallery/thumbnails/', 
        blank=True, 
        help_text="Auto-generated thumbnail (leave blank)"
    )
    category = models.ForeignKey(
        PhotoCategory, 
        on_delete=models.CASCADE,
        help_text="Select the appropriate category"
    )
    caption = models.TextField(
        blank=True, 
        help_text="Detailed description or story behind the photo"
    )
    school_name = models.CharField(
        max_length=200, 
        blank=True,
        help_text="Name of the school featured in this photo"
    )
    date_taken = models.DateField(
        blank=True, 
        null=True,
        help_text="When was this photo taken?"
    )
    order = models.PositiveIntegerField(
        default=0, 
        help_text="Order for display within category (lower numbers first)"
    )
    is_featured = models.BooleanField(
        default=False,
        help_text="Show in featured photos section"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this photo is visible on the website"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Photo Gallery Item"
        verbose_name_plural = "Photo Gallery Items"
        ordering = ['order', '-created_at']
    
    def __str__(self):
        return self.title
    
    def image_preview(self):
        """Return HTML for admin image preview"""
        if self.image:
            return mark_safe(f'<img src="{self.image.url}" style="max-width: 150px; max-height: 100px; object-fit: cover; border-radius: 8px;" />')
        return "No image"
    image_preview.short_description = "Preview"
    
    def save(self, *args, **kwargs):
        """Auto-generate thumbnail when saving"""
        super().save(*args, **kwargs)
        
        if self.image and not self.thumbnail:
            # Create thumbnail
            img = Image.open(self.image.path)
            img.thumbnail((400, 300), Image.Resampling.LANCZOS)
            
            # Save thumbnail
            thumb_name = f"thumb_{os.path.basename(self.image.name)}"
            thumb_path = os.path.join('gallery/thumbnails/', thumb_name)
            full_thumb_path = os.path.join('media', thumb_path)
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(full_thumb_path), exist_ok=True)
            
            img.save(full_thumb_path, optimize=True, quality=85)
            self.thumbnail = thumb_path
            super().save(update_fields=['thumbnail'])


class VideoTestimonial(models.Model):
    """Video testimonials from students and schools"""
    title = models.CharField(
        max_length=200, 
        help_text="Testimonial title (e.g., 'Amazing AI Learning Experience')"
    )
    student_name = models.CharField(
        max_length=100,
        help_text="Name of the student giving testimonial"
    )
    student_grade = models.CharField(
        max_length=50, 
        blank=True,
        help_text="Student's grade/class (e.g., 'Grade 5', 'Class 10')"
    )
    school_name = models.CharField(
        max_length=200,
        help_text="Name of the school"
    )
    video_file = models.FileField(
        upload_to='gallery/videos/', 
        blank=True,
        help_text="Upload MP4 video file (recommended: under 50MB)"
    )
    video_url = models.URLField(
        blank=True,
        help_text="Or paste YouTube/Vimeo URL instead of uploading file"
    )
    thumbnail = models.ImageField(
        upload_to='gallery/video_thumbnails/', 
        blank=True,
        help_text="Custom thumbnail image (auto-generated if left blank)"
    )
    transcript = models.TextField(
        blank=True,
        help_text="Full transcript of the video (for accessibility)"
    )
    summary = models.TextField(
        blank=True,
        help_text="Brief summary of what the student says"
    )
    duration = models.DurationField(
        blank=True, 
        null=True,
        help_text="Video duration (auto-detected when possible)"
    )
    order = models.PositiveIntegerField(
        default=0,
        help_text="Order for display (lower numbers first)"
    )
    is_featured = models.BooleanField(
        default=False,
        help_text="Show in featured testimonials section"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this testimonial is visible on the website"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Video Testimonial"
        verbose_name_plural = "Video Testimonials"
        ordering = ['order', '-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.student_name} ({self.school_name})"
    
    def video_preview(self):
        """Return HTML for admin video preview"""
        if self.video_file:
            return mark_safe(f'''
                <video width="200" height="150" controls style="border-radius: 8px;">
                    <source src="{self.video_file.url}" type="video/mp4">
                    Your browser does not support the video tag.
                </video>
            ''')
        elif self.video_url:
            if 'youtube.com' in self.video_url or 'youtu.be' in self.video_url:
                # Extract YouTube video ID
                video_id = None
                if 'youtube.com/watch?v=' in self.video_url:
                    video_id = self.video_url.split('v=')[1].split('&')[0]
                elif 'youtu.be/' in self.video_url:
                    video_id = self.video_url.split('youtu.be/')[1].split('?')[0]
                
                if video_id:
                    return mark_safe(f'''
                        <iframe width="200" height="150" 
                                src="https://www.youtube.com/embed/{video_id}" 
                                frameborder="0" allowfullscreen
                                style="border-radius: 8px;">
                        </iframe>
                    ''')
            
            return mark_safe(f'<a href="{self.video_url}" target="_blank">🎥 View Video</a>')
        
        return "No video"
    video_preview.short_description = "Preview"
    
    def get_video_embed_url(self):
        """Convert regular YouTube/Vimeo URLs to embed URLs"""
        if not self.video_url:
            return None
            
        if 'youtube.com' in self.video_url or 'youtu.be' in self.video_url:
            if 'youtube.com/watch?v=' in self.video_url:
                video_id = self.video_url.split('v=')[1].split('&')[0]
            elif 'youtu.be/' in self.video_url:
                video_id = self.video_url.split('youtu.be/')[1].split('?')[0]
            else:
                return None
            return f"https://www.youtube.com/embed/{video_id}"
        
        elif 'vimeo.com' in self.video_url:
            video_id = self.video_url.split('vimeo.com/')[1].split('?')[0]
            return f"https://player.vimeo.com/video/{video_id}"
        
        return self.video_url