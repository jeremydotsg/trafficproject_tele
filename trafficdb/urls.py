from django.urls import path
from trafficdb.views import IndexView, queue_detail, disclaimer
from . import views

app_name = "trafficdb"
urlpatterns = [
    path("", IndexView.as_view(), name="index"),
    path('queues/', views.queue_list, name='queue_list'),
    path('queues/<int:queue_id>/', views.queue_detail, name='queue_detail'),
    path('disclaimer/', disclaimer, name='disclaimer'),
    # path("<int:pk>/", views.DetailView.as_view(), name="detail"),
    # path("<int:pk>/results/", views.ResultsView.as_view(), name="results"),
    # path("<int:question_id>/vote/", views.vote, name="vote"),
]