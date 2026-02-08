from django.urls import path
from . import views

app_name = 'reviews'

urlpatterns = [
    # Submit reviews and comments
    path('event/<int:event_id>/review/', views.CreateEventReviewView.as_view(), name='create_event_review'),
    path('venue/<int:venue_id>/review/', views.CreateVenueReviewView.as_view(), name='create_venue_review'),
    path('event/<int:event_id>/comment/', views.CreateCommentView.as_view(), name='create_comment'),
    
    # Review management
    path('review/<int:pk>/edit/', views.EditReviewView.as_view(), name='edit_review'),
    path('review/<int:pk>/delete/', views.DeleteReviewView.as_view(), name='delete_review'),
    
    # Comment management
    path('comment/<int:pk>/reply/', views.ReplyToCommentView.as_view(), name='reply_comment'),
    path('comment/<int:pk>/like/', views.LikeCommentView.as_view(), name='like_comment'),
    path('comment/<int:pk>/edit/', views.EditCommentView.as_view(), name='edit_comment'),
    path('comment/<int:pk>/delete/', views.DeleteCommentView.as_view(), name='delete_comment'),
    
    # Review voting
    path('review/<int:pk>/vote/', views.VoteReviewView.as_view(), name='vote_review'),
    
    # Moderation (for admins)
    path('moderate/', views.ModerationDashboardView.as_view(), name='moderation_dashboard'),
    path('review/<int:pk>/approve/', views.ApproveReviewView.as_view(), name='approve_review'),
    path('review/<int:pk>/reject/', views.RejectReviewView.as_view(), name='reject_review'),
    path('comment/<int:pk>/approve/', views.ApproveCommentView.as_view(), name='approve_comment'),
    path('comment/<int:pk>/reject/', views.RejectCommentView.as_view(), name='reject_comment'),
]
