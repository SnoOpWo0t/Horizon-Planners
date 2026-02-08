# Horizon Planner Project Documentation

---

## 1. User Roles and Their Capabilities

Horizon Planner has four main user roles, each with distinct functionalities:

### 1.1 Basic User / Buyer

- **Sign Up / Login:** Users can register using email and password. Login is separate and leads to their homepage.
- **View Events:** Browse upcoming events in a grid/list with filters by category, venue, and search query.
- **Browse Venues:** Check available venues with filters for location, capacity, and amenities.
- **Book Tickets:** Select an event, choose available seats, proceed to payment, and receive a downloadable ticket (PDF/QR/text-based).
- **Payment Gateway:** Simulated secure payment for booking tickets.
- **Download Ticket:** Tickets can be downloaded after booking.
- **Rate / Review Event:** Submit ratings and text reviews for attended events.
- **Event Comments:** Participate in discussion sections for each event.
- **Request Role Upgrade:** Apply to become a Horizon Planner or Venue Manager.

### 1.2 Horizon Planner

- **Create Event:** Add new events with title, description, date, venue, price, and category.
- **Manage Event:** Update event details, seat availability, and media.
- **Book Venue:** Choose and reserve a venue for events.
- **Check Venue Availability:** View available dates for venues.
- **Manage Tickets:** Set ticket inventory, pricing tiers, and categories.
- **View Sales Dashboard:** Analytics for ticket sales, revenue, and attendance.

### 1.3 Venue Manager

- **Manage Venues:** Add, edit, or delete venue listings with details, images, and amenities.
- **Set Venue Availability:** Define dates and times for venue bookings.
- **Upload Venue Media:** Add images, videos, and virtual tours.
- **Monitor Bookings & Analytics:** Track bookings, revenue, and visitor data.
- **Confirm / Cancel Bookings:** Approve or reject booking requests.

### 1.4 Admin

- **Approve Role Requests:** Approve or deny applications to become a Horizon Planner or Venue Manager.
- **Manage Users:** Assign, update, or revoke roles.
- **Oversee Events & Venues:** Monitor all events and venue activities.
- **Moderate Reviews / Comments:** Approve, edit, or remove reviews and comments.
- **View Platform Analytics:** Global stats on bookings, revenue, and user activity.

---

## 2. Pages in the Application

EventEase is split into separate pages for clarity and modern navigation. Pages are routed via a hash-based router (or could be replaced with React Router):

### Auth Page (Login / Signup)

- **Purpose:** Entry point for all users.
- **Features:**
  - Login for existing users
  - Sign up for new users
  - Role selection (demo purposes)
  - Redirects to Home after login
- **Flow:** 
  - Sign up → Home  
  - Login → Home

### Home Page (Events Listing)

- **Purpose:** Main dashboard for Basic Users.
- **Features:**
  - Event search and filtering
  - Event cards with seat selection
  - Book & pay for tickets
  - Download tickets
  - Review events
  - Comment section
  - Request role upgrade
- **Flow:**
  - Click Event → Seat selection → Payment → Ticket download
  - Role upgrade request → Admin review

### Venues Page

- **Purpose:** Browse and filter venues.
- **Features:**
  - Search by location, capacity, amenities
  - View venue availability
  - View images/media for venues
- **Flow:**
  - Basic Users browse → Horizon Planner selects venue → Venue Manager approves

### Horizon Planner Page

- **Purpose:** Manage events and ticketing.
- **Features:**
  - Create events
  - Manage existing events
  - Book venues for events
  - Set ticket inventory and pricing tiers
  - Sales analytics dashboard
- **Flow:**
  - Create Event → Select Venue → Ticketing → Sales Dashboard

### Venue Manager Page

- **Purpose:** Manage venue listings and bookings.
- **Features:**
  - Add/edit/delete venue
  - Set availability
  - Upload media (images/videos)
  - Confirm or cancel booking requests
  - View analytics for bookings
- **Flow:**
  - Add Venue → Set Availability → Monitor Bookings → Approve/Reject Requests

### Admin Page

- **Purpose:** Global control over platform.
- **Features:**
  - Approve role requests
  - Manage all users and roles
  - Monitor all events and venues
  - Moderate reviews and comments
  - View platform-wide analytics
- **Flow:**
  - Review user requests → Approve/Deny → Monitor activity and revenue

### Profile Page

- **Purpose:** User personal info overview.
- **Features:**
  - View name, email, role
  - Placeholder for future profile management
- **Flow:** Accessible from top navigation for logged-in users

### DevTests Page

- **Purpose:** Debugging and automated checks for frontend logic.
- **Features:**
  - Test seat building
  - Test seat booking logic
  - Test ticket generation
- **Flow:** Developers only, runs checks automatically

---

## 3. Navigation & Page Flow

### 3.1 General Flow

- User lands on **Auth Page** by default.
- After login or signup:
  - Redirected to **Home Page**.
- From Home:
  - Users can navigate to Venues, Profile, Horizon Planner / Venue Manager / Admin (based on role).

### 3.2 Role Upgrade Flow

- Basic User requests upgrade → Admin approves → User can access new pages.

