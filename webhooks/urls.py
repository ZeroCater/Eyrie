from django.conf.urls import url

from webhooks import views

urlpatterns = [
    url(r'^webhook$', views.WebhookView, name='webhook'),
]
