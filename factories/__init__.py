"""
Factories for generating test data using Factory Boy and Faker
"""

from .authentication_factories import (
    CustomUserFactory,
    UserProfileFactory,
    UserSessionFactory,
    AdminUserFactory,
    DataEngineerFactory,
    AnalystFactory,
    ViewerFactory,
)

from .core_factories import (
    OrganizationFactory,
    OrganizationMembershipFactory,
    StartupOrganizationFactory,
    EnterpriseOrganizationFactory,
    OrganizationWithTeamFactory,
)

from .connectors_factories import (
    CredentialFactory,
    ConnectorFactory,
    DatabaseConnectorFactory,
    PostgreSQLConnectorFactory,
    MySQLConnectorFactory,
    APIConnectorFactory,
    RESTAPIConnectorFactory,
    FileConnectorFactory,
    CSVFileConnectorFactory,
    CloudConnectorFactory,
    S3ConnectorFactory,
    AzureBlobConnectorFactory,
    ConnectorSetFactory,
)

from .pipelines_factories import (
    PipelineFactory,
    PipelineStepFactory,
    PipelineScheduleFactory,
    PipelineTagFactory,
    PipelineTagAssignmentFactory,
    DataIngestionPipelineFactory,
    DataTransformationPipelineFactory,
    ReportingPipelineFactory,
    CompletePipelineFactory,
)

from .tasks_factories import (
    TaskTemplateFactory,
    TaskFactory,
    TaskParameterFactory,
    TaskDependencyFactory,
    SQLExtractionTaskFactory,
    PythonTransformTaskFactory,
    DatabaseLoadTaskFactory,
    TaskSetFactory,
)

from .execution_factories import (
    PipelineRunFactory,
    SuccessfulPipelineRunFactory,
    FailedPipelineRunFactory,
    LongRunningPipelineRunFactory,
    TaskRunFactory,
    ExecutionQueueFactory,
    ExecutionLockFactory,
    DataLineageFactory,
)

from .monitoring_factories import (
    AlertFactory,
    CriticalAlertFactory,
    PerformanceAlertFactory,
    DataQualityAlertFactory,
    MetricFactory,
    HealthCheckFactory,
    PerformanceReportFactory,
    NotificationChannelFactory,
    NotificationRuleFactory,
    NotificationLogFactory,
)

__all__ = [
    # Authentication
    'CustomUserFactory',
    'UserProfileFactory', 
    'UserSessionFactory',
    'AdminUserFactory',
    'DataEngineerFactory',
    'AnalystFactory',
    'ViewerFactory',
    
    # Core
    'OrganizationFactory',
    'OrganizationMembershipFactory',
    'StartupOrganizationFactory',
    'EnterpriseOrganizationFactory',
    'OrganizationWithTeamFactory',
    
    # Connectors
    'CredentialFactory',
    'ConnectorFactory',
    'DatabaseConnectorFactory',
    'PostgreSQLConnectorFactory',
    'MySQLConnectorFactory',
    'APIConnectorFactory',
    'RESTAPIConnectorFactory',
    'FileConnectorFactory',
    'CSVFileConnectorFactory',
    'CloudConnectorFactory',
    'S3ConnectorFactory',
    'AzureBlobConnectorFactory',
    'ConnectorSetFactory',
    
    # Pipelines
    'PipelineFactory',
    'PipelineStepFactory',
    'PipelineScheduleFactory',
    'PipelineTagFactory',
    'PipelineTagAssignmentFactory',
    'DataIngestionPipelineFactory',
    'DataTransformationPipelineFactory',
    'ReportingPipelineFactory',
    'CompletePipelineFactory',
    
    # Tasks
    'TaskTemplateFactory',
    'TaskFactory',
    'TaskParameterFactory',
    'TaskDependencyFactory',
    'SQLExtractionTaskFactory',
    'PythonTransformTaskFactory',
    'DatabaseLoadTaskFactory',
    'TaskSetFactory',
    
    # Execution
    'PipelineRunFactory',
    'SuccessfulPipelineRunFactory',
    'FailedPipelineRunFactory',
    'LongRunningPipelineRunFactory',
    'TaskRunFactory',
    'ExecutionQueueFactory',
    'ExecutionLockFactory',
    'DataLineageFactory',
    
    # Monitoring
    'AlertFactory',
    'CriticalAlertFactory',
    'PerformanceAlertFactory',
    'DataQualityAlertFactory',
    'MetricFactory',
    'HealthCheckFactory',
    'PerformanceReportFactory',
    'NotificationChannelFactory',
    'NotificationRuleFactory',
    'NotificationLogFactory',
]
