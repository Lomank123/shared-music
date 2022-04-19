# Auth

# Sets custom user model
AUTH_USER_MODEL = 'main.CustomUser'

# Login
LOGIN_REDIRECT_URL = '/'
LOGIN_URL = '/login/'

# Logout
LOGOUT_URL = '/logout/'
LOGOUT_REDIRECT_URL = '/login/'
