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