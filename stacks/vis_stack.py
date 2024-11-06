# quicksight_stack.py

from aws_cdk import (
    Stack,
    aws_iam as iam,
    aws_quicksight as quicksight,
    aws_lambda as _lambda,
    custom_resources as cr,
    RemovalPolicy,
    Duration,
)
from constructs import Construct

import os
import csv

def find_first_csv_file():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(script_dir) + "/dummy_data"
    
    for root, dirs, files in os.walk(parent_dir):
        for file in files:
            if file.endswith('.csv'):
                file_path = os.path.join(root, file)
                file_name_without_extension = os.path.splitext(file)[0]  # Remove .csv extension
                return file_path, file_name_without_extension  # Return path and name without extension
    return None, None


class QuickSightStack(Stack):
    def __init__(self, scope: Construct, id: str, data_lake_stack: Stack, ENVIROMENT, variables, **kwargs):
        super().__init__(scope, id, **kwargs)

        athena_workgroup_name = data_lake_stack.athena_workgroup.name
    
        # IAM Role for QuickSight to access Athena and S3
        quicksight_role = iam.Role(
            self,
            f'{ENVIROMENT}-quicksight_athena_role',
            assumed_by=iam.ServicePrincipal("quicksight.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonAthenaFullAccess"),
                # iam.ManagedPolicy.from_aws_managed_policy_name("AmazonS3FullAccess"),
            ],
        )
        quicksight_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "s3:GetBucketLocation",
                    "s3:GetObject",
                    "s3:ListBucket",
                    "s3:ListBucketMultipartUploads",
                    "s3:ListMultipartUploadParts",
                    "s3:AbortMultipartUpload",
                    "s3:CreateBucket",
                    "s3:PutObject",
                ],
                resources=[
                    f"arn:aws:s3:::{data_lake_stack.data_lake_bucket.bucket_name}",
                    f"arn:aws:s3:::{data_lake_stack.data_lake_bucket.bucket_name}/*",
                ],
            )
        )
        # Apply removal policy to IAM Role
        quicksight_role.apply_removal_policy(RemovalPolicy.DESTROY)

        # Grant S3 read access to QuickSight role
        data_lake_stack.data_lake_bucket.grant_read_write(quicksight_role)

        # Note: For QuickSight to use this role, you need to assign it in QuickSight's settings

        # QuickSight Data Source
        data_source = quicksight.CfnDataSource(
            self,
            f'{ENVIROMENT}-quicksight_data_source',
            aws_account_id=self.account,
            data_source_id=f'{ENVIROMENT}-athena_data_source',
            name=f'{ENVIROMENT}-{self.node.try_get_context(variables).get("glue_database_name")}',
            type="ATHENA",
            data_source_parameters=quicksight.CfnDataSource.DataSourceParametersProperty(
                athena_parameters=quicksight.CfnDataSource.AthenaParametersProperty(
                    role_arn=quicksight_role.role_arn,
                    work_group=athena_workgroup_name
                )
            ),
            permissions=[
                quicksight.CfnDataSource.ResourcePermissionProperty(
                    actions=[
                        "quicksight:DescribeDataSource",
                        "quicksight:DescribeDataSourcePermissions",
                        "quicksight:PassDataSource",
                        "quicksight:UpdateDataSource",
                        "quicksight:DeleteDataSource",
                        "quicksight:UpdateDataSourcePermissions"
                    ],
                    principal=f"arn:aws:quicksight:{self.region}:{self.account}:user/default/{self.node.try_get_context(variables).get("quicksight_and_alarm_email")}",
                )
            ],
            ssl_properties=quicksight.CfnDataSource.SslPropertiesProperty(
                disable_ssl=False
            ),
        )

       
        csv_path, csv_name = find_first_csv_file()
        with open(csv_path) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter = ',')
            list_of_column_names = []
            for row in csv_reader:
                list_of_column_names.append(row)
                break
        input_columns = []
        for column in list_of_column_names[0]:
            input_columns.append(
                    quicksight.CfnDataSet.InputColumnProperty(
                        name=column,
                        type="STRING"
                    )
                )


        # QuickSight Dataset of the first csv file found under the dummy_data directory
        dataset = quicksight.CfnDataSet(
            self,
            f'{ENVIROMENT}-quicksight_dataset',
            aws_account_id=self.account,
            data_set_id=f'{ENVIROMENT}-athena_dataset',
            name=f'{ENVIROMENT}-athena_dataset',
            permissions=[
                quicksight.CfnDataSet.ResourcePermissionProperty(
                    actions=[
                        "quicksight:DescribeDataSet",
                        "quicksight:DescribeDataSetPermissions",
                        "quicksight:PassDataSet",
                        "quicksight:DescribeIngestion",
                        "quicksight:ListIngestions",
                        "quicksight:UpdateDataSet",
                        "quicksight:DeleteDataSet",
                        "quicksight:CreateIngestion",
                        "quicksight:CancelIngestion",
                        "quicksight:UpdateDataSetPermissions"
                    ],
                    principal=f"arn:aws:quicksight:{self.region}:{self.account}:user/default/{self.node.try_get_context(variables).get("quicksight_and_alarm_email")}",
                )
            ],
            import_mode="DIRECT_QUERY",
            physical_table_map={
                "AthenaTable": quicksight.CfnDataSet.PhysicalTableProperty(
                    relational_table=quicksight.CfnDataSet.RelationalTableProperty(
                        data_source_arn=data_source.attr_arn,
                        catalog="AwsDataCatalog",
                        schema=data_lake_stack.glue_database.database_name,
                        name=csv_name, 
                        input_columns=input_columns,
                    )
                )
            },
        )
        dataset.node.add_dependency(data_source)

#         # Custom Resource to Delete QuickSight Resources on Stack Deletion
#         cleanup_function = _lambda.Function(
#             self,
#             f'{ENVIROMENT}-quicksight_cleanup_lambda',
#             runtime=_lambda.Runtime.PYTHON_3_9,
#             handler="index.handler",
#             code=_lambda.Code.from_inline(
#                 f"""
# import boto3

# def handler(event, context):
#     quicksight = boto3.client('quicksight', region_name='{self.region}')
#     account_id = '{self.account}'
#     user_name = '{quicksight_username}'

#     if event['RequestType'] == 'Delete':

#         try:
#             # Delete Dataset
#             quicksight.delete_data_set(
#                 AwsAccountId=account_id,
#                 DataSetId='{ENVIROMENT}-athena_dataset',
#             )
#         except Exception as e:
#             print(f"Error deleting dataset: {{e}}")

#         try:
#             # Delete Data Source
#             quicksight.delete_data_source(
#                 AwsAccountId=account_id,
#                 DataSourceId='{ENVIROMENT}-athena_data_source'
#             )
#         except Exception as e:
#             print(f"Error deleting data source: {{e}}")

#     return {{'Status': 'SUCCESS'}}
# """
#             ),
#             timeout=Duration.minutes(5),
#         )

#         # Grant Permissions to the Lambda Function
#         cleanup_function.add_to_role_policy(
#             iam.PolicyStatement(
#                 actions=[
#                     "quicksight:DeleteDashboard",
#                     "quicksight:DeleteAnalysis",
#                     "quicksight:DeleteDataSet",
#                     "quicksight:DeleteDataSource",
#                 ],
#                 resources=["*"],
#             )
#         )