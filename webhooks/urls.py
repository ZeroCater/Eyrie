from django.conf.urls import url

from webhooks import views

urlpatterns = [
    url(r'^hooks/github$', views.github_webhook, name='hooksgithub'),
]
