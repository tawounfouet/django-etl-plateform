"""
Factories pour les modèles core
"""
import factory
from faker import Faker
from apps.core.models import Organization, OrganizationMembership
from .authentication_factories import CustomUserFactory

fake = Faker('fr_FR')


class OrganizationFactory(factory.django.DjangoModelFactory):
    """Factory pour Organization"""
    
    class Meta:
        model = Organization
        django_get_or_create = ('slug',)

    id = factory.Faker('uuid4')
    name = factory.Faker('company')
    slug = factory.LazyAttribute(lambda obj: fake.slug())
    
    settings = factory.LazyFunction(lambda: {
        'max_pipelines': fake.random_int(10, 1000),
        'max_connectors': fake.random_int(5, 100),
        'max_users': fake.random_int(5, 500),
        'retention_days': fake.random_int(30, 365),
        'allowed_file_types': fake.random_elements(
            ['csv', 'json', 'xml', 'parquet', 'xlsx'], 
            length=fake.random_int(2, 5)
        ),
        'timezone': fake.random_element([
            'UTC', 'Europe/Paris', 'America/New_York'
        ]),
        'notification_settings': {
            'email_enabled': fake.boolean(),
            'slack_enabled': fake.boolean(),
            'webhook_enabled': fake.boolean(),
        },
        'security_settings': {
            'password_expiry_days': fake.random_int(90, 365),
            'max_login_attempts': fake.random_int(3, 10),
            'session_timeout_minutes': fake.random_int(30, 480),
        },
        'feature_flags': {
            'advanced_monitoring': fake.boolean(),
            'data_lineage': fake.boolean(),
            'custom_transforms': fake.boolean(),
            'api_access': fake.boolean(),
        }
    })


class OrganizationMembershipFactory(factory.django.DjangoModelFactory):
    """Factory pour OrganizationMembership"""
    
    class Meta:
        model = OrganizationMembership
        django_get_or_create = ('user', 'organization')

    id = factory.Faker('uuid4')
    user = factory.SubFactory(CustomUserFactory)
    organization = factory.SubFactory(OrganizationFactory)
    role = factory.Faker('random_element', elements=[
        OrganizationMembership.Role.VIEWER,
        OrganizationMembership.Role.DEVELOPER,
        OrganizationMembership.Role.ADMIN,
        OrganizationMembership.Role.OWNER,
    ])
    is_active = factory.Faker('boolean', chance_of_getting_true=90)


# Factories spécialisées pour différents types d'organisations

class StartupOrganizationFactory(OrganizationFactory):
    """Factory pour une startup/petite organisation"""
    name = factory.Faker('random_element', elements=[
        'DataFlow Startup', 'Analytics Pro', 'InnoData Solutions',
        'SmartPipe Technologies', 'DataStream Inc', 'FlowTech Startup'
    ])
    
    settings = factory.LazyFunction(lambda: {
        'max_pipelines': fake.random_int(5, 50),
        'max_connectors': fake.random_int(3, 20),
        'max_users': fake.random_int(2, 25),
        'retention_days': 90,
        'allowed_file_types': ['csv', 'json', 'xlsx'],
        'timezone': 'Europe/Paris',
        'notification_settings': {
            'email_enabled': True,
            'slack_enabled': True,
            'webhook_enabled': False,
        },
        'feature_flags': {
            'advanced_monitoring': False,
            'data_lineage': True,
            'custom_transforms': False,
            'api_access': True,
        }
    })


class EnterpriseOrganizationFactory(OrganizationFactory):
    """Factory pour une grande entreprise"""
    name = factory.Faker('random_element', elements=[
        'Global Data Corp', 'Enterprise Analytics Ltd', 'MegaData Solutions',
        'International Pipeline Co', 'DataVault Enterprise', 'StreamFlow Corp'
    ])
    
    settings = factory.LazyFunction(lambda: {
        'max_pipelines': fake.random_int(500, 2000),
        'max_connectors': fake.random_int(50, 200),
        'max_users': fake.random_int(100, 1000),
        'retention_days': 365,
        'allowed_file_types': ['csv', 'json', 'xml', 'parquet', 'xlsx', 'avro'],
        'timezone': 'UTC',
        'notification_settings': {
            'email_enabled': True,
            'slack_enabled': True,
            'webhook_enabled': True,
        },
        'security_settings': {
            'password_expiry_days': 90,
            'max_login_attempts': 5,
            'session_timeout_minutes': 120,
        },
        'feature_flags': {
            'advanced_monitoring': True,
            'data_lineage': True,
            'custom_transforms': True,
            'api_access': True,
        }
    })


# Factories pour créer des organisations avec des équipes complètes

class OrganizationWithTeamFactory(OrganizationFactory):
    """Factory qui crée une organisation avec une équipe complète"""
    
    @factory.post_generation
    def create_team(self, create, extracted, **kwargs):
        if not create:
            return
        
        from .authentication_factories import (
            AdminUserFactory, DataEngineerFactory, 
            AnalystFactory, ViewerFactory
        )
        
        # Créer un admin/owner
        admin = AdminUserFactory()
        OrganizationMembershipFactory(
            user=admin,
            organization=self,
            role=OrganizationMembership.Role.OWNER
        )
        
        # Créer des data engineers
        for _ in range(fake.random_int(2, 5)):
            engineer = DataEngineerFactory()
            OrganizationMembershipFactory(
                user=engineer,
                organization=self,
                role=OrganizationMembership.Role.DEVELOPER
            )
        
        # Créer des analystes
        for _ in range(fake.random_int(3, 8)):
            analyst = AnalystFactory()
            OrganizationMembershipFactory(
                user=analyst,
                organization=self,
                role=OrganizationMembership.Role.VIEWER
            )
        
        # Créer quelques viewers
        for _ in range(fake.random_int(1, 3)):
            viewer = ViewerFactory()
            OrganizationMembershipFactory(
                user=viewer,
                organization=self,
                role=OrganizationMembership.Role.VIEWER
            )
