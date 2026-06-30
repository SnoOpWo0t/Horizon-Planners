from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import TemplateView, View, ListView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Avg, Count, Q
from django.utils import timezone
from django.core.paginator import Paginator

from .models import Review, ReviewVote, Comment, CommentLike
from apps.events.models import Event
from apps.venues.models import Venue, VenueBookingRequest
from apps.payments.models import Order
from apps.core.models import Notification


class AdminRequiredMixin(UserPassesTestMixin):
    """Mixin to require admin role"""
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_admin_user


# ─────────────────────────────────────────────
# COMMENT VIEWS
# ─────────────────────────────────────────────

class CreateCommentView(LoginRequiredMixin, View):
    """Create a comment on an event"""

    def post(self, request, event_id):
        event = get_object_or_404(Event, pk=event_id, status='published')
        content = request.POST.get('content', '').strip()

        if not content:
            messages.error(request, 'Comment cannot be empty.')
            return redirect('events:event_detail', pk=event.pk)

        comment = Comment.objects.create(
            user=request.user,
            event=event,
            content=content,
            status=Comment.Status.APPROVED,
        )

        # Send notification to the event manager
        if event.manager != request.user:
            Notification.objects.create(
                recipient=event.manager,
                admin_user=None,
                notification_type=Notification.NotificationType.NEW_COMMENT,
                subject=f'New comment on "{event.title}"',
                message=f'{request.user.get_full_name() or request.user.username} commented: "{content[:100]}..."',
                event=event,
                comment=comment,
                details={
                    'event_title': event.title,
                    'event_id': event.id,
                    'commenter': request.user.username,
                    'comment_preview': content[:200],
                }
            )

        messages.success(request, 'Your comment has been posted!')
        return redirect('events:event_detail', pk=event.pk)


class ReplyToCommentView(LoginRequiredMixin, View):
    """Reply to an existing comment"""

    def post(self, request, pk):
        parent_comment = get_object_or_404(Comment, pk=pk, status='approved')
        content = request.POST.get('content', '').strip()

        if not content:
            messages.error(request, 'Reply cannot be empty.')
            return redirect('reviews:event_comments', event_id=parent_comment.event.pk)

        reply = Comment.objects.create(
            user=request.user,
            event=parent_comment.event,
            parent=parent_comment,
            content=content,
            status=Comment.Status.APPROVED,
        )

        # Notify the parent comment author
        if parent_comment.user != request.user:
            Notification.objects.create(
                recipient=parent_comment.user,
                notification_type=Notification.NotificationType.COMMENT_REPLY,
                subject=f'New reply to your comment on "{parent_comment.event.title}"',
                message=f'{request.user.get_full_name() or request.user.username} replied: "{content[:100]}..."',
                event=parent_comment.event,
                comment=reply,
                details={
                    'event_title': parent_comment.event.title,
                    'event_id': parent_comment.event.id,
                    'replier': request.user.username,
                    'reply_preview': content[:200],
                }
            )

        # Also notify event manager if reply is from someone else
        event = parent_comment.event
        if event.manager != request.user and event.manager != parent_comment.user:
            Notification.objects.create(
                recipient=event.manager,
                notification_type=Notification.NotificationType.NEW_COMMENT,
                subject=f'New reply on "{event.title}"',
                message=f'{request.user.get_full_name() or request.user.username} replied to a comment: "{content[:100]}..."',
                event=event,
                comment=reply,
                details={
                    'event_title': event.title,
                    'event_id': event.id,
                    'replier': request.user.username,
                }
            )

        messages.success(request, 'Your reply has been posted!')
        return redirect('reviews:event_comments', event_id=parent_comment.event.pk)


