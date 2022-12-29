from unittest.case import TestCase
from unittest.mock import patch, MagicMock
import json

import boto3
from botocore.stub import Stubber

from modules.enroll import EnrollAWSAccount


class TestEnrollAwsAccount(TestCase):
    def setUp(self):
        self.aws_account_id = "12345"
        self.management_aws_account_id = "000000"
        self.assume_role_name = "my-test-role"
        self.enroller = EnrollAWSAccount(aws_account_id=self.aws_account_id, assume_role_name=self.assume_role_name)

    def test_init(self):
        enroller = EnrollAWSAccount(aws_account_id=self.aws_account_id, assume_role_name=self.assume_role_name)
        self.assertEqual(self.aws_account_id, enroller.aws_account_id)
        self.assertEqual(self.assume_role_name, enroller.assume_role_name)

    @patch("modules.enroll.EnrollAWSAccount.assume_role_in_destination_account")
    @patch("modules.enroll.boto3")
    def test_get_boto_session_within_target_account(self, boto3_mock, assume_role_in_destination_account_mock):
        boto3_mock.client.return_value.get_caller_identity.return_value = {"Account": self.aws_account_id}
        self.assertEqual(self.enroller.get_boto_session(), boto3_mock.Session.return_value)
        assume_role_in_destination_account_mock.assert_not_called()

    @patch("modules.enroll.EnrollAWSAccount.assume_role_in_destination_account")
    @patch("modules.enroll.boto3")
    def test_get_boto_session_within_management_account(self, boto3_mock, assume_role_in_destination_account_mock):
        boto3_mock.client.return_value.get_caller_identity.return_value = {"Account": self.management_aws_account_id}
        self.assertEqual(self.enroller.get_boto_session(), assume_role_in_destination_account_mock.return_value)
        assume_role_in_destination_account_mock.assert_called_once_with()

    @patch("modules.enroll.boto3")
    def test_asssume_role_in_destination_account(self, boto3_mock):
        access_key = "ABC"
        secret_access_key = "123"
        session_token = "DEF456"
        # If relying on the mocked response entirely, it just validates that the 'an' object two levels down is accessed, not the right key
        boto3_mock.client.return_value.assume_role.return_value = {
            "Credentials": {
                "AccessKeyId": access_key,
                "SecretAccessKey": secret_access_key,
                "SessionToken": session_token,
            }
        }

        self.enroller.assume_role_in_destination_account()
        boto3_mock.client.return_value.assume_role.assert_called_once_with(
            RoleArn=f"arn:aws:iam::{self.aws_account_id}:role/{self.assume_role_name}",
            RoleSessionName="control-tower-enrollment",
        )
        boto3_mock.Session.assert_called_once_with(
            aws_access_key_id=access_key, aws_secret_access_key=secret_access_key, aws_session_token=session_token
        )

    def test_attach_policy(self):
        client_mock = MagicMock()
        self.enroller.iam_client = client_mock
        self.enroller.attach_policy()
        client_mock.attach_role_policy.assert_called_with(
            RoleName=self.enroller.control_tower_role_name, PolicyArn=self.enroller.control_tower_permissions_policy
        )

    @patch("modules.enroll.EnrollAWSAccount.get_iam_client")
    @patch("modules.enroll.EnrollAWSAccount.attach_policy")
    def test_create_role_logging_with_input(self, attach_policy_mock, get_iam_client_mock):

        supplied_account = "123"
        self.enroller.create_role(human_supplied_management_account_id=supplied_account)
        get_iam_client_mock.assert_called_with()
        get_iam_client_mock.return_value.create_role.assert_called_once_with(
            RoleName=self.enroller.control_tower_role_name,
            AssumeRolePolicyDocument=json.dumps(
                {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Principal": {"AWS": f"arn:aws:iam::{supplied_account}:root"},
                            "Action": "sts:AssumeRole",
                            "Condition": {},
                        }
                    ],
                }
            ),
        )
        attach_policy_mock.assert_called_once_with()

    @patch("modules.enroll.EnrollAWSAccount.get_iam_client")
    @patch("modules.enroll.EnrollAWSAccount.attach_policy")
    def test_create_role_logging_with_out_input(self, attach_policy_mock, get_iam_client_mock):
        inheritted_account = "123"
        self.enroller.management_account_id = inheritted_account
        self.enroller.create_role()
        get_iam_client_mock.assert_called_with()
        get_iam_client_mock.return_value.create_role.assert_called_once_with(
            RoleName=self.enroller.control_tower_role_name,
            AssumeRolePolicyDocument=json.dumps(
                {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Principal": {"AWS": f"arn:aws:iam::{inheritted_account}:root"},
                            "Action": "sts:AssumeRole",
                            "Condition": {},
                        }
                    ],
                }
            ),
        )
        attach_policy_mock.assert_called_once_with()

    @patch("modules.enroll.EnrollAWSAccount.get_iam_client")
    @patch("modules.enroll.EnrollAWSAccount.attach_policy")
    def test_create_role_logging_with_role_already_created(self, attach_policy_mock, get_iam_client):
        mock_client = boto3.client("iam")
        get_iam_client.return_value = mock_client
        stubber = Stubber(mock_client)
        stubber.add_client_error("create_role", service_error_code="EntityAlreadyExistsException")
        stubber.activate()
        self.enroller.create_role()
