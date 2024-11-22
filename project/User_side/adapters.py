from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.exceptions import ImmediateHttpResponse
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth import login, get_user_model  # Import default User model

# Use get_user_model() to refer to the default or custom user model
User = get_user_model()

class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        user = sociallogin.user

        # If the user is already authenticated, exit early
        if user.id:
            return

        try:
            # Check if a user with the same email exists in the User model
            existing_user = User.objects.get(email=user.email)

            # Connect the social login to the existing user
            sociallogin.connect(request, existing_user)

            # Log the user in using Django's authentication system
            login(request, existing_user, backend='django.contrib.auth.backends.ModelBackend')

            # Show a success message
            messages.success(request, 'Your Google account has been connected to your existing account.')

            # Redirect the user to the home page
            raise ImmediateHttpResponse(redirect('home'))

        except User.DoesNotExist:
            # If no user with the email exists, continue with the signup flow
            pass
