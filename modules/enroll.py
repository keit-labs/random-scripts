import boto3, botocore
import logging
import json


class EnrollAWSAccount:
    def __init__(self, aws_account_id: str, assume_role_name: str):
        self.control_tower_role_name = "AWSControlTowerExecution"
        self.control_tower_permissions_policy = "arn:aws:iam::aws:policy/AdministratorAccess"
        self.management_account_id = ""
        self.aws_account_id = aws_account_id
        self.assume_role_name = assume_role_name

    def get_boto_session(self) -> boto3.Session:
        current_aws_account = boto3.client("sts").get_caller_identity()["Account"]
        if current_aws_account == self.aws_account_id:
            return boto3.Session()
        logging.warning(
            f"Not in correct account, will use {self.assume_role_name} to assume access into {self.aws_account_id}"
        )
        self.management_account_id = current_aws_account
        return self.assume_role_in_destination_account()

    def assume_role_in_destination_account(self) -> boto3.Session:
        sts_client = boto3.client("sts")
        destination_session = sts_client.assume_role(
            RoleArn=f"arn:aws:iam::{self.aws_account_id}:role/{self.assume_role_name}",
            RoleSessionName="control-tower-enrollment",
        )
        return boto3.Session(
            aws_access_key_id=destination_session["Credentials"]["AccessKeyId"],
            aws_secret_access_key=destination_session["Credentials"]["SecretAccessKey"],
            aws_session_token=destination_session["Credentials"]["SessionToken"],
        )

    def attach_policy(self):
        self.iam_client.attach_role_policy(
            RoleName=self.control_tower_role_name, PolicyArn=self.control_tower_permissions_policy
        )

    def get_iam_client(self):
        boto_session = self.get_boto_session()
        return boto_session.client("iam")

    def create_role(self, human_supplied_management_account_id: str = ""):
        management_account_id = self.management_account_id or human_supplied_management_account_id

        self.iam_client = self.get_iam_client()

        # https://docs.aws.amazon.com/en_us/controltower/latest/userguide/enroll-manually.html
        try:
            self.iam_client.create_role(
                RoleName=self.control_tower_role_name,
                AssumeRolePolicyDocument=json.dumps(
                    {
                        "Version": "2012-10-17",
                        "Statement": [
                            {
                                "Effect": "Allow",
                                "Principal": {"AWS": f"arn:aws:iam::{management_account_id}:root"},
                                "Action": "sts:AssumeRole",
                                "Condition": {},
                            }
                        ],
                    }
                ),
            )
        except self.iam_client.exceptions.ClientError as ex:
            if ex.response["Error"]["Code"] == "EntityAlreadyExistsException":
                logging.warning("Role Already created")

        logging.info(f"Attaching Policy to Role")
        self.attach_policy()
