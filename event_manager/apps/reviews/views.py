from django.shortcuts import render, get_object_or_404
from django.views.generic import TemplateView, View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin


class AdminRequiredMixin(UserPassesTestMixin):
    """Mixin to require admin role"""
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_admin_user


# Stub views for reviews app
class CreateEventReviewView(LoginRequiredMixin, TemplateView):
    template_name = 'reviews/create_event_review.html'

class CreateVenueReviewView(LoginRequiredMixin, TemplateView):
    template_name = 'reviews/create_venue_review.html'

class CreateCommentView(LoginRequiredMixin, TemplateView):
    template_name = 'reviews/create_comment.html'

class EditReviewView(LoginRequiredMixin, TemplateView):
    template_name = 'reviews/edit_review.html'

class DeleteReviewView(LoginRequiredMixin, TemplateView):
    template_name = 'reviews/delete_review.html'

class ReplyToCommentView(LoginRequiredMixin, TemplateView):
    template_name = 'reviews/reply_comment.html'

class LikeCommentView(LoginRequiredMixin, TemplateView):
    template_name = 'reviews/like_comment.html'

class EditCommentView(LoginRequiredMixin, TemplateView):
    template_name = 'reviews/edit_comment.html'

class DeleteCommentView(LoginRequiredMixin, TemplateView):
    template_name = 'reviews/delete_comment.html'

class VoteReviewView(LoginRequiredMixin, TemplateView):
    template_name = 'reviews/vote_review.html'

class ModerationDashboardView(AdminRequiredMixin, TemplateView):
    template_name = 'reviews/moderation_dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from .models import Review, Comment
        
        # Get pending reviews and comments for moderation
        context.update({
            'pending_reviews': Review.objects.filter(status='pending').select_related('user', 'event', 'venue').order_by('-created_at'),
            'pending_comments': Comment.objects.filter(status='pending').select_related('user', 'event').order_by('-created_at'),
            'recent_approved_reviews': Review.objects.filter(status='approved').select_related('user', 'event', 'venue').order_by('-updated_at')[:10],
            'recent_rejected_reviews': Review.objects.filter(status='rejected').select_related('user', 'event', 'venue').order_by('-updated_at')[:10],
            'total_pending_reviews': Review.objects.filter(status='pending').count(),
            'total_pending_comments': Comment.objects.filter(status='pending').count(),
            'total_approved_reviews': Review.objects.filter(status='approved').count(),
            'total_rejected_reviews': Review.objects.filter(status='rejected').count(),
        })
        
        return context

class ApproveReviewView(AdminRequiredMixin, View):
    def post(self, request, pk):
        from django.http import JsonResponse
        from .models import Review
        
        try:
            review = get_object_or_404(Review, pk=pk)
            review.status = 'approved'
            review.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Review approved successfully'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)

class RejectReviewView(AdminRequiredMixin, View):
    def post(self, request, pk):
        from django.http import JsonResponse
        from .models import Review
        
        try:
            review = get_object_or_404(Review, pk=pk)
            review.status = 'rejected'
            review.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Review rejected successfully'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)

class ApproveCommentView(AdminRequiredMixin, View):
    def post(self, request, pk):
        from django.http import JsonResponse
        from .models import Comment
        
        try:
            comment = get_object_or_404(Comment, pk=pk)
            comment.status = 'approved'
            comment.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Comment approved successfully'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)

class RejectCommentView(AdminRequiredMixin, View):
    def post(self, request, pk):
        from django.http import JsonResponse
        from .models import Comment
        
        try:
            comment = get_object_or_404(Comment, pk=pk)
            comment.status = 'rejected'
            comment.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Comment rejected successfully'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)
