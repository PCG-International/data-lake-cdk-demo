# import aws_cdk.core as cdk
from aws_cdk import (
    App,
    # Duration,
    # core as cdk,
    Stack,
    aws_s3 as s3,
    aws_glue_alpha as glue_,
    aws_glue as _glue,
    aws_lakeformation as lakeformation_,
    aws_iam as iam_,
    aws_sqs as sqs,
    aws_sns as sns,
    aws_s3_notifications as s3_notifications,
    aws_sns_subscriptions as subscriptions,
    aws_s3_deployment as s3deploy,
    RemovalPolicy,
    aws_athena as athena,
    CfnOutput,
    Duration
    # aws_sqs as sqs,
)
from constructs import Construct
import random
import string
import secrets
import os

class DataLakeInfrastrStack(Stack):

    def __init__(self, scope: Construct, id: str, props, ENVIROMENT, variables, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        
        # Environment variables
        REMOVAL_POLICY = RemovalPolicy.DESTROY

        # Create a bucket
        data_lake_bucket = s3.Bucket(
            self,
            f'{ENVIROMENT}-{self.node.try_get_context(variables).get("bucket_name")}',
            bucket_name = f'{ENVIROMENT}-{self.node.try_get_context(variables).get("bucket_name")}',
            versioned=True,
            removal_policy=REMOVAL_POLICY,
            encryption=s3.BucketEncryption.S3_MANAGED,
            auto_delete_objects=True
        )
        self.data_lake_bucket = data_lake_bucket
        deployment = s3deploy.BucketDeployment(
            self, 
            f'{ENVIROMENT}-deployment_of_dummy_data',
            sources=[s3deploy.Source.asset(os.path.join(os.getcwd(), "dummy_data"))],
            destination_bucket=data_lake_bucket
        )
        # Create a glue database
        glue_database = glue_.Database(
            self,
            f'{ENVIROMENT}-{self.node.try_get_context(variables).get("glue_database_name")}',
            database_name = f'{ENVIROMENT}-{self.node.try_get_context(variables).get("glue_database_name")}'
        )
        self.glue_database = glue_database
        glue_database.apply_removal_policy(REMOVAL_POLICY)

        # Create a glue crawler role 
        glue_crawler_role = iam_.Role(
            self,
            f'{ENVIROMENT}-{self.node.try_get_context(variables).get("data_lake_glue_crawler_role")}',
            assumed_by=iam_.ServicePrincipal("glue.amazonaws.com"),
            managed_policies=[
                iam_.ManagedPolicy.from_managed_policy_arn(
                    self,
                    f'{ENVIROMENT}-"data_lake_crawler_glue_role',
                    managed_policy_arn="arn:aws:iam::aws:policy/service-role/AWSGlueServiceRole",
                ),
                iam_.PolicyStatement(
                    actions=["s3:GetObject", "s3:PutObject"],
                    resources=[data_lake_bucket.bucket_arn],
                )
            ]
        )
        glue_crawler_role.add_to_policy(
            iam_.PolicyStatement(
                actions=["lakeformation:GetDataAccess"],
                resources=["*"],
            )
        )
        glue_crawler_role.apply_removal_policy(REMOVAL_POLICY)
        data_lake_bucket.grant_read_write(glue_crawler_role)


        # Create a glue crawler
        random_crawler_attachment = ''.join(random.choice(string.ascii_lowercase) for i in range(4)) 
        glue_crawler = _glue.CfnCrawler(
            self,
            f'{ENVIROMENT}-{self.node.try_get_context(variables).get("glue_crawler_name")}-{random_crawler_attachment}',
            database_name=f'{ENVIROMENT}-{self.node.try_get_context(variables).get("glue_database_name")}',
            role=glue_crawler_role.role_arn,
            name=f'{ENVIROMENT}-{self.node.try_get_context(variables).get("glue_crawler_name")}-{random_crawler_attachment}',
            targets={"s3Targets": [{"path": data_lake_bucket.bucket_name}]},
            # schedule={"scheduleExpression":"cron(0/5 * * * ? *)"},
        ).apply_removal_policy(REMOVAL_POLICY)


        # LakeFormation Permissions, Resources and admins
        lakeformation_.CfnDataLakeSettings(
            self, 
            f'{ENVIROMENT}-data_lake_lake_formation_admins_update',
            admins=[ 
                lakeformation_.CfnDataLakeSettings.DataLakePrincipalProperty(
                    data_lake_principal_identifier=glue_crawler_role.role_arn 
                )
            ],
            trusted_resource_owners=["trustedResourceOwners"]
        )
        data_lake_lake_formation_location_resource = lakeformation_.CfnResource(
            self,
            f'{ENVIROMENT}-data_lake_lake_formation_location_resource',
            resource_arn=data_lake_bucket.bucket_arn,
            use_service_linked_role=True
        )
        data_lake_lake_formation_location_resource.apply_removal_policy(REMOVAL_POLICY)

        # # SQS Queue and permissions
        # s3_sqs_queue = sqs.Queue(
        #     self, 
        #     f'{ENVIROMENT}-{self.node.try_get_context(variables).get("sqs_queue_name")}',
        #     queue_name = f'{ENVIROMENT}-{self.node.try_get_context(variables).get("sqs_queue_name")}'
        # )
        # s3_sqs_queue.apply_removal_policy(REMOVAL_POLICY)

        # s3_notification_topic = sns.Topic(
        #     self, 
        #     f'{ENVIROMENT}-data_lake_s3_notification_topic',
        # )
        # s3_notification_topic.add_subscription(subscriptions.SqsSubscription(s3_sqs_queue))
        # self.s3_notification_topic = s3_notification_topic
        # data_lake_bucket.add_event_notification(s3.EventType.OBJECT_CREATED, s3_notifications.SnsDestination(s3_notification_topic))
        # s3_sqs_queue.grant_consume_messages(glue_crawler_role)
        # glue_crawler_role.add_to_policy(
        #     iam_.PolicyStatement(
        #         actions=[
        #             "sqs:DeleteMessage",
        #             "sqs:GetQueueUrl",
        #             "sqs:ListDeadLetterSourceQueues",
        #             "sqs:ChangeMessageVisibility",
        #             "sqs:PurgeQueue",
        #             "sqs:ReceiveMessage",
        #             "sqs:GetQueueAttributes",
        #             "sqs:ListQueueTags",
        #             "sqs:SetQueueAttributes"
        #         ],
        #         resources=[s3_sqs_queue.queue_arn],
        #     )
        # )
        # glue_crawler_role.add_to_policy(
        #     iam_.PolicyStatement(
        #         actions=[
        #             "sqs:ListQueues"
        #         ],
        #         resources=["*"],
        #     )
        # )

        # Athena Workgroup
        self.athena_workgroup = athena.CfnWorkGroup(
            self,
            f'{ENVIROMENT}_athena_workgroup',
            name=f'{ENVIROMENT}_athena_datalake_workgroup',
            state="ENABLED",
            recursive_delete_option=True,
            work_group_configuration=athena.CfnWorkGroup.WorkGroupConfigurationProperty(
                publish_cloud_watch_metrics_enabled=True,
                requester_pays_enabled=False,
                result_configuration=athena.CfnWorkGroup.ResultConfigurationProperty(
                    output_location=f"s3://{self.data_lake_bucket.bucket_name}/athena-results/"
                ),
            ),
        )
    