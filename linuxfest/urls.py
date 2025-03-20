from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

urlpatterns = [
    path('', TemplateView.as_view(template_name='home.html'), name='home'),
    path('admin/', admin.site.urls),
    path('events/', include('events.urls', namespace='events')),
    path('dashboard/', include('dashboard.urls', namespace='dashboard')),
    path('registrations/', include('registrations.urls', namespace='registrations')),
    path('checkin/', include('checkin.urls', namespace='checkin')),
    path('accounts/', include('django.contrib.auth.urls')),  # Added for login functionality
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
