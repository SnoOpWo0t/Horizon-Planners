from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.events.models import Category
from apps.venues.models import Venue

User = get_user_model()


class Command(BaseCommand):
    help = 'Create sample data for EventEase'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Creating sample data...'))

        # Create categories
        categories_data = [
            {'name': 'Music', 'description': 'Concerts, festivals, and musical performances', 'color': '#FF6B6B', 'icon': 'fas fa-music'},
            {'name': 'Sports', 'description': 'Sporting events and competitions', 'color': '#4ECDC4', 'icon': 'fas fa-football-ball'},
            {'name': 'Technology', 'description': 'Tech conferences, workshops, and meetups', 'color': '#45B7D1', 'icon': 'fas fa-laptop-code'},
            {'name': 'Art & Culture', 'description': 'Art exhibitions, cultural events, and performances', 'color': '#96CEB4', 'icon': 'fas fa-palette'},
            {'name': 'Food & Drink', 'description': 'Food festivals, wine tastings, and culinary events', 'color': '#FECA57', 'icon': 'fas fa-utensils'},
            {'name': 'Business', 'description': 'Networking events, seminars, and corporate gatherings', 'color': '#6C5CE7', 'icon': 'fas fa-briefcase'},
            {'name': 'Education', 'description': 'Workshops, classes, and educational seminars', 'color': '#FD79A8', 'icon': 'fas fa-graduation-cap'},
            {'name': 'Community', 'description': 'Local community events and gatherings', 'color': '#FDCB6E', 'icon': 'fas fa-users'},
        ]

        for cat_data in categories_data:
            category, created = Category.objects.get_or_create(
                name=cat_data['name'],
                defaults={
                    'description': cat_data['description'],
                    'color': cat_data['color'],
                    'icon': cat_data['icon']
                }
            )
            if created:
                self.stdout.write(f'Created category: {category.name}')
            else:
                self.stdout.write(f'Category already exists: {category.name}')

        # Create sample users with different roles
        users_data = [
            {
                'username': 'event_manager1',
                'email': 'eventmanager@example.com',
                'first_name': 'John',
                'last_name': 'Smith',
                'role': 'horizon_planner',
                'password': 'password123'
            },
            {
                'username': 'venue_manager1',
                'email': 'venuemanager@example.com',
                'first_name': 'Sarah',
                'last_name': 'Johnson',
                'role': 'venue_manager',
                'password': 'password123'
            },
            {
                'username': 'basic_user1',
                'email': 'user@example.com',
                'first_name': 'Mike',
                'last_name': 'Wilson',
                'role': 'basic',
                'password': 'password123'
            }
        ]

        for user_data in users_data:
            user, created = User.objects.get_or_create(
                username=user_data['username'],
                defaults={
                    'email': user_data['email'],
                    'first_name': user_data['first_name'],
                    'last_name': user_data['last_name'],
                    'role': user_data['role']
                }
            )
            if created:
                user.set_password(user_data['password'])
                user.save()
                self.stdout.write(f'Created user: {user.username} with role {user.role}')
            else:
                self.stdout.write(f'User already exists: {user.username}')

        # Create sample venues
        venue_manager = User.objects.filter(role='venue_manager').first()
        if venue_manager:
            venues_data = [
                {
                    'name': 'Grand Convention Center',
                    'description': 'A premier venue for large events and conferences with state-of-the-art facilities.',
                    'address': '123 Main Street',
                    'city': 'New York',
                    'state': 'NY',
                    'postal_code': '10001',
                    'capacity': 500,
                    'hourly_rate': 150.00,
                    'daily_rate': 1000.00,
                    'contact_person': 'Sarah Johnson',
                    'contact_phone': '(555) 123-4567',
                    'contact_email': 'venuemanager@example.com',
                    'has_parking': True,
                    'has_wifi': True,
                    'has_catering': True,
                    'has_av_equipment': True,
                    'has_accessibility': True,
                },
                {
                    'name': 'Downtown Music Hall',
                    'description': 'Historic music venue perfect for concerts and live performances.',
                    'address': '456 Broadway',
                    'city': 'New York',
                    'state': 'NY',
                    'postal_code': '10002',
                    'capacity': 300,
                    'hourly_rate': 100.00,
                    'daily_rate': 750.00,
                    'contact_person': 'Sarah Johnson',
                    'contact_phone': '(555) 123-4567',
                    'contact_email': 'venuemanager@example.com',
                    'has_parking': False,
                    'has_wifi': True,
                    'has_catering': False,
                    'has_av_equipment': True,
                    'has_accessibility': True,
                },
                {
                    'name': 'Rooftop Garden Venue',
                    'description': 'Beautiful outdoor venue with stunning city views, perfect for upscale events.',
                    'address': '789 Sky Tower',
                    'city': 'New York',
                    'state': 'NY',
                    'postal_code': '10003',
                    'capacity': 150,
                    'hourly_rate': 200.00,
                    'daily_rate': 1200.00,
                    'contact_person': 'Sarah Johnson',
                    'contact_phone': '(555) 123-4567',
                    'contact_email': 'venuemanager@example.com',
                    'has_parking': True,
                    'has_wifi': True,
                    'has_catering': True,
                    'has_av_equipment': False,
                    'has_accessibility': False,
                }
            ]

            for venue_data in venues_data:
                venue, created = Venue.objects.get_or_create(
                    name=venue_data['name'],
                    defaults={**venue_data, 'manager': venue_manager}
                )
                if created:
                    self.stdout.write(f'Created venue: {venue.name}')
                else:
                    self.stdout.write(f'Venue already exists: {venue.name}')

        self.stdout.write(
            self.style.SUCCESS('Successfully created sample data!')
        )
        
        self.stdout.write(
            self.style.WARNING('\nSample user credentials:')
        )
        self.stdout.write('Horizon Planner: event_manager1 / password123')
        self.stdout.write('Venue Manager: venue_manager1 / password123')
        self.stdout.write('Basic User: basic_user1 / password123')
        self.stdout.write(f'Admin User: akhi / 1')  # The superuser we created
