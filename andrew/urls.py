from django.conf.urls import url, include
from django.contrib import admin
from django.views.generic.base import TemplateView

urlpatterns = [
    # url(r'^api/', include('gui.urls', namespace='gui')),
    url(r'^admin/', admin.site.urls),
    url("", TemplateView.as_view(template_name="index.html")),

]