from requests import request
from .models import Booking, Transaction
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.db.models import Q
from .models import AgentProfile
from django.db.models import Sum
# Add Review here
from .models import UserProfile, Post, Booking, AgentProfile, Comment, Review
from decimal import Decimal  # Add this import at the top
from django.utils import timezone
from .models import Booking, Review
from datetime import datetime
from django.contrib.auth.decorators import user_passes_test
from django.db import IntegrityError
# --- 1. Authentication ---


def home(request): return render(request, 'home.html')


def register(request):
    if request.method == "POST":
        u_name = request.POST.get('username')
        u_email = request.POST.get('email')
        u_pass = request.POST.get('password')
        u_role = request.POST.get('role')
        if User.objects.filter(username=u_name).exists():
            messages.error(request, "ইউজারনেমটি ইতিমধ্যে ব্যবহৃত হয়েছে।")
        else:
            new_user = User.objects.create_user(
                username=u_name, email=u_email, password=u_pass)
            UserProfile.objects.create(user=new_user, role=u_role, full_name=request.POST.get(
                'full_name'), mobile_number=request.POST.get('mobile_number'))
            if u_role == 'agent':
                AgentProfile.objects.get_or_create(user=new_user)
            messages.success(request, "নিবন্ধন সফল হয়েছে!")
            return redirect('login')
    return render(request, 'register.html')


def user_login(request):
    if request.method == "POST":
        user = authenticate(request, username=request.POST.get(
            'username'), password=request.POST.get('password'))
        if user:
            login(request, user)
            return redirect('dashboard')
        messages.error(request, "ইউজারনেম বা পাসওয়ার্ড সঠিক নয়।")
    return render(request, 'login.html')


def user_logout(request): logout(request); return redirect('home')

# --- 2. Dashboards ---


@login_required
def dashboard(request):
    try:
        if request.user.userprofile.role == 'agent':
            return redirect('agent_dashboard')
        return redirect('user_dashboard')
    except UserProfile.DoesNotExist:
        UserProfile.objects.create(
            user=request.user, role='user', full_name=request.user.username, mobile_number="000")
        return redirect('user_dashboard')


@login_required
def user_dashboard(request): return render(request, 'user_dashboard.html')


@login_required
def agent_dashboard(request):
    agent_prof = get_object_or_404(AgentProfile, user=request.user)

    # 1. Financial Calculations (Dynamic from Paid Bookings)
    paid_bookings = Booking.objects.filter(agent=agent_prof, is_paid=True)
    total_calls = paid_bookings.count()
    gross_total = paid_bookings.aggregate(Sum('total_amount'))[
        'total_amount__sum'] or 0
    gross_earnings = float(gross_total)
    total_minutes = paid_bookings.aggregate(Sum('duration_minutes'))[
        'duration_minutes__sum'] or 0
    commission_amount = gross_earnings * 0.20
    net_balance = gross_earnings - commission_amount

    # 2. Fetch Recent Bookings
    recent_bookings = Booking.objects.filter(
        agent=agent_prof).order_by('-id')[:5]

    # 3. Profile Completion Logic (REQUIRED to fix NameError)
    required_fields = [
        agent_prof.profile_image, agent_prof.identity_document,
        agent_prof.present_address, agent_prof.permanent_address,
        agent_prof.relative_name, agent_prof.relative_mobile,
        agent_prof.nominee_name, agent_prof.nominee_mobile,
        agent_prof.nominee_nid, agent_prof.dob
    ]
    filled = sum(1 for f in required_fields if f)
    # This defines the 'completion' variable that was causing the error
    completion = int((filled / len(required_fields))
                     * 100) if required_fields else 0
    reg_payment = Transaction.objects.filter(
        user=request.user,
        payment_type='registration',
        status='approved'
    ).first()

    context = {
        'agent_prof': agent_prof,
        'recent_bookings': recent_bookings,
        'gross_earnings': f"{gross_earnings:.2f}",
        'total_calls': total_calls,  # Add this to fix the 0 display
        'total_minutes': total_minutes,  # New tracker variable
        'commission_amount': f"{commission_amount:.2f}",
        'net_balance': f"{net_balance:.2f}",
        'actual_score': agent_prof.rating if agent_prof.rating else "0.0",
        'completion': completion,  # Now 'completion' is defined!
        'reg_payment': reg_payment,  # CRITICAL: This allows the button to show
    }
    return render(request, 'agent_dashboard.html', context)

