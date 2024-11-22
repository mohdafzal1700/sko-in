from django.shortcuts import redirect
from django.urls import reverse

class AdminAccessMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Check if the path is for the admin and if the user is not a superuser
        if request.path.startswith('/admin/') and not request.user.is_superuser:
            # Redirect to the admin login page if the user is not a superuser
            return redirect(reverse('adminlogin'))

        # Process the request and get the response
        response = self.get_response(request)
        return response