class LikeCommentView(LoginRequiredMixin, View):
    """Toggle like on a comment"""

    def post(self, request, pk):
        comment = get_object_or_404(Comment, pk=pk, status='approved')

        like, created = CommentLike.objects.get_or_create(
            comment=comment,
            user=request.user,
        )

        if not created:
            # Unlike — remove the like
            like.delete()
            comment.likes = max(0, comment.likes - 1)
            comment.save(update_fields=['likes'])
            liked = False
        else:
            comment.likes += 1
            comment.save(update_fields=['likes'])
            liked = True

        # Return JSON for AJAX or redirect for regular form submit
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'liked': liked,
                'likes_count': comment.likes,
            })

        return redirect(request.META.get('HTTP_REFERER', 'events:home'))


class EditCommentView(LoginRequiredMixin, View):
    """Edit own comment"""

    def post(self, request, pk):
        comment = get_object_or_404(Comment, pk=pk, user=request.user)
        content = request.POST.get('content', '').strip()

        if not content:
            messages.error(request, 'Comment cannot be empty.')
        else:
            comment.content = content
            comment.save(update_fields=['content', 'updated_at'])
            messages.success(request, 'Comment updated successfully!')

        return redirect('reviews:event_comments', event_id=comment.event.pk)


class DeleteCommentView(LoginRequiredMixin, View):
    """Delete own comment (or admin can delete any)"""

    def post(self, request, pk):
        comment = get_object_or_404(Comment, pk=pk)

        if comment.user != request.user and not request.user.is_admin_user:
            messages.error(request, 'You can only delete your own comments.')
            return redirect('reviews:event_comments', event_id=comment.event.pk)

        event_id = comment.event.pk
        comment.delete()
        messages.success(request, 'Comment deleted successfully.')
        return redirect('reviews:event_comments', event_id=event_id)


class EventCommentsPageView(View):
    """Full-page threaded comments view for an event"""

    def get(self, request, event_id):
        event = get_object_or_404(Event, pk=event_id, status='published')

        # Get top-level comments (no parent) with their replies
        comments = Comment.objects.filter(
            event=event,
            status='approved',
            parent__isnull=True,
        ).select_related('user').prefetch_related(
            'replies__user', 'comment_likes'
        ).order_by('-is_pinned', '-created_at')

        # Track which comments the user has liked
        user_liked_ids = set()
        if request.user.is_authenticated:
            user_liked_ids = set(
                CommentLike.objects.filter(
                    user=request.user,
                    comment__event=event,
                ).values_list('comment_id', flat=True)
            )

        paginator = Paginator(comments, 15)
        page_number = request.GET.get('page', 1)
        comments_page = paginator.get_page(page_number)

        context = {
            'event': event,
            'comments': comments_page,
            'user_liked_ids': user_liked_ids,
            'total_comments': Comment.objects.filter(event=event, status='approved').count(),
        }
        return render(request, 'reviews/event_comments.html', context)


# ─────────────────────────────────────────────
# REVIEW VIEWS
# ─────────────────────────────────────────────

class CreateEventReviewView(LoginRequiredMixin, View):
    """Create a review for an event (post-purchase only)"""

    def get(self, request, event_id):
        event = get_object_or_404(Event, pk=event_id)

        # Check eligibility: must have a completed order
        has_completed_order = Order.objects.filter(
            user=request.user,
            event=event,
            payment__status='completed',
        ).exists()

        already_reviewed = Review.objects.filter(
            user=request.user,
            event=event,
        ).exists()

        context = {
            'event': event,
            'has_completed_order': has_completed_order,
            'already_reviewed': already_reviewed,
        }
        return render(request, 'reviews/create_event_review.html', context)

    def post(self, request, event_id):
        event = get_object_or_404(Event, pk=event_id)

        # Check eligibility
        has_completed_order = Order.objects.filter(
            user=request.user,
            event=event,
            payment__status='completed',
        ).exists()

        if not has_completed_order:
            messages.error(request, 'You can only review events you have attended.')
            return redirect('events:event_detail', pk=event.pk)

        already_reviewed = Review.objects.filter(
            user=request.user,
            event=event,
        ).exists()

        if already_reviewed:
            messages.error(request, 'You have already reviewed this event.')
            return redirect('events:event_detail', pk=event.pk)

        try:
            rating = int(request.POST.get('rating', 0))
            if rating < 1 or rating > 5:
                raise ValueError('Invalid rating')
        except (ValueError, TypeError):
            messages.error(request, 'Please select a valid rating (1-5 stars).')
            return redirect('reviews:create_event_review', event_id=event.pk)

        title = request.POST.get('title', '').strip()
        content = request.POST.get('content', '').strip()

        if not title or not content:
            messages.error(request, 'Please fill in both the title and review content.')
            return redirect('reviews:create_event_review', event_id=event.pk)

        review = Review.objects.create(
            user=request.user,
            event=event,
            rating=rating,
            title=title,
            content=content,
            status=Review.Status.APPROVED,
        )

        # Notify event manager
        if event.manager != request.user:
            Notification.objects.create(
                recipient=event.manager,
                notification_type=Notification.NotificationType.NEW_REVIEW,
                subject=f'New {rating}★ review on "{event.title}"',
                message=f'{request.user.get_full_name() or request.user.username} left a review: "{title}"',
                event=event,
                details={
                    'event_title': event.title,
                    'event_id': event.id,
                    'reviewer': request.user.username,
                    'rating': rating,
                }
            )

        messages.success(request, 'Your review has been posted! Thank you for your feedback.')
        return redirect('events:event_detail', pk=event.pk)


