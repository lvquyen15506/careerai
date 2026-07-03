"""
URL configuration cho Student Job Platform project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from core import views as oauth_override_views

urlpatterns = [
    # Django Admin
    path('admin/', admin.site.urls),

    # Override Allauth login with custom unified login
    path('accounts/login/', oauth_override_views.unified_login_view, name='account_login'),

    # Allauth (SSO Google/Microsoft)
    path('accounts/', include('allauth.urls')),

    # Core app
    path('', include('core.urls')),
]

# Serve media files trong development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Customize admin site
admin.site.site_header = 'Quản trị Việc làm Sinh viên'
admin.site.site_title = 'Student Job Platform'
admin.site.index_title = 'Bảng điều khiển'
