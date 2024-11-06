# AWS Data Lake CDK Deployment Documentation

## Table of Contents

- [AWS Data Lake CDK Deployment Documentation](#aws-data-lake-cdk-deployment-documentation)
  - [Table of Contents](#table-of-contents)
  - [Introduction](#introduction)
  - [Architecture Diagram](#architecture-diagram)
  - [AWS CDK Stack Components](#aws-cdk-stack-components)
    - [Data Lake Stack (`DataLakeInfrastrStack`)](#data-lake-stack-datalakeinfrastrstack)
    - [QuickSight Stack (`QuickSightStack`)](#quicksight-stack-quicksightstack)
    - [Budget Stack (`BudgetStack`)](#budget-stack-budgetstack)
- [Deployment Instructions](#deployment-instructions)
    - [Prerequisites](#prerequisites)
    - [Deployment Steps](#deployment-steps)
  - [Cleanup Instructions](#cleanup-instructions)

---

## Introduction

This documentation provides a comprehensive guide to deploying an AWS Data Lake solution using the AWS Cloud Development Kit (CDK) in Python. The solution includes:

- An **Amazon S3** bucket acting as the data lake storage.
- An **AWS Glue** crawler and database for data cataloging.
- An **Amazon Athena** workgroup for querying the data.
- An **Amazon QuickSight** setup for data visualization.
- An **AWS Budget** alarm to monitor costs exceeding a user-defined amount of USD per month.

This guide includes detailed explanations of each component, deployment instructions, an architecture diagram, deployment and cleanup instructions.

---

## Architecture Diagram
Below is a diagram representing the architecture of the AWS resources:

![image info](/Architecture%20diagram.png)

---

## AWS CDK Stack Components

### Data Lake Stack (`DataLakeInfrastrStack`)

Responsible for setting up the foundational data lake components:

- **Amazon S3 Bucket** (`data_lake_bucket`):
  - Stores raw and processed data.
  - Versioning and server-side encryption enabled.
  - Configured to auto-delete objects and bucket upon stack deletion.

- **AWS Glue Crawler** (`glue_crawler`):
  - Scans the S3 bucket to detect schema changes.
  - Updates the AWS Glue Data Catalog.

- **AWS Glue Database** (`glue_database`):
  - Stores metadata about the data in the S3 bucket.

- **Amazon Athena Workgroup** (`athena_workgroup`):
  - Executes queries against data cataloged by AWS Glue.
  - Stores query results in a specified S3 location within the data lake bucket.

- **IAM Roles and Policies**:
  - `glue_crawler_role`: Grants AWS Glue permissions to read/write to the S3 bucket.

### QuickSight Stack (`QuickSightStack`)

Sets up Amazon QuickSight resources for data visualization:

- **IAM Role** (`quicksight_role`):
  - Allows QuickSight to access Athena and S3.
  - Must be manually assigned in QuickSight settings.

- **QuickSight Data Source** (`data_source`):
  - Connects QuickSight to Athena using the specified workgroup.

- **QuickSight Dataset** (`dataset`):
  - Defines the data to be used for analyses and dashboards.

- **Custom Resource for Cleanup**:
  - AWS Lambda function (`cleanup_function`) to delete QuickSight resources upon stack deletion.

### Budget Stack (`BudgetStack`)

Creates a budget alarm to monitor AWS costs:

- **AWS Budget** (`budget`):
  - Sets a monthly budget limit of user-defined [monthly_budget_usd](cdk.json) amount of USD.
  - Sends notifications when actual spend exceeds 100% of the budget.
  - Notifications are sent via email to the specified address defined in the [quicksight_and_alarm_email](cdk.json) variable.

---


# Deployment Instructions

### Prerequisites

- **AWS Account**: An AWS account with permissions to create the necessary resources.
- **AWS CLI Installed**: Ensure the AWS CLI is installed and configured with your credentials.
- **AWS CDK Installed**: Install the AWS CDK if not already installed.

  ```
  npm install -g aws-cdk
  ```
### Deployment Steps

1. Clone the Repository or Create Project Structure:
    ```
    mkdir data-lake-cdk-demo
    cd data-lake-cdk-demo
    cdk init app --language python
    ```
2. Install Python Dependencies:
   
    Install the dependencies:
    ```
    pip install -r requirements.txt
    ```
      
3. Update Placeholder Values:
      
   Adapt all the variables under the [data_lake_constants](cdk.json) key

4. Bootstrap Your AWS Environment:

    ```
    cdk bootstrap
    ```
5. Synthesize the CDK App:
    ```
    cdk synth
    ```
6. Deploy the CDK App:
    ```
    cdk deploy --all --require-approval never
    ```
7. Confirm Budget Subscription:

    Check your email for a confirmation message from AWS Budgets and confirm your subscription.


## Cleanup Instructions

To delete all resources created by the CDK stacks, run the following command:
```
cdk destroy --all
```