from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', include('kothaboli_app.urls')),  # MUST BE FIRST
    path('admin/', admin.site.urls),
]

# urlpatterns = [
# 1. PRIORITY: Custom App Routes
# Includes admin/view-profile/ defined in kothaboli_app.urls
# path('', include('kothaboli_app.urls')),

# 2. STANDARD DJANGO ADMIN
# Must be placed AFTER custom app routes to avoid 404 hijacking
# path('admin/', admin.site.urls),
# ]

# --- MEDIA CONFIGURATION ---
# Serves Agent Photos and NID Documents during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
