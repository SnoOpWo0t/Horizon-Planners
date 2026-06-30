# Horizon Planners - Project Context

This file serves as a context guide for AI agents and developers working on the Horizon Planners project. It documents the recent architectural decisions, bug fixes, and feature additions to provide an understanding of the current state of the application.

## 🛠 Tech Stack
- **Backend**: Django 5.2.6, Django REST Framework
- **Database**: SQLite (Local), PostgreSQL (Production/Vercel)
- **Frontend**: Django Templates with Bootstrap components
- **Deployment**: Vercel (`@vercel/python` builder)

## ✨ Core Features & Recent Updates

### 1. Venue Management System
- **Venue Model**: Venues utilize an auto-generated `slug` field for URL routing.
- **Venue Form**: Complete validation including required fields (`city`, `state`, `postal_code`, `contact_person`, `country`) and boolean amenity fields (`has_parking`, `has_wifi`, etc.).
- **Venue Listing**: Advanced filtering by city, capacity, and comprehensive search capabilities.
- **Permissions**: Admin users can manage all venues, while Venue Managers can only edit and manage venues they own. Regular users view active venues for booking.

### 2. Category Management
- **Event Categories**: Dynamic category management system allowing Create, Read, Update, and Delete (CRUD) operations.
- **Inline Creation**: Planners can create new categories on-the-fly directly from the event creation form.

### 3. Analytics & Admin Dashboard
- **Analytics Exports**: URL routing for data exports strictly match template references (`export_event_data`, `export_user_data`, `export_revenue_data`).
- **Dashboard Optimization**: The recent activity feed uses a fixed-height container with a 10-item limit and pagination to prevent infinite scrolling performance issues.

### 4. Vercel Deployment Structure
- The project was recently migrated from a nested `event_manager` subdirectory to the **root** of the repository.
- `vercel.json` points to `horizon_planner/wsgi.py`.
- Ensure Vercel project settings have an empty/root **Root Directory** and use `bash build.sh` for build commands to execute `collectstatic` and `migrate`.

## 🐛 Known Patterns & Fixed Issues
- **Slugs Over PKs**: URLs for Venues and specific management tasks were refactored to use `slugs` rather than Primary Keys for SEO and consistency.
- **Template Safety**: Admin templates incorporate safety checks for missing data fields to prevent rendering exceptions.

## 🚀 Future Roadmap / Next Steps
- Implement comprehensive venue booking system with availability calendar integration.
- Add venue images support and multi-image galleries.
- Enhance event creation with deeper category integrations.