# --- 3. Agent & Booking Actions ---


def agent_list(request):
    # Only show agents who are verified AND activated
    agents = AgentProfile.objects.filter(is_verified=True, is_activated=True)
    return render(request, 'agent_list.html', {'agents': agents})


def search_agents(request):
    query = request.GET.get('q', '')
    # Filter by name while ensuring they are verified
    agents = AgentProfile.objects.filter(
        Q(user__userprofile__full_name__icontains=query),
        is_verified=True,
        is_activated=True
    ).select_related('user__userprofile')

    return render(request, 'agent_list.html', {'agents': agents, 'query': query})


@login_required
def agent_detail(request, agent_id):
    """Missing function required for URL patterns."""
    agent = get_object_or_404(AgentProfile, id=agent_id)
    return render(request, 'agent_detail.html', {'agent': agent})


@login_required
def book_agent(request, agent_id):
    agent = get_object_or_404(AgentProfile, id=agent_id)
    rate_per_minute = 10  # This should ideally come from agent.hourly_rate / 60

    if request.method == "POST":
        start_str = request.POST.get('start_time')
        end_str = request.POST.get('end_time')

        start_time = datetime.strptime(start_str, '%Y-%m-%dT%H:%M')
        end_time = datetime.strptime(end_str, '%Y-%m-%dT%H:%M')

        # Calculate difference in minutes
        duration = end_time - start_time
        duration_minutes = duration.total_seconds() / 60
        total_charge = duration_minutes * rate_per_minute

        # Save booking with the calculated charge
        booking = Booking.objects.create(
            client=request.user,
            agent=agent,
            start_time=start_time,
            end_time=end_time,
            total_amount=total_charge,
            payment_status='pending'
        )
        return redirect('my_bookings')

    return render(request, 'book_agent.html', {'agent': agent})


@login_required
def my_bookings(request):
    bookings = Booking.objects.filter(
        client=request.user).order_by('-scheduled_time')

    return render(request, 'my_bookings.html', {'bookings': bookings})


@login_required
def manage_bookings(request):
    agent_prof = get_object_or_404(AgentProfile, user=request.user)
    bookings = Booking.objects.filter(
        agent=agent_prof).order_by('-scheduled_time')
    return render(request, 'manage_bookings.html', {'bookings': bookings})


@login_required
def update_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    if request.method == "POST":
        booking.is_paid = request.POST.get('is_paid') == 'on'
        booking.save()
        return redirect('manage_bookings')
    return render(request, 'update_booking.html', {'booking': booking})

# --- 4. Payments ---


@login_required
def payment_options(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, client=request.user)
    # The agent's hourly rate acts as the total amount
    total_amount = booking.agent.hourly_rate
    return render(request, 'pay_booking.html', {
        'booking': booking,
        'total_amount': total_amount
    })


@login_required
def payment_success(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, client=request.user)
    booking.is_paid = True
    booking.save()
    return render(request, 'payment_success.html', {'booking': booking})


# views.py
@login_required
def pay_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, client=request.user)

    # Change 'payment_success.html' to 'pay_booking.html'
    return render(request, 'pay_booking.html', {
        'booking': booking,
        'agent': booking.agent
    })

# --- 5. Community ---


@login_required
def community_blog(request):
    posts = Post.objects.all().order_by('-created_at')
    return render(request, 'blog.html', {'posts': posts})


@login_required
def create_post(request):
    if request.method == "POST" and request.POST.get('content'):
        Post.objects.create(author=request.user,
                            content=request.POST.get('content'))
    return redirect('blog')


@login_required
def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    return render(request, 'post_detail.html', {'post': post})


