from allauth.account.adapter import DefaultAccountAdapter
from django.urls import reverse


class CustomAccountAdapter(DefaultAccountAdapter):
    """
    Custom account adapter to handle role-based redirects after login.
    """
    
    def get_login_redirect_url(self, request):
        """
        Redirect users to their role-specific dashboard after login.
        """
        user = request.user
        
        if user.is_authenticated:
            # Super Admin → Admin Dashboard
            if user.is_admin_user():
                return reverse('dashboard:admin_dashboard')
            
            # Pharmacist → Pharmacist Dashboard
            elif user.is_pharmacist():
                return reverse('dashboard:pharmacist_dashboard')
            
            # Customer → Customer Dashboard
            elif user.is_customer():
                return reverse('dashboard:customer_dashboard')
        
        # Default fallback to homepage
        return reverse('catalog:home')
    
    def get_signup_redirect_url(self, request):
        """
        Redirect users to their role-specific dashboard after signup.
        New users are customers by default.
        """
        return reverse('dashboard:customer_dashboard')
