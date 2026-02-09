from django.contrib import admin
from .models import UserProfile, AgentProfile, Booking, Post

# --- 1. Admin Site Branding ---
admin.site.site_header = "Kotha Boli Administration"
admin.site.index_title = "Manage HR & Agent Operations"

# --- 2. Corrected Menu Redirection Logic ---


class MyAdminSite(admin.AdminSite):
    def get_app_list(self, request, app_label=None):
        app_list = super().get_app_list(request, app_label)

        # New Financial Approval Link
        payment_link = {
            'name': '💰 Payment Approval Center',
            'admin_url': '/admin/payment-approval/',  # Ensure this matches your URL name
            'view_only': True,
        }

        # Existing Agent Approval Link
        agent_link = {
            'name': '🛡️ Agent Approval Center',
            'admin_url': '/admin-approval/',
            'view_only': True,
        }

        for app in app_list:
            if app['app_label'] == 'kothaboli_app':
                # Inserting both custom links at the top of the model list
                app['models'].insert(0, payment_link)
                app['models'].insert(1, agent_link)
        return app_list


admin.site.__class__ = MyAdminSite

# --- 3. Custom Admin Actions ---


@admin.action(description='Approve Selected Payments')
def approve_payments(modeladmin, request, queryset):
    """Updates both status and is_paid fields."""
    queryset.update(payment_status='approved', is_paid=True)

# --- 4. Model Registrations ---


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'user', 'role', 'mobile_number')


@admin.register(AgentProfile)
class AgentProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'is_verified', 'is_activated', 'hourly_rate')
    list_editable = ('is_verified', 'is_activated')


class BookingAdmin(admin.ModelAdmin):
    list_display = ['id', 'client', 'payment_status',
                    'is_paid', 'transaction_id']
    actions = [approve_payments]


# REGISTERED ONLY ONCE TO FIX CRASH
admin.site.register(Booking, BookingAdmin)
admin.site.register(Post)