@login_required
def like_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if post.likes.filter(id=request.user.id).exists():
        post.likes.remove(request.user)
    else:
        post.likes.add(request.user)
    return redirect('blog')


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.method == "POST":
        content = request.POST.get('comment_text')
        if content:
            Comment.objects.create(
                post=post, author=request.user, text=content)
    return redirect('blog')

# --- 6. AGENT VERIFICATION & ADMIN APPROVAL ---


@login_required
def agent_verification_setup(request):
    agent_prof, created = AgentProfile.objects.get_or_create(user=request.user)

    if request.method == "POST":
        # 1. Capture Data (Addresses, Relatives, Nominee)
        agent_prof.present_address = request.POST.get('present_address')
        agent_prof.permanent_address = request.POST.get('permanent_address')
        agent_prof.relative_name = request.POST.get('relative_name')
        agent_prof.relative_mobile = request.POST.get('relative_mobile')
        agent_prof.nominee_name = request.POST.get('nominee_name')
        agent_prof.nominee_mobile = request.POST.get('nominee_mobile')
        agent_prof.nominee_nid = request.POST.get('nominee_nid')
        agent_prof.hourly_rate = request.POST.get('hourly_rate')
        dob = request.POST.get('dob')
        if dob:
            agent_prof.dob = dob
        # 2. Handle File Uploads
        if request.FILES.get('profile_image'):
            agent_prof.profile_image = request.FILES.get('profile_image')
        if request.FILES.get('identity_document'):
            agent_prof.identity_document = request.FILES.get(
                'identity_document')

        # 3. SECURITY CHECK: Ensure fee is paid
        if not agent_prof.is_activated:
            messages.warning(
                request, "প্রোফাইল আপডেট করার আগে নিবন্ধন ফি প্রদান করুন!")
            return redirect('agent_registration_fee')

        # 4. RESET STATUS (The marked area in your screenshot)
        # This clears the old rejection and sends it back to Admin for review
        agent_prof.rejection_reason = ""
        agent_prof.is_verified = False

        agent_prof.save()  # This saves ALL changes above to the DB

        messages.success(
            request, "আপনার তথ্য সফলভাবে সংরক্ষিত হয়েছে এবং যাচাইয়ের জন্য পাঠানো হয়েছে!")
        return redirect('agent_dashboard')

    return render(request, 'agent_verification.html', {'agent_prof': agent_prof})

# kothaboli_app/views.py


@login_required
def admin_approval_list(request):
    if not request.user.is_staff:
        return redirect('dashboard')

    # Use 'all_agents' to match your revised template
    all_agents = AgentProfile.objects.all().order_by('-id')

    return render(request, 'admin_approval.html', {'all_agents': all_agents})


@login_required
def admin_view_profile(request, agent_id):
    if not request.user.is_staff:
        return redirect('dashboard')
    agent = get_object_or_404(AgentProfile, id=agent_id)
    return render(request, 'admin_agent_detail.html', {'agent': agent})


@login_required
def verify_agent_action(request, agent_id):
    if not request.user.is_staff:
        return redirect('login')
    agent = get_object_or_404(AgentProfile, id=agent_id)
    agent.is_verified = True
    agent.save()
    messages.success(request, f"{agent.user.username} ভেরিফাই করা হয়েছে!")
    return redirect('admin_approval_list')


# kothaboli_app/views.py

# kothaboli_app/views.py
@login_required
def reject_agent_action(request, agent_id):
    if not request.user.is_staff:
        return redirect('dashboard')
    if request.method == "POST":
        agent = get_object_or_404(AgentProfile, id=agent_id)
        # Reset flags so status changes to Rejected
        agent.is_verified = False
        agent.rejection_reason = request.POST.get('rejection_reason')
        agent.save()
        messages.warning(request, "প্রোফাইলটি রিজেক্ট করা হয়েছে।")
    return redirect('admin_approval_list')

# kothaboli_app/views.py


