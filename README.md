# 🌅 Horizon Planners

![Django](https://img.shields.io/badge/Django-5.2.6-092E20?style=for-the-badge&logo=django&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)

**Horizon Planners** is a comprehensive, full-stack Event and Venue Management Platform built with Django. It empowers event planners, venue managers, and attendees by providing robust tools for event creation, venue booking, analytics, and category management.

---

## ✨ Features

- **🎭 Event Management**: Easily create, publish, and manage events. Includes an on-the-fly category management system for organizing events efficiently.
- **🏢 Venue Management**: Dedicated dashboard for venue managers to list properties, manage amenities (WiFi, parking, A/V equipment), and handle capacities and pricing.
- **📊 Analytics Dashboard**: Powerful insights and moderation tools for administrators, including exportable revenue, user, and event data.
- **🔐 Role-Based Access Control**: Tailored experiences and permissions for standard users, venue managers, and administrators.
- **📱 Responsive UI**: A beautifully crafted frontend utilizing Bootstrap components for a seamless experience across desktop and mobile devices.

## 🚀 Quick Start (Local Development)

Follow these steps to get the project running on your local machine.

### Prerequisites
- Python 3.10+
- pip (Python package manager)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/horizon-planners.git
   cd horizon-planners
   ```

2. **Set up a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run database migrations**
   ```bash
   python manage.py migrate
   ```

5. **Start the development server**
   ```bash
   python manage.py runserver
   ```

6. **Access the application**
   Open your browser and navigate to `http://127.0.0.1:8000/`.

## ☁️ Deployment (Vercel)

This project is optimized for Serverless Deployment on Vercel.

1. Connect your repository to Vercel.
2. In the Vercel Project Settings:
   - **Root Directory**: Leave empty (or set to `.`)
   - **Build Command**: `bash build.sh` (handles static files and database migrations)
   - **Install Command**: `pip install -r requirements.txt` (Default)
3. Set the required **Environment Variables** (`SECRET_KEY`, `DEBUG=False`, `DATABASE_URL`).
4. Deploy! Vercel will automatically detect the `vercel.json` configuration and build your Django application.

## 📁 Project Structure

```
horizon-planners/
├── apps/                 # Django applications (core, users, events, venues, etc.)
├── horizon_planner/      # Main project settings and configurations
├── static/               # Global static files (CSS, JS, images)
├── templates/            # HTML templates organized by app
├── build.sh              # Build script for Vercel deployment
├── manage.py             # Django command-line utility
├── PROJECT_CONTEXT.md    # Developer & AI Agent architectural context
└── requirements.txt      # Python dependencies
```

## 🤝 Contributing
Contributions are welcome! Please feel free to submit a Pull Request or open an Issue to discuss improvements.
