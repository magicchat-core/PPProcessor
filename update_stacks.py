import time
import argparse
from stack_info import *  # Contains all stack vars + hosted_zone_details
from cloud_utils import StackDeployer

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("branch_name", help="Git branch name (e.g., dev, staging, prod)")
    args = parser.parse_args()
    
    deployer = StackDeployer()
    

    timestamp = str(int(time.time()))
        # HostedZoneName, HostedZoneId, CertArn = hosted_zone_details.get(env_name, (None, None, None))

        # print(f"Deploying for branch: {env_name}")
    env_name = args.branch_name
    requirements_zip_name = f"requirements_{timestamp}.zip"
    lambda_zip_name = f"lambda_handler_{timestamp}.zip"
    stack_parameters = {
        "bucket_params": {
            "StackPrefix": env_name,
            "S3BucketName": env_name+s3_bucket_name
        },
        "custom_domain_params": {
            "StackPrefix": env_name,
            "HostedZoneName": hosted_zone_details[env_name][0],
            "HostedZoneId": hosted_zone_details[env_name][1],
            "CertArn": hosted_zone_details[env_name][2]
        },
        "infra_params": {
            "StackPrefix": env_name,
            "LambdaZipKey": lambda_zip_name,
            "ReqZipKey": requirements_zip_name,
            "DeploymentTimestamp":timestamp

        }
    }



    deployer.deploy(args.branch_name, {
        "bucket_stack_name": bucket_stack_name,
        "bucket_template_file": bucket_template_file,
        "capabilities": capabilities,
        "s3_bucket_name": s3_bucket_name,
        "custom_stack_name_suffix": custom_stack_name_suffix,
        "custom_domain_template_file": custom_domain_template_file,
        "infra_stack_name": infra_stack_name,
        "infra_template_file": infra_template_file
    },stack_parameters)
