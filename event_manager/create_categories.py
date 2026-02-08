#!/usr/bin/env python
"""
Script to create default categories for the Horizon Planner
"""
import os
import sys
import django

# Add the project path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'horizon_planner.settings')
django.setup()

from apps.events.models import Category

def create_default_categories():
    """Create default event categories"""
    
    categories_data = [
        {
            'name': 'Music',
            'description': 'Concerts, festivals, and musical performances',
            'color': '#ff6b6b',
            'icon': 'fas fa-music'
        },
        {
            'name': 'Sports',
            'description': 'Sporting events and competitions',
            'color': '#4ecdc4',
            'icon': 'fas fa-football-ball'
        },
        {
            'name': 'Business',
            'description': 'Conferences, workshops, and networking events',
            'color': '#45b7d1',
            'icon': 'fas fa-briefcase'
        },
        {
            'name': 'Entertainment',
            'description': 'Shows, comedy, and entertainment events',
            'color': '#f9ca24',
            'icon': 'fas fa-theater-masks'
        },
        {
            'name': 'Education',
            'description': 'Workshops, seminars, and educational events',
            'color': '#6c5ce7',
            'icon': 'fas fa-graduation-cap'
        },
        {
            'name': 'Food & Drink',
            'description': 'Food festivals, tastings, and culinary events',
            'color': '#fd79a8',
            'icon': 'fas fa-utensils'
        },
        {
            'name': 'Art & Culture',
            'description': 'Art exhibitions, cultural events, and galleries',
            'color': '#00b894',
            'icon': 'fas fa-palette'
        },
        {
            'name': 'Technology',
            'description': 'Tech conferences, hackathons, and innovation events',
            'color': '#0984e3',
            'icon': 'fas fa-laptop'
        },
    ]
    
    created_count = 0
    existing_count = 0
    
    for cat_data in categories_data:
        category, created = Category.objects.get_or_create(
            name=cat_data['name'],
            defaults=cat_data
        )
        
        if created:
            print(f'✓ Created category: {category.name}')
            created_count += 1
        else:
            print(f'○ Category already exists: {category.name}')
            existing_count += 1
    
    total_categories = Category.objects.count()
    print(f'\n--- Summary ---')
    print(f'Categories created: {created_count}')
    print(f'Categories already existed: {existing_count}')
    print(f'Total categories in database: {total_categories}')
    
    return total_categories

if __name__ == '__main__':
    print('Creating default categories for Horizon Planner...\n')
    create_default_categories()
