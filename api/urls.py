from django.urls import path,  include
from . import views
from authentication.views import RegistrationAPIView, LoginAPIView, UserRetrieveUpdateAPIView


urlpatterns = [
    path('', views.PostList.as_view(), name='home'),
    path('registration', RegistrationAPIView.as_view(), name='registration'),
    path('login', LoginAPIView.as_view(), name='login'),
    path('user', UserRetrieveUpdateAPIView.as_view(), name='user'),
    path('<int:pk>', views.PostDetail.as_view(), name='post'),
    path('<int:pk>/like', views.PostLike.as_view(), name='post_like'),
    path('<int:pk>/comments', views.PostComment.as_view(), name='post_comments'),
    path('analytics/date_from=<str:date_from>&date_to=<str:date_to>', views.Analytics.as_view(), name='analytics'),
    # Example url (analytics/date_from=2021-04-04&date_to=2021-04-06)
    path('<int:pk>/backup', views.PostBackup.as_view(), name='post_backup'),
]