### 3.3 Special UI Flow

**Event Booking:**
1. Select Event → Seat Map
2. Select Seats → Click Pay
3. Generate Ticket → Download Ticket
4. Optionally rate or comment

**Venue Booking (Horizon Planner + Venue Manager):**
1. Horizon Planner selects venue → submits booking request
2. Venue Manager approves → Venue booked

**Role Upgrade:**
1. Basic User clicks "Request Role Upgrade"
2. Admin reviews requests → Approve/Deny
3. User gains access to Horizon Planner or Venue Manager pages

---

## 4. Features Summary

- **Authentication:** Login/Signup with separate page, role-based access.
- **Event Management:** Create, update, delete events (Horizon Planner), book venues.
- **Ticket Management:** Seat selection, payment, download ticket, manage inventory.
- **Venue Management:** Add/edit/delete venues, set availability, media uploads, analytics.
- **Admin Management:** User roles, platform overview, approve requests, moderate content.
- **Community Interaction:** Event reviews and comment sections.
- **Analytics & Dashboard:** Sales, bookings, visitor data for managers and admins.
- **Theming:** Light/Dark mode, multiple color accents.
- **Developer Page:** DevTests for checking frontend logic.

---

## 5. Django Project Structure for horizon_planner


5. User Django Project Structure for horizon_planner

horizon_planner/                  # Django project root
├── manage.py               # Django management script
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables (e.g., DB credentials, secret key)
├── horizon_planner/            # Main Django project config
│   ├── __init__.py
│   ├── settings.py         # Main settings (can be split into dev/prod)
│   ├── urls.py             # Root URL router
│   ├── wsgi.py
│   └── asgi.py
│
├── apps/                   # All Django apps (modular design)
│   ├── users/              # Authentication & user roles
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── models.py       # Custom User model, roles
│   │   ├── serializers.py  # DRF serializers (if API-based)
│   │   ├── urls.py         # Users-specific endpoints
│   │   ├── views.py        # Login/Signup, Profile, Role Upgrade
│   │   └── forms.py        # Django forms for signup/login
│   │
│   ├── events/             # Event management
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── models.py       # Event, Category, Seat, Ticket
│   │   ├── serializers.py
│   │   ├── urls.py
│   │   ├── views.py        # Event CRUD, booking
│   │   └── forms.py
│   │
│   ├── venues/             # Venue management
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── models.py       # Venue, Media, Availability
│   │   ├── serializers.py
│   │   ├── urls.py
│   │   ├── views.py        # Venue CRUD, approve bookings
│   │   └── forms.py
│   │
│   ├── reviews/            # Event reviews and comments
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── models.py       # Review, Comment
│   │   ├── serializers.py
│   │   ├── urls.py
│   │   └── views.py        # CRUD, moderation
│   │
│   ├── payments/           # Payment processing & tickets
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── models.py       # Payment, Order, Ticket
│   │   ├── serializers.py
│   │   ├── urls.py
│   │   └── views.py        # Payment gateway integration, ticket download
│   │
│   ├── analytics/          # Platform-wide analytics
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── models.py       # Optional: analytics models
│   │   ├── serializers.py
│   │   ├── urls.py
│   │   └── views.py        # Dashboard, sales reports
│   │
│   └── core/               # Shared utilities
│       ├── __init__.py
│       ├── models.py       # Base models
│       ├── utils.py        # Shared functions (e.g., generate ticket PDF/QR)
│       └── signals.py      # Django signals (e.g., send email on booking)
│
├── templates/              # HTML templates for all apps
│   ├── users/
│   │   ├── login.html
│   │   ├── signup.html
│   │   └── profile.html
│   ├── events/
│   │   ├── event_list.html
│   │   ├── event_detail.html
│   │   └── create_event.html
│   ├── venues/
│   │   ├── venue_list.html
│   │   └── create_venue.html
│   └── base.html           # Base template for all pages
│
├── static/                 # Static files (JS, CSS, images)
│   ├── css/
│   ├── js/
│   └── images/
│
├── media/                  # Uploaded media files
│
└── tests/                  # Test cases for each app
    ├── test_users.py
    ├── test_events.py
    ├── test_venues.py
    ├── test_reviews.py
    └── test_payments.py



---

### App Responsibilities and Flow

| **App**   | **Responsibility**                                | **Connected To / Flow**                                             |
| --------- | ------------------------------------------------- | ------------------------------------------------------------------- |
| users     | Authentication, registration, user roles, profile | Event booking, role upgrades, Admin approval                        |
| events    | Event CRUD, booking, seat management              | Venue availability, ticket generation, reviews                      |
| venues    | Venue CRUD, availability, media, approve bookings | Horizon Planner books venue → Venue Manager approves                  |
| reviews   | Ratings, comments, moderation                     | Linked to events, moderated by Admin                                |
| payments  | Payment processing, orders, ticket downloads      | Tied to events and users; triggers ticket generation                |
| analytics | Dashboards, sales, platform-wide stats            | Aggregates data from events, venues, users, payments                |
| core      | Shared models/utilities                           | Used across all apps (e.g., PDF/QR generation, email notifications) |
