"""
Factories pour les modèles d'authentification
"""
import factory
from django.contrib.auth import get_user_model
from django.utils import timezone
from faker import Faker
from apps.authentication.models import UserProfile, UserSession

fake = Faker('fr_FR')  # Utilisation de données en français

User = get_user_model()


class CustomUserFactory(factory.django.DjangoModelFactory):
    """Factory pour CustomUser"""
    
    class Meta:
        model = User
        django_get_or_create = ('email',)

    id = factory.Faker('uuid4')
    email = factory.Sequence(lambda n: f'user{n}@{fake.domain_name()}')
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    
    is_active = True
    is_staff = factory.Faker('boolean', chance_of_getting_true=20)
    
    # Champs ETL spécifiques
    department = factory.Faker('random_element', elements=(
        'Data Engineering', 'Analytics', 'Business Intelligence', 
        'IT Operations', 'Data Science', 'DevOps'
    ))
    job_title = factory.Faker('random_element', elements=(
        'Data Engineer', 'Analytics Engineer', 'BI Developer',
        'ETL Developer', 'Data Architect', 'Platform Engineer',
        'Senior Data Engineer', 'Lead Data Engineer'
    ))
    phone = factory.Faker('phone_number')
    
    # Permissions ETL
    can_create_pipelines = factory.Faker('boolean', chance_of_getting_true=60)
    can_modify_pipelines = factory.Faker('boolean', chance_of_getting_true=40)
    can_execute_pipelines = factory.Faker('boolean', chance_of_getting_true=90)
    can_view_monitoring = factory.Faker('boolean', chance_of_getting_true=95)
    can_manage_connectors = factory.Faker('boolean', chance_of_getting_true=30)
    
    # Préférences utilisateur
    preferences = factory.LazyFunction(lambda: {
        'theme': fake.random_element(['light', 'dark', 'auto']),
        'dashboard_layout': fake.random_element(['grid', 'list', 'cards']),
        'default_page_size': fake.random_int(10, 100),
        'auto_refresh_interval': fake.random_int(30, 300),
        'notifications_enabled': fake.boolean(),
    })
    
    last_login_ip = factory.Faker('ipv4')

    @factory.post_generation
    def set_password(self, create, extracted, **kwargs):
        if not create:
            return
        password = extracted or 'testpass123'
        self.set_password(password)
        self.save()


class UserProfileFactory(factory.django.DjangoModelFactory):
    """Factory pour UserProfile"""
    
    class Meta:
        model = UserProfile
        django_get_or_create = ('user',)

    user = factory.SubFactory(CustomUserFactory)
    
    timezone = factory.Faker('random_element', elements=(
        'UTC', 'Europe/Paris', 'America/New_York', 'Asia/Tokyo',
        'Australia/Sydney', 'America/Los_Angeles'
    ))
    language = factory.Faker('random_element', elements=('en', 'fr', 'es'))
    
    email_notifications = factory.Faker('boolean', chance_of_getting_true=80)
    pipeline_notifications = factory.Faker('boolean', chance_of_getting_true=75)
    
    bio = factory.Faker('text', max_nb_chars=400)


class UserSessionFactory(factory.django.DjangoModelFactory):
    """Factory pour UserSession"""
    
    class Meta:
        model = UserSession

    user = factory.SubFactory(CustomUserFactory)
    session_key = factory.Faker('sha1')
    ip_address = factory.Faker('ipv4')
    user_agent = factory.Faker('user_agent')
    is_active = factory.Faker('boolean', chance_of_getting_true=70)


# Factory spécialisées pour différents types d'utilisateurs

class AdminUserFactory(CustomUserFactory):
    """Factory pour les administrateurs"""
    is_staff = True
    is_superuser = True
    can_create_pipelines = True
    can_modify_pipelines = True
    can_execute_pipelines = True
    can_view_monitoring = True
    can_manage_connectors = True
    job_title = 'Platform Administrator'


class DataEngineerFactory(CustomUserFactory):
    """Factory pour les data engineers"""
    department = 'Data Engineering'
    job_title = factory.Faker('random_element', elements=(
        'Senior Data Engineer', 'Lead Data Engineer', 'Principal Data Engineer'
    ))
    can_create_pipelines = True
    can_modify_pipelines = True
    can_execute_pipelines = True
    can_view_monitoring = True
    can_manage_connectors = True


class AnalystFactory(CustomUserFactory):
    """Factory pour les analystes"""
    department = 'Analytics'
    job_title = factory.Faker('random_element', elements=(
        'Data Analyst', 'Business Analyst', 'BI Developer'
    ))
    can_create_pipelines = False
    can_modify_pipelines = False
    can_execute_pipelines = True
    can_view_monitoring = True
    can_manage_connectors = False


class ViewerFactory(CustomUserFactory):
    """Factory pour les utilisateurs en lecture seule"""
    job_title = 'Business User'
    can_create_pipelines = False
    can_modify_pipelines = False
    can_execute_pipelines = False
    can_view_monitoring = True
    can_manage_connectors = False
