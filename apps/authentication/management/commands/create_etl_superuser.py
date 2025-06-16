from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.authentication.utils import generate_random_password

User = get_user_model()


class Command(BaseCommand):
    help = 'Create a superuser with ETL permissions'

    def add_arguments(self, parser):
        parser.add_argument('--email', type=str, help='Email address for the superuser')
        parser.add_argument('--first-name', type=str, help='First name')
        parser.add_argument('--last-name', type=str, help='Last name')
        parser.add_argument('--password', type=str, help='Password (if not provided, will generate random)')
        parser.add_argument('--no-input', action='store_true', help='Run without prompting for input')

    def handle(self, *args, **options):
        email = options.get('email')
        first_name = options.get('first_name')
        last_name = options.get('last_name')
        password = options.get('password')
        no_input = options.get('no_input')

        if not no_input:
            if not email:
                email = input('Email address: ')
            if not first_name:
                first_name = input('First name: ')
            if not last_name:
                last_name = input('Last name: ')
            if not password:
                password = input('Password (leave blank to generate): ')

        if not email:
            self.stdout.write(
                self.style.ERROR('Email address is required')
            )
            return

        if not first_name:
            first_name = 'Admin'
        if not last_name:
            last_name = 'User'

        if not password:
            password = generate_random_password()
            self.stdout.write(
                self.style.WARNING(f'Generated password: {password}')
            )

        if User.objects.filter(email=email).exists():
            self.stdout.write(
                self.style.ERROR(f'User with email {email} already exists')
            )
            return

        try:
            user = User.objects.create_superuser(
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )
            
            self.stdout.write(
                self.style.SUCCESS(f'Successfully created superuser: {email}')
            )
            self.stdout.write(f'Name: {user.get_full_name()}')
            self.stdout.write(f'ETL Permissions: All enabled')
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error creating superuser: {str(e)}')
            )
