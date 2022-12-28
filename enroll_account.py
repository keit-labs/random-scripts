import argparse
import logging
import sys
import json

import boto3

file_handler = logging.FileHandler(filename="enroll_account.log")
stdout_handler = logging.StreamHandler(stream=sys.stdout)
handlers = [file_handler, stdout_handler]

logging.basicConfig(
    level=logging.INFO, format="[%(asctime)s] {%(filename)s:%(lineno)d} %(levelname)s - %(message)s", handlers=handlers
)


class EnrollAWSAccount:
    def __init__(self, aws_account_id: str, assume_role_name: str):
        self.control_tower_role_name = "AWSControlTowerExecution"
        self.control_tower_permissions_policy = "arn:aws:iam::aws:policy/AdministratorAccess"
        self.management_account_id = ""
        self.aws_account_id = aws_account_id
        self.assume_role_name = assume_role_name
        self.boto3_session = self.get_boto_session()

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

    def create_role(self, human_supplied_management_account_id: str = ""):
        management_account_id = self.management_account_id or human_supplied_management_account_id

        self.iam_client = self.boto3_session.client("iam")
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
        except self.iam_client.exceptions.EntityAlreadyExistsException:
            logging.warning("Role Already created")

        logging.info(f"Attaching Policy to Role")
        self.attach_policy()


parser = argparse.ArgumentParser(
    description="Small util to help with enrolling of existing accounts with AWS Control Tower"
)
parser.add_argument("--aws-account-id", "-i", help="Destination of the AWS Account Id of role to assume", required=True)
parser.add_argument(
    "--role-to-assume",
    help="AWS Role Name (with path) to assume from current account, if not logged into destination account",
    default="OrganizationAccountAccessRole",
)
args = parser.parse_args()


enroller = EnrollAWSAccount(
    aws_account_id=getattr(args, "aws_account_id"), assume_role_name=getattr(args, "role_to_assume")
)
if not enroller.management_account_id:
    management_account_id = input("Provide Management AWS Account Id (where control tower is running): ")
else:
    management_account_id = ""

print("")
logging.info("Creating Role")
enroller.create_role(management_account_id)
