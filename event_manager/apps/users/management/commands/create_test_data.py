from django.core.management.base import BaseCommand
from apps.users.models import User, RoleUpgradeRequest


class Command(BaseCommand):
    help = 'Create test users and role upgrade requests for development'

    def add_arguments(self, parser):
        parser.add_argument('--create-admin', action='store_true', help='Create admin user')
        parser.add_argument('--create-test-data', action='store_true', help='Create test data')

    def handle(self, *args, **options):
        if options['create_admin']:
            self.create_admin_user()
        
        if options['create_test_data']:
            self.create_test_data()

    def create_admin_user(self):
        """Create an admin user for testing"""
        admin_username = 'admin'
        admin_email = 'admin@eventmanager.com'
        admin_password = 'admin123'
        
        # Check if admin user already exists
        if User.objects.filter(username=admin_username).exists():
            self.stdout.write(
                self.style.WARNING(f'Admin user "{admin_username}" already exists!')
            )
            return
        
        # Create admin user
        admin_user = User.objects.create_user(
            username=admin_username,
            email=admin_email,
            password=admin_password,
            first_name='Admin',
            last_name='User',
            role=User.Role.ADMIN
        )
        admin_user.is_staff = True
        admin_user.is_superuser = True
        admin_user.save()
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created admin user: {admin_username} / {admin_password}'
            )
        )

    def create_test_data(self):
        """Create test users and role upgrade requests"""
        # Create test basic users
        test_users = [
            {
                'username': 'john_doe',
                'email': 'john@example.com',
                'first_name': 'John',
                'last_name': 'Doe',
                'role': User.Role.BASIC
            },
            {
                'username': 'jane_smith',
                'email': 'jane@example.com', 
                'first_name': 'Jane',
                'last_name': 'Smith',
                'role': User.Role.BASIC
            },
            {
                'username': 'bob_wilson',
                'email': 'bob@example.com',
                'first_name': 'Bob',
                'last_name': 'Wilson',
                'role': User.Role.BASIC
            }
        ]
        
        created_users = []
        for user_data in test_users:
            if not User.objects.filter(username=user_data['username']).exists():
                user = User.objects.create_user(
                    username=user_data['username'],
                    email=user_data['email'],
                    password='password123',
                    first_name=user_data['first_name'],
                    last_name=user_data['last_name'],
                    role=user_data['role']
                )
                created_users.append(user)
                self.stdout.write(
                    self.style.SUCCESS(f'Created user: {user.username}')
                )
        
        # Create role upgrade requests
        upgrade_requests = [
            {
                'user': 'john_doe',
                'requested_role': RoleUpgradeRequest.RequestedRole.HORIZON_PLANNER,
                'reason': 'I have experience organizing events at my university and would like to help organize events on this platform. I have managed 5+ successful events with 100+ attendees each.'
            },
            {
                'user': 'jane_smith', 
                'requested_role': RoleUpgradeRequest.RequestedRole.VENUE_MANAGER,
                'reason': 'I own a banquet hall and would like to list my venue on this platform. I have been in the hospitality business for 10 years and have excellent customer service skills.'
            },
            {
                'user': 'bob_wilson',
                'requested_role': RoleUpgradeRequest.RequestedRole.HORIZON_PLANNER,
                'reason': 'I am a professional event planner with 3 years of experience. I have organized corporate events, weddings, and conferences. I would like to expand my services through this platform.'
            }
        ]
        
        for req_data in upgrade_requests:
            try:
                user = User.objects.get(username=req_data['user'])
                if not RoleUpgradeRequest.objects.filter(
                    user=user, 
                    status=RoleUpgradeRequest.Status.PENDING
                ).exists():
                    upgrade_request = RoleUpgradeRequest.objects.create(
                        user=user,
                        requested_role=req_data['requested_role'],
                        reason=req_data['reason']
                    )
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Created role upgrade request: {user.username} -> {req_data["requested_role"]}'
                        )
                    )
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'User {req_data["user"]} not found')
                )
        
        self.stdout.write(
            self.style.SUCCESS('Test data creation completed!')
        )
