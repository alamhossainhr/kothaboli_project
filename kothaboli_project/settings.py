# settings.py
import os
import dj_database_url  # ADD THIS IMPORT AT THE TOP

# ... (keep BASE_DIR, SECRET_KEY, etc.)

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # ADD THIS for CSS/Images
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# REMOVE the old MySQL DATABASES block
# USE THIS SINGLE BLOCK INSTEAD:
DATABASES = {
    'default': dj_database_url.config(
        default='sqlite:///db.sqlite3',
        conn_max_age=600
    )
}

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
# This allows Render to serve your dashboard CSS
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
