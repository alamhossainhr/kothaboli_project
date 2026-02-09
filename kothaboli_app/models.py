from django.db import models
from django.contrib.auth.models import User

# --- 1. User Profile ---


class UserProfile(models.Model):
    ROLE_CHOICES = (('user', 'User'), ('agent', 'Agent'))
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    full_name = models.CharField(max_length=100)
    mobile_number = models.CharField(max_length=15)

    def __str__(self):
        return self.full_name

# --- 2. Agent Profile (Defined before Booking to avoid E300 error) ---


class AgentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    bio = models.TextField(null=True, blank=True)
    hourly_rate = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00)
    is_available = models.BooleanField(default=True)
    is_online = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)  # Verification status
    is_activated = models.BooleanField(default=False)  # Activation fee status
    # --- ADD THIS FIELD FOR REJECTION NOTIFICATIONS ---
    rejection_reason = models.TextField(null=True, blank=True)
    rating = models.DecimalField(max_digits=3, decimal_places=1, default=0.0)
    # Images and Documents
    profile_image = models.ImageField(
        upload_to='agents/profiles/', null=True, blank=True)
    identity_document = models.FileField(
        upload_to='agents/documents/', null=True, blank=True)
    phone_number = models.CharField(max_length=15, null=True, blank=True)
    # Address Details
    present_address = models.TextField(null=True, blank=True)
    permanent_address = models.TextField(null=True, blank=True)

    # Relative Information
    relative_name = models.CharField(max_length=100, null=True, blank=True)
    relative_mobile = models.CharField(max_length=15, null=True, blank=True)

    # Nominee Information
    nominee_name = models.CharField(max_length=100, null=True, blank=True)
    nominee_mobile = models.CharField(max_length=15, null=True, blank=True)
    nominee_nid = models.CharField(max_length=20, null=True, blank=True)
    dob = models.DateField(null=True, blank=True)
    # Becomes True after Fee Payment
    is_activated = models.BooleanField(default=False)
    agreement_accepted = models.BooleanField(
        default=False)  # New tracking field

    # Earnings tracking
    total_earned = models.DecimalField(
        max_digits=12, decimal_places=2, default=0.00)
    net_balance = models.DecimalField(
        max_digits=12, decimal_places=2, default=0.00)  # Amount after 20% cut

    def __str__(self):
        return self.user.username

# --- 3. Booking Model ---


# models.py
class Booking(models.Model):
    # Core Relationships
    client = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='client_bookings')
    agent = models.ForeignKey(
        AgentProfile, on_delete=models.CASCADE, related_name='agent_tasks')

    # Time Tracking Fields
    scheduled_time = models.DateTimeField(null=True, blank=True)
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)

    # Financials
    total_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00)
    is_paid = models.BooleanField(default=False)

    # Payment Gateway Data
    payment_method = models.CharField(max_length=20, blank=True, null=True)
    sender_number = models.CharField(max_length=15, blank=True, null=True)
    transaction_id = models.CharField(max_length=50, blank=True, null=True)
    total_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00)
    duration_minutes = models.IntegerField(
        default=0)  # Add this to track minutes
    # Status Management
    STATUS_CHOICES = (
        ('pending', 'Pending Approval'),
        ('approved', 'Paid'),
        ('rejected', 'Payment Failed/Rejected'),
    )
    payment_status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='pending')

    def __str__(self):
        return f"Booking {self.id} - {self.client.username}"


# --- 4. Post/Story Model ---


class Post(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    # Track likes using a Many-to-Many relationship
    likes = models.ManyToManyField(User, related_name='blog_likes', blank=True)

    def total_likes(self):
        return self.likes.count()


class Comment(models.Model):
    post = models.ForeignKey(
        Post, related_name="comments", on_delete=models.CASCADE)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)


class Review(models.Model):
    booking = models.OneToOneField(
        Booking, on_delete=models.CASCADE, related_name='review')
    client = models.ForeignKey(User, on_delete=models.CASCADE)
    agent = models.ForeignKey(AgentProfile, on_delete=models.CASCADE)
    rating = models.IntegerField(default=5)  # 1 to 5 stars
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class Transaction(models.Model):
    PAYMENT_TYPES = (
        ('booking', 'User Booking Fee'),
        ('registration', 'Agent Registration Fee'),
    )

    PAYMENT_METHODS = (
        ('bkash', 'bKash'),
        ('nagad', 'Nagad'),
        ('rocket', 'Rocket'),
        ('dbbl', 'DBBL Card'),
    )

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='transactions')
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPES)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_id = models.CharField(max_length=100, unique=True)
    sender_number = models.CharField(max_length=15)
    # pending, approved, rejected
    status = models.CharField(max_length=20, default='pending')
    created_at = models.DateTimeField(
        auto_now_add=True)  # THIS FIXES THE ERROR

    def __str__(self):
        return f"{self.payment_type} - {self.transaction_id} ({self.status})"
