#!/usr/bin/env python3
import aws_cdk as cdk
from stacks.main_stack import MainStack

app = cdk.App()

MainStack(
    app,
    "MainStack",
    env=cdk.Environment(
        account=app.node.try_get_context("account"),
        region=app.node.try_get_context("region") or "us-west-2"
    )
)

app.synth()