class CreateVenueReviewView(LoginRequiredMixin, View):
    """Create a review for a venue"""

    def get(self, request, venue_id):
        venue = get_object_or_404(Venue, pk=venue_id)

        # Check eligibility: must have booked the venue (approved booking request)
        has_booked = VenueBookingRequest.objects.filter(
            requester=request.user,
            venue=venue,
            status__in=['approved', 'completed'],
        ).exists()

        # Also allow Horizon Planners who have events at this venue
        has_event_at_venue = Event.objects.filter(
            manager=request.user,
            venue=venue,
        ).exists()

        can_review = has_booked or has_event_at_venue

        already_reviewed = Review.objects.filter(
            user=request.user,
            venue=venue,
        ).exists()

        context = {
            'venue': venue,
            'can_review': can_review,
            'already_reviewed': already_reviewed,
        }
        return render(request, 'reviews/create_venue_review.html', context)

    def post(self, request, venue_id):
        venue = get_object_or_404(Venue, pk=venue_id)

        # Check eligibility
        has_booked = VenueBookingRequest.objects.filter(
            requester=request.user,
            venue=venue,
            status__in=['approved', 'completed'],
        ).exists()

        has_event_at_venue = Event.objects.filter(
            manager=request.user,
            venue=venue,
        ).exists()

        can_review = has_booked or has_event_at_venue

        if not can_review:
            messages.error(request, 'You can only review venues you have booked or used.')
            return redirect('venues:venue_detail', slug=venue.slug)

        already_reviewed = Review.objects.filter(
            user=request.user,
            venue=venue,
        ).exists()

        if already_reviewed:
            messages.error(request, 'You have already reviewed this venue.')
            return redirect('venues:venue_detail', slug=venue.slug)

        try:
            rating = int(request.POST.get('rating', 0))
            if rating < 1 or rating > 5:
                raise ValueError('Invalid rating')
        except (ValueError, TypeError):
            messages.error(request, 'Please select a valid rating (1-5 stars).')
            return redirect('reviews:create_venue_review', venue_id=venue.pk)

        title = request.POST.get('title', '').strip()
        content = request.POST.get('content', '').strip()

        if not title or not content:
            messages.error(request, 'Please fill in both the title and review content.')
            return redirect('reviews:create_venue_review', venue_id=venue.pk)

        review = Review.objects.create(
            user=request.user,
            venue=venue,
            rating=rating,
            title=title,
            content=content,
            status=Review.Status.APPROVED,
        )

        # Notify venue manager
        if venue.manager != request.user:
            Notification.objects.create(
                recipient=venue.manager,
                notification_type=Notification.NotificationType.NEW_REVIEW,
                subject=f'New {rating}★ review on "{venue.name}"',
                message=f'{request.user.get_full_name() or request.user.username} left a review: "{title}"',
                venue=venue,
                details={
                    'venue_name': venue.name,
                    'venue_id': venue.id,
                    'reviewer': request.user.username,
                    'rating': rating,
                }
            )

        messages.success(request, 'Your review has been posted! Thank you for your feedback.')
        return redirect('venues:venue_detail', slug=venue.slug)


