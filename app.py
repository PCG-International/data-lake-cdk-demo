#!/usr/bin/env python3
import os

import aws_cdk as cdk

from stacks.data_lake_infrastructure_stack import DataLakeInfrastrStack
from stacks.budgets_stack import BudgetStack
from stacks.vis_stack import QuickSightStack


# Environment variables
ENVIROMENT = "demo"
variables = "data_lake_constants"

app = cdk.App()
props = {'namespace': 'DataLakeInfStack'}
data_lake_stack = DataLakeInfrastrStack(app, "DataLakeExampleAwsStack",props, ENVIROMENT = ENVIROMENT, variables=variables)
BudgetStack(app, "BudgetStack", ENVIROMENT = ENVIROMENT, variables=variables)
quicksight_stack = QuickSightStack(app, "QuickSightStack", data_lake_stack=data_lake_stack, ENVIROMENT = ENVIROMENT, variables=variables)

app.synth()
