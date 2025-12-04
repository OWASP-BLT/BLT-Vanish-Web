"""
Main URL configuration for SelfErase Web Monitoring Backend
"""
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from django.views.generic import RedirectView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # API Authentication
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # App URLs
    path('api/accounts/', include('accounts.urls', namespace='accounts')),
    path('api/monitoring/', include('monitoring.urls', namespace='monitoring')),
    
    # Web Interface URLs
    path('accounts/', include('accounts.web_urls', namespace='web_accounts')),
    path('monitoring/', include('monitoring.web_urls', namespace='web_monitoring')),
    
    # Root redirect
    path('', RedirectView.as_view(url='monitoring/', permanent=False), name='home'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
