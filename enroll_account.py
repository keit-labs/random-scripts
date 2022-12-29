import argparse
import logging
import sys
from modules.enroll import EnrollAWSAccount

file_handler = logging.FileHandler(filename="enroll_account.log")
stdout_handler = logging.StreamHandler(stream=sys.stdout)
handlers = [file_handler, stdout_handler]

logging.basicConfig(
    level=logging.INFO, format="[%(asctime)s] {%(filename)s:%(lineno)d} %(levelname)s - %(message)s", handlers=handlers
)

if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Small util to help with enrolling of existing accounts with AWS Control Tower"
    )
    parser.add_argument(
        "--aws-account-id", "-i", help="Destination of the AWS Account Id of role to assume", required=True
    )
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
