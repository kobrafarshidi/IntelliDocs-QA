from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from django.http import HttpResponse

def home(request):
    return HttpResponse("LLM QA Project is running 🚀")

urlpatterns = [
    path("", home),
    path("admin/", admin.site.urls),
    path("api/", include("documents.urls")),
    path("api/", include("qa.urls")),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="docs"),
]
