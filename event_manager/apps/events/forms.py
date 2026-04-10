from django import forms
from django.contrib.auth import get_user_model
from .models import Event, Category, Ticket, TicketPricing
from apps.venues.models import Venue

User = get_user_model()


class EventForm(forms.ModelForm):
    """Form for creating and editing events"""
    
    class Meta:
        model = Event
        fields = [
            'title', 'description', 'category', 'venue', 'start_date', 'end_date',
            'registration_deadline', 'max_capacity', 'min_capacity', 'requires_approval',
            'is_free', 'base_price', 'poster_image', 'age_restriction',
            'special_instructions', 'is_active', 'is_featured'
        ]
        widgets = {
            'start_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'registration_deadline': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'description': forms.Textarea(attrs={'rows': 4}),
            'special_instructions': forms.Textarea(attrs={'rows': 3}),
            'poster_image': forms.FileInput(attrs={'accept': 'image/*'}),
            'is_featured': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_free': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'requires_approval': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Only show active venues
        self.fields['venue'].queryset = Venue.objects.filter(is_active=True)
        
        # If user is not admin, limit venue choices to ones they can book
        if user and not user.is_admin_user:
            # For now, allow all venues - booking approval happens later
            pass
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        max_capacity = cleaned_data.get('max_capacity')
        min_capacity = cleaned_data.get('min_capacity')
        is_free = cleaned_data.get('is_free')
        base_price = cleaned_data.get('base_price')

        if start_date and end_date and start_date >= end_date:
            raise forms.ValidationError('End time must be after start time.')

        if max_capacity and min_capacity and min_capacity > max_capacity:
            raise forms.ValidationError('Minimum capacity cannot exceed maximum capacity.')

        if is_free:
            cleaned_data['base_price'] = 0
        elif base_price is not None and base_price < 0:
            raise forms.ValidationError('Base price cannot be negative.')

        # Keep canonical fields populated for code paths still using older field names.
        if start_date:
            cleaned_data['event_date'] = start_date.date()
            cleaned_data['start_time'] = start_date.time().replace(second=0, microsecond=0)
        if end_date:
            cleaned_data['end_time'] = end_date.time().replace(second=0, microsecond=0)
        if max_capacity:
            cleaned_data['total_seats'] = max_capacity
        
        return cleaned_data

    def save(self, commit=True):
        event = super().save(commit=False)
        if event.start_date:
            event.event_date = event.start_date.date()
            event.start_time = event.start_date.time().replace(second=0, microsecond=0)
        if event.end_date:
            event.end_time = event.end_date.time().replace(second=0, microsecond=0)
        if event.max_capacity:
            event.total_seats = event.max_capacity
        if event.is_free:
            event.base_price = 0

        if commit:
            event.save()
        return event


class BookTicketForm(forms.ModelForm):
    """Form for booking tickets"""
    
    class Meta:
        model = Ticket
        fields = ['ticket_type', 'quantity']
        widgets = {
            'quantity': forms.NumberInput(attrs={'min': 1, 'max': 10}),
        }
    
    def __init__(self, *args, **kwargs):
        event = kwargs.pop('event', None)
        super().__init__(*args, **kwargs)
        
        if event:
            # Limit quantity based on available seats
            max_quantity = min(10, event.available_seats)
            self.fields['quantity'].widget.attrs['max'] = max_quantity
            
            # Add help text showing available seats
            self.fields['quantity'].help_text = f'{event.available_seats} seats available'
    
    def clean_quantity(self):
        quantity = self.cleaned_data['quantity']
        if quantity < 1:
            raise forms.ValidationError('Quantity must be at least 1.')
        if quantity > 10:
            raise forms.ValidationError('Maximum 10 tickets per booking.')
        return quantity


class EventSearchForm(forms.Form):
    """Form for searching events"""
    search = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Search events...',
            'class': 'form-control'
        })
    )
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        required=False,
        empty_label='All Categories',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    venue = forms.ModelChoiceField(
        queryset=Venue.objects.filter(is_active=True),
        required=False,
        empty_label='All Venues',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        })
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        })
    )


class TicketPricingForm(forms.ModelForm):
    """Form for managing ticket pricing tiers"""
    
    class Meta:
        model = TicketPricing
        fields = [
            'ticket_type', 'name', 'price', 'available_quantity',
            'valid_from', 'valid_until', 'is_active'
        ]
        widgets = {
            'valid_from': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'valid_until': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        valid_from = cleaned_data.get('valid_from')
        valid_until = cleaned_data.get('valid_until')
        
        if valid_from and valid_until and valid_from >= valid_until:
            raise forms.ValidationError('Valid until must be after valid from.')
        
        return cleaned_data
