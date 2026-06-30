from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.core.models import TimeStampedModel


class Review(TimeStampedModel):
    """Event and venue reviews"""
    
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending Moderation'
        APPROVED = 'approved', 'Approved'
        REJECTED = 'rejected', 'Rejected'
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reviews')
    
    # Polymorphic review - can be for event or venue
    event = models.ForeignKey('events.Event', on_delete=models.CASCADE, null=True, blank=True, related_name='reviews')
    venue = models.ForeignKey('venues.Venue', on_delete=models.CASCADE, null=True, blank=True, related_name='reviews')
    
    # Review content
    rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text='Rating from 1 to 5 stars'
    )
    title = models.CharField(max_length=200)
    content = models.TextField()
    
    # Moderation
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    moderated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='moderated_reviews'
    )
    moderation_notes = models.TextField(blank=True)
    moderated_at = models.DateTimeField(null=True, blank=True)
    
    # Helpfulness tracking
    helpful_votes = models.PositiveIntegerField(default=0)
    total_votes = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.CheckConstraint(
                check=models.Q(event__isnull=False) | models.Q(venue__isnull=False),
                name='review_must_have_event_or_venue'
            ),
            models.CheckConstraint(
                check=~(models.Q(event__isnull=False) & models.Q(venue__isnull=False)),
                name='review_cannot_have_both_event_and_venue'
            )
        ]
        # Ensure one review per user per event/venue
        unique_together = [
            ['user', 'event'],
            ['user', 'venue']
        ]
    
    def __str__(self):
        target = self.event or self.venue
        return f"{self.user.username}'s review of {target} - {self.rating}★"
    
    @property
    def helpfulness_percentage(self):
        if self.total_votes == 0:
            return 0
        return (self.helpful_votes / self.total_votes) * 100


class ReviewVote(models.Model):
    """Track helpfulness votes on reviews"""
    
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name='votes')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='review_votes')
    is_helpful = models.BooleanField(help_text='True if helpful, False if not helpful')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['review', 'user']
    
    def __str__(self):
        return f"{self.user.username} - {'Helpful' if self.is_helpful else 'Not Helpful'}"


class Comment(TimeStampedModel):
    """Comments on events for discussion"""
    
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending Moderation'
        APPROVED = 'approved', 'Approved'
        REJECTED = 'rejected', 'Rejected'
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='comments')
    event = models.ForeignKey('events.Event', on_delete=models.CASCADE, related_name='comments')
    
    # Comment threading support
    parent = models.ForeignKey(
        'self', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='replies'
    )
    
    # Comment content
    content = models.TextField()
    
    # Moderation
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.APPROVED)
    moderated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='moderated_comments'
    )
    moderation_notes = models.TextField(blank=True)
    moderated_at = models.DateTimeField(null=True, blank=True)
    
    # Engagement tracking
    likes = models.PositiveIntegerField(default=0)
    is_pinned = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-is_pinned', '-created_at']
    
    def __str__(self):
        return f"Comment by {self.user.username} on {self.event.title}"
    
    @property
    def is_reply(self):
        return self.parent is not None


class CommentLike(models.Model):
    """Track likes on comments"""
    
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name='comment_likes')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='liked_comments')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['comment', 'user']
    
    def __str__(self):
        return f"{self.user.username} likes comment on {self.comment.event.title}"
