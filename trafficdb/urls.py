from django.urls import path
from trafficdb.views import IndexView, queue_detail, disclaimer, get_bus_arrivals
from . import views

app_name = "trafficdb"
urlpatterns = [
    path("", views.blog_index, name="blog_index"),
    path("post/<int:pk>/", views.blog_detail, name="blog_detail"),
    path("category/<category>/", views.blog_category, name="blog_category"),
    path("dashboard/", IndexView.as_view(), name="index"),
    path('bus_arrivals919191918888/', get_bus_arrivals, name='bus_arrivals'),
    #path('queues/', views.queue_list, name='queue_list'),
    path('queues/<int:queue_id>/', views.queue_detail, name='queue_detail'),
    path('disclaimer/', disclaimer, name='disclaimer'),
    #path('line_chart/', views.line_chart, name='line_chart'),
    #path('line_chart/json', views.line_chart_json, name='line_chart_json'),
    path('bus_stops/', views.bus_stop_view, name='bus_stops'),
    # path("<int:pk>/", views.DetailView.as_view(), name="detail"),
    # path("<int:pk>/results/", views.ResultsView.as_view(), name="results"),
    # path("<int:question_id>/vote/", views.vote, name="vote"),
]