# views.py
@login_required
def agent_registration_fee(request):
    agent_prof, _ = AgentProfile.objects.get_or_create(user=request.user)

    if request.method == "POST":
        # 1. Create a Pending record for Admin to see
        Booking.objects.create(
            client=request.user,  # The Agent acting as the client for this fee
            agent=agent_prof,
            payment_method=request.POST.get('payment_method', 'Nagad'),
            sender_number=request.POST.get('sender_number'),
            transaction_id=request.POST.get('transaction_id'),
            total_amount=Decimal('500.00'),
            payment_status='pending',  # THIS MAKES IT VISIBLE TO ADMIN
            is_paid=False
        )

        # 2. Mark as 'Activated' but not 'Verified' yet
        agent_prof.is_activated = True
        agent_prof.save()

        messages.info(
            request, "আপনার পেমেন্ট এডমিন রিভিউয়ের জন্য পাঠানো হয়েছে।")
        return redirect('agent_dashboard')

    return render(request, 'agent_registration_fee.html', {'amount': '500.00'})

# kothaboli_app/views.py


@login_required
def complete_payment_logic(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    agent = booking.agent

    if not booking.is_paid:
        amount = agent.hourly_rate
        # Calculate 20% App Cut
        app_commission = amount * 0.20
        agent_earnings = amount - app_commission

        # Update Agent Ledger
        agent.total_earned += amount
        agent.net_balance += agent_earnings

        booking.is_paid = True
        booking.save()
        agent.save()

    return redirect('agent_dashboard')


@login_required
def submit_review(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, client=request.user)
    if request.method == "POST":
        rating = request.POST.get('rating')
        comment = request.POST.get('comment')

        # Create the review record
        Review.objects.create(
            booking=booking,
            client=request.user,
            agent=booking.agent,
            rating=rating,
            comment=comment
        )

        # Update the Agent's average rating
        all_reviews = Review.objects.filter(agent=booking.agent)
        avg_rating = sum(r.rating for r in all_reviews) / all_reviews.count()
        booking.agent.rating = round(avg_rating, 1)
        booking.agent.save()

        messages.success(request, "আপনার রিভিউ সফলভাবে গ্রহণ করা হয়েছে!")
    return redirect('my_bookings')


@login_required
def bkash_gateway(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, client=request.user)
    amount = Decimal(str(booking.agent.hourly_rate))
    commission = amount * Decimal('0.20')

    if request.method == "POST":
        # Resolve the TypeError by using Decimal
        app_commission = amount * Decimal('0.20')
        agent_earnings = amount - app_commission

        # Update Agent Balances
        booking.agent.total_earned += amount
        booking.agent.net_balance += agent_earnings

        booking.is_paid = True
        booking.save()
        booking.agent.save()

        # SUCCESS: Redirect to the receipt view instead of a missing template
        messages.success(request, "পেমেন্ট সফল হয়েছে!")
        return redirect('download_receipt', booking_id=booking.id)

    return render(request, 'bkash_gateway.html', {'booking': booking, 'amount': amount})


# views.py
@login_required
def agent_dbbl_gateway(request):
    amount = 500.00
    if request.method == "POST":
        # Capture the Card/Account Number and TrxID
        trx_id = request.POST.get('transaction_id')
        card_no = request.POST.get('phone_number')

        # 1. Check for Duplicate Transaction ID
        if Transaction.objects.filter(transaction_id=trx_id).exists():
            messages.error(request, "Your transaction id is already exist!")
            return render(request, 'agent_dbbl_gateway.html', {'amount': amount})

        # 2. Save as registration transaction
        Transaction.objects.create(
            user=request.user,
            payment_type='registration',
            payment_method='DBBL',
            amount=amount,
            transaction_id=trx_id,
            sender_number=card_no,
            status='pending'
        )
        messages.success(
            request, "পেমেন্ট জমা হয়েছে। এডমিন যাচাইয়ের পর একাউন্ট সচল হবে।")
        return redirect('agent_dashboard')

    return render(request, 'agent_dbbl_gateway.html', {'amount': amount})


# views.py
@login_required
def agent_nagad_gateway(request):
    amount = 500.00
    if request.method == "POST":
        trx_id = request.POST.get('transaction_id')
        phone = request.POST.get('phone_number')

        # 1. DUPLICATE CHECK: Prevents server crash
        if Transaction.objects.filter(transaction_id=trx_id).exists():
            messages.error(request, "Your transaction id is already exist!")
            return render(request, 'agent_nagad_gateway.html', {'amount': amount})

        # 2. SAVE: visible in Unified Payment Approval Center
        Transaction.objects.create(
            user=request.user,
            payment_type='registration',
            payment_method='Nagad',
            amount=amount,
            transaction_id=trx_id,
            sender_number=phone,
            status='pending'
        )
        messages.success(
            request, "পেমেন্ট জমা হয়েছে। এডমিন যাচাইয়ের পর একাউন্ট সচল হবে।")
        return redirect('agent_dashboard')

    return render(request, 'agent_nagad_gateway.html', {'amount': amount})

# Rocket Registration


@login_required
@login_required
def agent_rocket_gateway(request):
    amount = 500.00
    if request.method == "POST":
        trx_id = request.POST.get('transaction_id')
        phone = request.POST.get('phone_number')

        # 1. DUPLICATE CHECK
        if Transaction.objects.filter(transaction_id=trx_id).exists():
            messages.error(request, "Your transaction id is already exist!")
            return render(request, 'agent_rocket_gateway.html', {'amount': amount})

        # 2. SAVE
        Transaction.objects.create(
            user=request.user,
            payment_type='registration',
            payment_method='Rocket',
            amount=amount,
            transaction_id=trx_id,
            sender_number=phone,
            status='pending'
        )
        messages.success(
            request, "রকেট পেমেন্ট জমা হয়েছে। এডমিন যাচাইয়ের পর একাউন্ট সচল হবে।")
        return redirect('agent_dashboard')

    return render(request, 'agent_rocket_gateway.html', {'amount': amount})

# DBBL Registration


login_required


def agent_dbbl_gateway(request):
    amount = 500.00
    if request.method == "POST":
        Transaction.objects.create(
            user=request.user,
            payment_type='registration',
            payment_method='DBBL',
            amount=amount,
            transaction_id=request.POST.get('transaction_id'),
            sender_number=request.POST.get('phone_number'),
            status='pending'
        )
        messages.success(
            request, "DBBL নিবন্ধন ফি জমা হয়েছে। যাচাইয়ের পর একাউন্ট সচল হবে।")
        return redirect('agent_dashboard')
    return render(request, 'agent_dbbl_gateway.html', {'amount': amount})


@login_required
def download_receipt(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, client=request.user)

    if not booking.is_paid:
        messages.error(request, "রসিদ ডাউনলোড করার আগে পেমেন্ট সম্পন্ন করুন।")
        return redirect('my_bookings')

    context = {
        # Unique Invoice format

        'client_name': request.user.userprofile.full_name,
        'agent_name': booking.agent.user.userprofile.full_name,
        'amount': booking.agent.hourly_rate,
        'payment_way': "bKash",  # Fetched from payment logic
        'date': timezone.now().date(),
        'time': timezone.now().time(),
        'booking': booking,
        'invoice_no': f"KB-{booking.id:04d}",  # Automatic Serial KB-0012
        'current_date': timezone.now(),

        'payment_method': booking.payment_method,
        'sender_number': booking.sender_number,
        'transaction_id': booking.transaction_id,
    }

    return render(request, 'money_receipt.html', context)


@login_required
def edit_booking(request, booking_id):
    """Allows a user to change the date/time of an unpaid booking."""
    # Security: Ensure the booking belongs to the logged-in user
    booking = get_object_or_404(Booking, id=booking_id, client=request.user)

    # Logic: Prevent editing if payment is already complete
    if booking.is_paid:
        messages.error(request, "পরিশোধিত বুকিং পরিবর্তন করা সম্ভব নয়।")
        return redirect('my_bookings')

    if request.method == "POST":
        new_time = request.POST.get('scheduled_time')
        if new_time:
            booking.scheduled_time = new_time
            booking.save()
            messages.success(request, "বুকিং সময় সফলভাবে আপডেট করা হয়েছে।")
            return redirect('my_bookings')

    return render(request, 'edit_booking.html', {'booking': booking})


@login_required
def cancel_booking(request, booking_id):
    """Removes the booking entry from the database."""
    # Security: Ensure the user can only delete their own data
    booking = get_object_or_404(Booking, id=booking_id, client=request.user)

    # Logic: Paid bookings cannot be deleted directly for accounting reasons
    if booking.is_paid:
        messages.error(request, "পরিশোধিত বুকিং বাতিল করা সম্ভব নয়।")
        return redirect('my_bookings')

    # Action: Delete from kothaboli_app_booking table
    booking.delete()
    messages.success(request, "বুকিংটি সফলভাবে বাতিল করা হয়েছে।")
    return redirect('my_bookings')


@login_required
def nagad_gateway(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, client=request.user)
    amount = Decimal(str(booking.agent.hourly_rate))

    if request.method == "POST":
        # Process financial logic
        booking.agent.total_earned += amount
        booking.agent.net_balance += (amount * Decimal('0.80'))
        booking.is_paid = True
        booking.save()
        booking.agent.save()
        return redirect('download_receipt', booking_id=booking.id)

    return render(request, 'nagad_gateway.html', {'booking': booking, 'amount': amount})


@login_required
def rocket_gateway(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, client=request.user)
    amount = Decimal(str(booking.agent.hourly_rate))  # Fix for TypeError

    if request.method == "POST":
        # Financial logic
        app_commission = amount * Decimal('0.20')
        agent_earnings = amount - app_commission

        # Update Agent Ledger
        booking.agent.total_earned += amount
        booking.agent.net_balance += agent_earnings

        booking.is_paid = True
        booking.save()
        booking.agent.save()

        # Redirect to receipt generation
        messages.success(request, "রকেট পেমেন্ট সফল হয়েছে!")
        return redirect('download_receipt', booking_id=booking.id)

    return render(request, 'rocket_gateway.html', {
        'booking': booking,
        'amount': amount
    })


@login_required
def dbbl_gateway(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, client=request.user)
    amount = Decimal(str(booking.agent.hourly_rate))  # Prevent TypeError

    if request.method == "POST":
        # Capture card details (simulated for this design)
        card_number = request.POST.get('card_number')

        # Financial logic: 20% commission
        app_commission = amount * Decimal('0.20')
        agent_earnings = amount - app_commission

        # Update Agent Ledger in MySQL
        booking.agent.total_earned += amount
        booking.agent.net_balance += agent_earnings

        booking.is_paid = True
        booking.save()
        booking.agent.save()

        messages.success(request, "DBBL কার্ড পেমেন্ট সফল হয়েছে!")
        return redirect('download_receipt', booking_id=booking.id)

    return render(request, 'dbbl_gateway.html', {
        'booking': booking,
        'amount': amount
    })


def confirm_booking(request, agent_id):
    if request.method == "POST":
        scheduled_time = request.POST.get('scheduled_time')
        agent = get_object_or_404(AgentProfile, id=agent_id)

        # Create the booking entry in the database
        Booking.objects.create(
            client=request.user,
            agent=agent,
            scheduled_time=scheduled_time,
            is_paid=False
        )
        messages.success(request, "বুকিং সফলভাবে সেট করা হয়েছে।")
        return redirect('my_bookings')
    return redirect('agent_list')


@login_required
def process_payment(request, booking_id, method_name):
    """Handles financial logic and sets status to pending for admin review."""
    booking = get_object_or_404(Booking, id=booking_id, client=request.user)
    amount = Decimal(str(booking.agent.hourly_rate))

    if request.method == "POST":
        # Capture specific number used
        booking.sender_number = request.POST.get(
            'phone_number') or request.POST.get('card_number')
        booking.transaction_id = request.POST.get(
            'transaction_id') or request.POST.get('cvv')
        booking.payment_method = method_name

        # Admin approval logic
        booking.payment_status = 'pending'
        booking.is_paid = False
        booking.save()

        return redirect('my_bookings')

    return render(request, f'{method_name.lower()}_gateway.html', {'booking': booking, 'amount': amount})


@login_required
def agent_registration_fee(request):
    context = {
        'amount': '500.00',  # Fixed fee attribute
        'booking': None      # Attribute to trigger registration layout
    }
    return render(request, 'agent_registration_fee.html', context)

# views.py


@login_required
def agent_registration_fee(request):
    """
    Renders the payment selection page. 
    Providing 'amount' here fixes the blank display issue.
    """
    context = {
        'amount': '500.00',  # Fixed registration fee
        'booking': None      # Set to None to avoid searching for a booking
    }
    return render(request, 'agent_registration_fee.html', context)

# views.py


# views.py
@login_required
def agent_bkash_gateway(request):
    amount = 500.00
    if request.method == "POST":
        trx_id = request.POST.get('transaction_id')
        phone = request.POST.get('phone_number')

        # 1. Check for Duplicate Transaction ID
        if Transaction.objects.filter(transaction_id=trx_id).exists():
            messages.error(
                request, "আপনার ট্রান্সজেকশন আইডি ইতোমধ্যে পাঠানো হয়েছে!")
            return render(request, 'agent_bkash_gateway.html', {'amount': amount})

        # 2. Save specifically as a 'registration' transaction
        Transaction.objects.create(
            user=request.user,
            payment_type='registration',
            payment_method='bKash',
            amount=amount,
            transaction_id=trx_id,
            sender_number=phone,
            status='pending'
        )
        messages.success(
            request, "বিকাশ নিবন্ধন ফি জমা হয়েছে। এডমিন যাচাইয়ের পর একাউন্ট সচল হবে।")
        return redirect('agent_dashboard')

    return render(request, 'agent_bkash_gateway.html', {'amount': amount})


# views.py
@user_passes_test(lambda u: u.is_superuser)
def admin_payment_approval(request):
    if request.method == "POST":
        obj_id = request.POST.get('obj_id')
        model_type = request.POST.get('model_type')
        action = request.POST.get('action')

        if model_type == 'booking':
            item = get_object_or_404(Booking, id=obj_id)
            if action == 'approve':
                item.payment_status = 'approved'
                item.is_paid = True
            elif action == 'reject':
                item.payment_status = 'rejected'
            item.save()

        elif model_type == 'registration':
            item = get_object_or_404(Transaction, id=obj_id)
            if action == 'approve':
                item.status = 'approved'
                # Activate and Verify the agent upon registration approval
                agent_prof = get_object_or_404(AgentProfile, user=item.user)
                agent_prof.is_activated = True
                agent_prof.is_verified = True
                agent_prof.save()
            elif action == 'reject':
                item.status = 'rejected'
            item.save()

        return redirect('admin_payment_approval')

    # Fetch data for unified list
    bookings = Booking.objects.filter(payment_status='pending')
    registrations = Transaction.objects.filter(
        status='pending', payment_type='registration')

    all_pending = []
    for b in bookings:
        all_pending.append({
            'id': b.id,
            'user': b.client.userprofile.full_name,
            'username': b.client.username,
            'method': b.payment_method,
            'number': b.sender_number,
            'trxid': b.transaction_id,
            'amount': b.total_amount,
            'type': 'Booking',
            'model_type': 'booking'
        })

    for r in registrations:
        all_pending.append({
            'id': r.id,
            'user': r.user.userprofile.full_name,
            'username': r.user.username,
            'method': r.payment_method,
            'number': r.sender_number,
            'trxid': r.transaction_id,
            'amount': r.amount,
            'type': 'Registration',
            'model_type': 'registration'
        })

    return render(request, 'admin_payment_approval.html', {'all_pending': all_pending})


@login_required
def agent_payment_gateway(request, method_name):
    """Unified logic with duplicate ID check."""
    amount = 500.00
    template_name = f'agent_{method_name.lower()}_gateway.html'

    if request.method == "POST":
        trx_id = request.POST.get('transaction_id')
        phone = request.POST.get('phone_number')

        # 1. CHECK IF TRANSACTION ID ALREADY EXISTS
        if Transaction.objects.filter(transaction_id=trx_id).exists():
            messages.error(
                request, "আপনার ট্রান্সজেকশন আইডি ইতোমধ্যে পাঠানো হয়েছে!")
            return render(request, template_name, {'amount': amount})

        try:
            # 2. SAVE AS REGISTRATION TRANSACTION
            Transaction.objects.create(
                user=request.user,
                payment_type='registration',
                payment_method=method_name,
                amount=amount,
                transaction_id=trx_id,
                sender_number=phone,
                status='pending'
            )
            messages.success(
                request, f"{method_name} পেমেন্ট জমা হয়েছে। এডমিন যাচাই করার পর একাউন্ট সচল হবে।")
            return redirect('agent_dashboard')

        except IntegrityError:
            # Fallback if the first check missed a race condition
            messages.error(
                request, "আপনার ট্রান্সজেকশন আইডি ইতোমধ্যে পাঠানো হয়েছে!")
            return render(request, template_name, {'amount': amount})

    return render(request, template_name, {'amount': amount})

# Specific Handlers


def agent_bkash_gateway(
    request): return agent_payment_gateway(request, 'bKash')


def agent_nagad_gateway(
    request): return agent_payment_gateway(request, 'Nagad')
def agent_rocket_gateway(
    request): return agent_payment_gateway(request, 'Rocket')


def agent_dbbl_gateway(request): return agent_payment_gateway(request, 'DBBL')

# views.py


# views.py
@login_required
def registration_receipt(request):
    reg_payment = Transaction.objects.filter(
        user=request.user,
        payment_type='registration',
        status='approved'
    ).order_by('-id').first()  # Prevents MultipleObjectsReturned error

    if not reg_payment:
        return redirect('agent_dashboard')

    return render(request, 'registration_receipt.html', {'reg_payment': reg_payment})


@login_required
def agent_edit_profile(request):
    agent_prof = get_object_or_404(AgentProfile, user=request.user)

    if request.method == "POST":
        # Save Address Info
        agent_prof.present_address = request.POST.get('present_address')
        agent_prof.permanent_address = request.POST.get('permanent_address')

        # Save Relative & Nominee Info
        agent_prof.relative_name = request.POST.get('relative_name')
        agent_prof.relative_mobile = request.POST.get('relative_mobile')
        agent_prof.nominee_name = request.POST.get('nominee_name')
        agent_prof.nominee_mobile = request.POST.get('nominee_mobile')
        agent_prof.nominee_nid = request.POST.get('nominee_nid')
        agent_prof.phone_number = request.POST.get('phone_number')
        # Save Service Charge & DOB
        agent_prof.hourly_rate = request.POST.get('hourly_rate')
        agent_prof.dob = request.POST.get('dob')

        # Handle File Uploads (Photos & NID)
        if 'profile_image' in request.FILES:
            agent_prof.profile_image = request.FILES['profile_image']
        if 'identity_document' in request.FILES:
            agent_prof.identity_document = request.FILES['identity_document']

        agent_prof.save()
        messages.success(request, "আপনার তথ্য সফলভাবে সংরক্ষিত হয়েছে!")
        return redirect('agent_dashboard')

    return render(request, 'agent_edit_profile.html', {'agent_prof': agent_prof})

# Individual Gateway Views


@login_required
def bkash_gateway(request, booking_id):
    return process_payment(request, booking_id, "bKash")


@login_required
def nagad_gateway(request, booking_id):
    return process_payment(request, booking_id, "Nagad")


@login_required
def rocket_gateway(request, booking_id):
    return process_payment(request, booking_id, "Rocket")


@login_required
def dbbl_gateway(request, booking_id):
    return process_payment(request, booking_id, "DBBL")
# --- Static ---


def support_center(request): return render(request, 'support.html')
def about(request): return render(request, 'about.html')
def contact(request): return render(request, 'contact.html')
def booking_success(request): return render(request, 'booking_success.html')
