from aws_cdk import (
    Stack,
    aws_budgets as budgets,
    RemovalPolicy
)
from constructs import Construct

class BudgetStack(Stack):
    def __init__(self, scope: Construct, id: str, ENVIROMENT, variables, **kwargs):
        super().__init__(scope, id, **kwargs)

        # Environment variables
        REMOVAL_POLICY = RemovalPolicy.DESTROY

        # Create a monthly budget
        budget = budgets.CfnBudget(
            self,
            f'{ENVIROMENT}-monthly_budget_alarm',
            budget=budgets.CfnBudget.BudgetDataProperty(
                budget_type="COST",
                time_unit="MONTHLY",
                budget_limit=budgets.CfnBudget.SpendProperty(
                    amount=self.node.try_get_context(variables).get("monthly_budget_usd"),
                    unit="USD"
                ),
            ),
            # budget_name = f'{ENVIROMENT}-monthly_budget_alarm',
            notifications_with_subscribers=[
                budgets.CfnBudget.NotificationWithSubscribersProperty(
                    notification=budgets.CfnBudget.NotificationProperty(
                        notification_type="ACTUAL",
                        comparison_operator="GREATER_THAN",
                        threshold=100.0,  # Notification at 100% of the budget
                        threshold_type="PERCENTAGE",
                    ),
                    subscribers=[
                        budgets.CfnBudget.SubscriberProperty(
                            subscription_type="EMAIL",
                            address=self.node.try_get_context(variables).get("quicksight_and_alarm_email")
                        )
                    ],
                )
            ],
        )
        budget.apply_removal_policy(REMOVAL_POLICY)
