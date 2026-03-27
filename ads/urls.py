from django.urls import path, reverse_lazy
from . import views

app_name='ads'
urlpatterns = [
    path('', views.AdListView.as_view(), name='all'),
    path('ad/create', views.AdCreateView.as_view(success_url=reverse_lazy('ads:all')), name='ad_create'),
    path('ad/<int:pk>', views.AdDetailView.as_view(), name='ad_detail'),
    path('ad/<int:pk>/update', views.AdUpdateView.as_view(success_url=reverse_lazy('ads:all')), name='ad_update'),
    path('ad/<int:pk>/delete', views.AdDeleteView.as_view(success_url=reverse_lazy('ads:all')), name='ad_delete'),
    path('ad_picture/<int:pk>', views.stream_file, name='ad_picture'),
    path('ad/<int:pk>/comment', views.CommentCreateView.as_view(), name='ad_comment_create'),
    path('ad/<int:pk>/message', views.MessageCreateView.as_view(), name='ad_message_create'),
    path('message/<int:pk>/reply', views.MessageReplyView.as_view(), name='ad_message_reply'),
    path('comment/<int:pk>/delete', views.CommentDeleteView.as_view(success_url=reverse_lazy('ads')), name='ad_comment_delete'),
    path('ad/<int:pk>/favorite',views.AddFavoriteView.as_view(), name='ad_favorite'),
    path('ad/<int:pk>/unfavorite',views.DeleteFavoriteView.as_view(), name='ad_unfavorite'),
    path('comment/<int:pk>/favorite', views.AddCommentFavoriteView.as_view(), name='comment_favorite'),
    path('comment/<int:pk>/unfavorite', views.DeleteCommentFavoriteView.as_view(), name='comment_unfavorite'),
    path('register/', views.register_request, name='register'),
    path('register', views.register_request),  # Backward-compatible route
    path('accounts/register/', views.register_request, name='register_account'),
    path('favorites', views.FavoriteListView.as_view(), name='favorites'),
    path('my-ads', views.MyAdListView.as_view(), name='my_ads'),
]