class EditReviewView(LoginRequiredMixin, View):
    """Edit own review"""

    def get(self, request, pk):
        review = get_object_or_404(Review, pk=pk, user=request.user)
        context = {
            'review': review,
            'event': review.event,
            'venue': review.venue,
        }
        template = 'reviews/create_event_review.html' if review.event else 'reviews/create_venue_review.html'
        return render(request, template, context)

    def post(self, request, pk):
        review = get_object_or_404(Review, pk=pk, user=request.user)

        try:
            rating = int(request.POST.get('rating', 0))
            if rating < 1 or rating > 5:
                raise ValueError('Invalid rating')
        except (ValueError, TypeError):
            messages.error(request, 'Please select a valid rating (1-5 stars).')
            return redirect('reviews:edit_review', pk=pk)

        title = request.POST.get('title', '').strip()
        content = request.POST.get('content', '').strip()

        if not title or not content:
            messages.error(request, 'Please fill in both the title and review content.')
            return redirect('reviews:edit_review', pk=pk)

        review.rating = rating
        review.title = title
        review.content = content
        review.save(update_fields=['rating', 'title', 'content', 'updated_at'])

        messages.success(request, 'Your review has been updated!')

        if review.event:
            return redirect('events:event_detail', pk=review.event.pk)
        elif review.venue:
            return redirect('venues:venue_detail', slug=review.venue.slug)
        return redirect('events:home')


class DeleteReviewView(LoginRequiredMixin, View):
    """Delete own review"""

    def post(self, request, pk):
        review = get_object_or_404(Review, pk=pk)

        if review.user != request.user and not request.user.is_admin_user:
            messages.error(request, 'You can only delete your own reviews.')
            return redirect('events:home')

        event = review.event
        venue = review.venue
        review.delete()
        messages.success(request, 'Review deleted successfully.')

        if event:
            return redirect('events:event_detail', pk=event.pk)
        elif venue:
            return redirect('venues:venue_detail', slug=venue.slug)
        return redirect('events:home')


class VoteReviewView(LoginRequiredMixin, View):
    """Vote a review as helpful or not helpful"""

    def post(self, request, pk):
        review = get_object_or_404(Review, pk=pk, status='approved')
        is_helpful = request.POST.get('is_helpful', 'true').lower() == 'true'

        vote, created = ReviewVote.objects.get_or_create(
            review=review,
            user=request.user,
            defaults={'is_helpful': is_helpful},
        )

        if not created:
            if vote.is_helpful == is_helpful:
                # Remove vote
                vote.delete()
                review.total_votes = max(0, review.total_votes - 1)
                if is_helpful:
                    review.helpful_votes = max(0, review.helpful_votes - 1)
                review.save(update_fields=['total_votes', 'helpful_votes'])
            else:
                # Change vote
                old_helpful = vote.is_helpful
                vote.is_helpful = is_helpful
                vote.save(update_fields=['is_helpful'])
                if is_helpful:
                    review.helpful_votes += 1
                else:
                    review.helpful_votes = max(0, review.helpful_votes - 1)
                review.save(update_fields=['helpful_votes'])
        else:
            review.total_votes += 1
            if is_helpful:
                review.helpful_votes += 1
            review.save(update_fields=['total_votes', 'helpful_votes'])

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'helpful_votes': review.helpful_votes,
                'total_votes': review.total_votes,
            })

        return redirect(request.META.get('HTTP_REFERER', 'events:home'))


# ─────────────────────────────────────────────
# ALL-REVIEWS PAGES
# ─────────────────────────────────────────────

