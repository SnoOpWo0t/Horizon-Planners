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
3. Set the required **Environment Variables**:
   - `SECRET_KEY`
   - `DEBUG=False`
   - `DATABASE_URL` (Neon Postgres Connection String)
   - `CLOUDINARY_URL` (For storing uploaded media files)
4. Deploy! Vercel will automatically detect the `vercel.json` configuration and build your Django application.

### Database Troubleshooting (Neon Postgres)

If you encounter errors related to the database when deploying to Vercel, check the following:

### Use SQLite for Local Testing + Neon for Production (Recommended)

This is the standard, cleanest industry workflow. You don't want your live website talking to a local file, and you don't want your local testing to slow down over the internet.

* **How it works:** When you run the app on your computer (`localhost`), Django automatically connects to  **SQLite** . When you push the code to  **Vercel** , Django instantly switches to  **Neon** .

- **Error:** `attempt to write a readonly database`

  - **Why it happens:** Vercel cannot find your `DATABASE_URL` environment variable, so Django falls back to using the local SQLite database. SQLite is read-only on Vercel's serverless environment.
  - **The Fix:** Ensure you added `DATABASE_URL` in Vercel's Environment Variables and that it's enabled for the **Production** environment. **You must hit "Redeploy"** after adding it, as Vercel does not apply new variables to already-running deployments.
- **Error:** `relation "..." does not exist`

  - **Why it happens:** Vercel successfully connected to your Neon Postgres database, but the database is completely empty (the tables haven't been created yet).
  - **The Fix:** You need to run `python manage.py migrate` to create the tables. You can do this by setting your local `.env` file's `DATABASE_URL` to your Neon connection string, and running `python manage.py migrate` locally.

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