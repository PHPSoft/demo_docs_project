import boto3
import re
from botocore.exceptions import ClientError

def is_vulnerable_s3_bucket(bucket_name, account_id):
    s3 = boto3.client('s3')
    
    # Check if bucket follows the predictable CDK pattern
    cdk_pattern = rf"^cdk-hnb659fds-assets-{account_id}-[a-z0-9\-]+$"
    if not re.match(cdk_pattern, bucket_name):
        print(f"Bucket {bucket_name} does not follow the default CDK pattern.")
    else:
        print(f"Bucket {bucket_name} follows the default CDK naming pattern, which could be predictable.")

    # Check bucket ACL and policy for public access
    try:
        # Check bucket ACL
        acl_response = s3.get_bucket_acl(Bucket=bucket_name)
        for grant in acl_response['Grants']:
            grantee = grant['Grantee']
            permission = grant['Permission']
            if grantee.get('URI') == "http://acs.amazonaws.com/groups/global/AllUsers":
                print(f"Warning: Bucket {bucket_name} is publicly accessible with {permission} permissions.")

        # Check bucket policy for public access
        try:
            policy_response = s3.get_bucket_policy(Bucket=bucket_name)
            policy = policy_response['Policy']
            if '"Effect": "Allow", "Principal": "*"' in policy:
                print(f"Warning: Bucket {bucket_name} has a policy allowing public access.")
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchBucketPolicy':
                print(f"No bucket policy found for {bucket_name}.")
            else:
                raise

    except ClientError as e:
        print(f"Could not retrieve ACL or policy for {bucket_name}: {e}")

def check_all_buckets():
    s3 = boto3.client('s3')
    sts = boto3.client('sts')

    # Get account ID
    account_id = sts.get_caller_identity()["Account"]

    # List all buckets
    try:
        buckets = s3.list_buckets()["Buckets"]
        print(f"Found {len(buckets)} bucket(s) in the account.")
        for bucket in buckets:
            bucket_name = bucket["Name"]
            print(f"\nChecking bucket: {bucket_name}")
            is_vulnerable_s3_bucket(bucket_name, account_id)
    except ClientError as e:
        print(f"Could not list buckets: {e}")

# Run the check for all buckets
check_all_buckets()