class EventAllReviewsView(View):
    """View all reviews for a specific event"""

    def get(self, request, event_id):
        event = get_object_or_404(Event, pk=event_id)

        reviews = Review.objects.filter(
            event=event,
            status='approved',
        ).select_related('user').order_by('-created_at')

        # Stats
        stats = reviews.aggregate(
            avg_rating=Avg('rating'),
            total_count=Count('id'),
        )

        # Rating breakdown
        rating_breakdown = {}
        for i in range(1, 6):
            count = reviews.filter(rating=i).count()
            total = stats['total_count'] or 1
            rating_breakdown[i] = {
                'count': count,
                'percentage': round((count / total) * 100) if total > 0 else 0,
            }

        # Check if current user can review
        can_review = False
        has_reviewed = False
        if request.user.is_authenticated:
            can_review = Order.objects.filter(
                user=request.user,
                event=event,
                payment__status='completed',
            ).exists()
            has_reviewed = Review.objects.filter(
                user=request.user,
                event=event,
            ).exists()

        paginator = Paginator(reviews, 10)
        page_number = request.GET.get('page', 1)
        reviews_page = paginator.get_page(page_number)

        # Track user's votes
        user_votes = {}
        if request.user.is_authenticated:
            votes = ReviewVote.objects.filter(
                user=request.user,
                review__event=event,
            )
            for vote in votes:
                user_votes[vote.review_id] = vote.is_helpful

        context = {
            'event': event,
            'reviews': reviews_page,
            'avg_rating': stats['avg_rating'] or 0,
            'total_reviews': stats['total_count'] or 0,
            'rating_breakdown': rating_breakdown,
            'can_review': can_review,
            'has_reviewed': has_reviewed,
            'user_votes': user_votes,
        }
        return render(request, 'reviews/event_reviews.html', context)


class VenueAllReviewsView(View):
    """View all reviews for a specific venue"""

    def get(self, request, venue_id):
        venue = get_object_or_404(Venue, pk=venue_id)

        reviews = Review.objects.filter(
            venue=venue,
            status='approved',
        ).select_related('user').order_by('-created_at')

        # Stats
        stats = reviews.aggregate(
            avg_rating=Avg('rating'),
            total_count=Count('id'),
        )

        # Rating breakdown
        rating_breakdown = {}
        for i in range(1, 6):
            count = reviews.filter(rating=i).count()
            total = stats['total_count'] or 1
            rating_breakdown[i] = {
                'count': count,
                'percentage': round((count / total) * 100) if total > 0 else 0,
            }

        # Check if current user can review
        can_review = False
        has_reviewed = False
        if request.user.is_authenticated:
            has_booked = VenueBookingRequest.objects.filter(
                requester=request.user,
                venue=venue,
                status__in=['approved', 'completed'],
            ).exists()
            has_event_at_venue = Event.objects.filter(
                manager=request.user,
                venue=venue,
            ).exists()
            can_review = has_booked or has_event_at_venue
            has_reviewed = Review.objects.filter(
                user=request.user,
                venue=venue,
            ).exists()

        paginator = Paginator(reviews, 10)
        page_number = request.GET.get('page', 1)
        reviews_page = paginator.get_page(page_number)

        # Track user's votes
        user_votes = {}
        if request.user.is_authenticated:
            votes = ReviewVote.objects.filter(
                user=request.user,
                review__venue=venue,
            )
            for vote in votes:
                user_votes[vote.review_id] = vote.is_helpful

        context = {
            'venue': venue,
            'reviews': reviews_page,
            'avg_rating': stats['avg_rating'] or 0,
            'total_reviews': stats['total_count'] or 0,
            'rating_breakdown': rating_breakdown,
            'can_review': can_review,
            'has_reviewed': has_reviewed,
            'user_votes': user_votes,
        }
        return render(request, 'reviews/venue_reviews.html', context)


# ─────────────────────────────────────────────
# MODERATION VIEWS (kept from original)
# ─────────────────────────────────────────────

class ModerationDashboardView(AdminRequiredMixin, TemplateView):
    template_name = 'reviews/moderation_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

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
