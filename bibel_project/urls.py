"""
URL configuration for bibel_project project.
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.http import JsonResponse
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

def health_check(request):
    return JsonResponse({"status": "ok", "message": "Bible Quiz API is running"})

def api_root(request):
    """API root endpoint showing available endpoints"""
    return JsonResponse({
        "status": "success",
        "message": "Bible Quiz API",
        "endpoints": {
            "bible": {
                "base": "/api/bible/",
                "endpoints": [
                    "GET /languages",
                    "GET /books/by-language?language=en",
                    "GET /testaments/{testament}/books",
                    "GET /books/{book_name}",
                    "GET /books/{book_name}/chapters",
                    "GET /books/{book_name}/chapters/{chapter}",
                    "GET /books/{book_name}/chapters/{chapter}/verses/{verse}",
                    "GET /search?q=query&language=en",
                    "GET /verse-of-the-day"
                ]
            },
            "auth": {
                "base": "/api/auth/",
                "endpoints": [
                    "POST /register",
                    "POST /login",
                    "POST /logout",
                    "POST /verify-email",
                    "POST /forgot-password",
                    "POST /reset-password",
                    "POST /google/",
                    "GET /google/redirect/",
                    "GET /google/callback/",
                    "POST /google/callback/",
                ]
            },
            "user": {
                "base": "/api/user/",
                "endpoints": [
                    "GET /profile",
                    "PUT /profile",
                    "POST /change-password",
                    "GET /complete-profile",
                    "GET /statistics",
                    "GET /quiz-history",
                    "GET /in-progress",
                    "POST /quiz/start",
                    "POST /quiz/submit-answer",
                    "POST /quiz/complete",
                    "GET /quiz/resume?attempt_id=123",
                    "GET /book-progress",
                    "POST /update-progress"
                ]
            },
            "documentation": {
                "swagger": "/swagger/",
                "redoc": "/redoc/"
            }
        }
    }, status=200)

# Swagger schema view
schema_view = get_schema_view(
    openapi.Info(
        title="Bible Quiz API",
        default_version='v1',
        description="API for Bible Quiz Application",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="contact@biblequiz.local"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    # Health check
    path('', health_check, name='health'),
    
    # API root
    path('api/', api_root, name='api-root'),
    
    # Admin
    path('admin/', admin.site.urls),
    
    # Django Allauth URLs (for Google OAuth and social login)
    path('accounts/', include('allauth.urls')),
    
    # Swagger
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    re_path(r'^swagger\.json$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    
    # API endpoints
    path('api/bible/', include('core.urls.bible_urls')),
    path('api/auth/', include('core.urls.auth_urls')),  # This now includes Google OAuth
    path('api/user/', include('core.urls.user_urls')),
    path('api/users/', include('core.urls.user_urls')),  # Alias for /api/user/
    path('api/quiz/', include('core.urls.quiz_urls')),
    path('api/admin/', include('core.urls.admin_urls')),
]