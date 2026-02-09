from django.urls import path
from . import views

urlpatterns = [
    # --- 1. Admin & Staff Review (MUST BE FIRST) ---
    # Placing these here prevents the standard admin from hijacking these URLs
    path('admin-approval/', views.admin_approval_list, name='admin_approval_list'),
    path('admin/view-profile/<int:agent_id>/',
         views.admin_view_profile, name='admin_view_profile'),
    path('admin/reject-agent/<int:agent_id>/',
         views.reject_agent_action, name='reject_agent_action'),
    path('verify-agent/<int:agent_id>/',
         views.verify_agent_action, name='verify_agent_action'),
    path('admin/payment-approval/', views.admin_payment_approval,
         name='admin_payment_approval'),

    # --- 2. Main Authentication & Home ---
    path('', views.home, name='home'),
    path('login/', views.user_login, name='login'),
    path('register/', views.register, name='register'),
    path('logout/', views.user_logout, name='logout'),

    # --- 3. Dashboards ---
    path('dashboard/', views.dashboard, name='dashboard'),
    path('user_dashboard/', views.user_dashboard, name='user_dashboard'),
    path('agent_dashboard/', views.agent_dashboard, name='agent_dashboard'),

    # --- 4. Agent & Booking Management ---
    path('agents/', views.agent_list, name='agent_list'),
    # This path renders 'agent_detail.html' for regular users
    path('agent-profile/<int:agent_id>/',
         views.agent_detail, name='agent_detail'),
    path('search-agents/', views.search_agents, name='search_agents'),
    path('book-agent/<int:agent_id>/', views.book_agent, name='book_agent'),
    path('my_bookings/', views.my_bookings, name='my_bookings'),
    path('manage_bookings/', views.manage_bookings, name='manage_bookings'),
    path('update-booking/<int:booking_id>/',
         views.update_booking, name='update_booking'),
    path('booking-success/', views.booking_success, name='booking_success'),
    path('verify/', views.agent_verification_setup,
         name='agent_verification_setup'),

    # --- 5. Payments ---
    path('pay/<int:booking_id>/', views.pay_booking, name='pay_booking'),
    path('payment-options/<int:booking_id>/',
         views.payment_options, name='payment_options'),
    path('payment-success/<int:booking_id>/',
         views.payment_success, name='payment_success'),

    # Path to handle the final successful payment logic
    path('pay-success/<int:booking_id>/',
         views.pay_booking, name='pay_booking'),
    path('payment-gateway/bkash/<int:booking_id>/',
         views.bkash_gateway, name='bkash_gateway'),
    path('download-receipt/<int:booking_id>/',
         views.download_receipt, name='download_receipt'),
    path('payment-gateway/nagad/<int:booking_id>/',
         views.nagad_gateway, name='nagad_gateway'),
    path('payment-gateway/rocket/<int:booking_id>/',
         views.rocket_gateway, name='rocket_gateway'),
    path('payment-gateway/dbbl/<int:booking_id>/',
         views.dbbl_gateway, name='dbbl_gateway'),

    # --- 6. Content & Static Pages ---
    path('blog/', views.community_blog, name='blog'),
    path('post/<int:post_id>/', views.post_detail, name='post_detail'),
    path('create-post/', views.create_post, name='create_post'),
    path('support/', views.support_center, name='support'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),

    # ADD THESE TWO LINES
    path('like/<int:post_id>/', views.like_post, name='like_post'),
    path('comment/<int:post_id>/', views.add_comment, name='add_comment'),
    path('submit-review/<int:booking_id>/',
         views.submit_review, name='submit_review'),
    path('edit-booking/<int:booking_id>/',
         views.edit_booking, name='edit_booking'),
    path('cancel-booking/<int:booking_id>/',
         views.cancel_booking, name='cancel_booking'),
    path('confirm-booking/<int:agent_id>/',
         views.confirm_booking, name='confirm_booking'),
    path('receipt/<int:booking_id>/',
         views.download_receipt, name='download_receipt'),
    path('agent-payment/bkash/', views.agent_bkash_gateway,
         name='agent_bkash_gateway'),

    path('registration-agreement/', views.agent_registration_fee,
         name='agent_registration_step'),
    path('registration-fee/', views.agent_registration_fee,
         name='agent_registration_fee'),
    path('agent-payment/bkash/', views.agent_bkash_gateway,
         name='agent_bkash_gateway'),
    path('agent-payment/nagad/', views.agent_nagad_gateway,
         name='agent_nagad_gateway'),
    path('agent-payment/rocket/', views.agent_rocket_gateway,
         name='agent_rocket_gateway'),
    path('agent-payment/dbbl/', views.agent_dbbl_gateway,
         name='agent_dbbl_gateway'),
    path('pay-booking/<int:booking_id>/',
         views.pay_booking, name='pay_booking'),
    path('agent/edit-profile/', views.agent_edit_profile,
         name='agent_edit_profile'),
    path('registration-receipt/', views.registration_receipt,
         name='registration_receipt'),  # Add this line
]
