import os
import subprocess
import time
import shutil

def zip_lambda_handler():
    try:
        # Zip lambda_handler.py
        # subprocess.run(["zip", "-jr","lambda_handler.zip", "src/*"])
        subprocess.run("zip -jr lambda_handler.zip src/*", shell=True)

        print("Lambda handler zip created successfully.")
    except Exception as e:
        print(f"Error zipping lambda handler: {e}")

def zip_requirements():
    try:
        # Create temporary directory
        temp_dir = "temp"
        os.makedirs(temp_dir, exist_ok=True)

        # Create site-packages directory inside temp_dir
        site_packages_dir = os.path.join(temp_dir,"python", "lib", "python3.9", "site-packages")
        os.makedirs(site_packages_dir, exist_ok=True)

        # Install requirements into site-packages directory
        install_requirements(site_packages_dir)

        # Zip contents of temp_dir into requirements.zip
        # subprocess.run(["cd", "temp/python"])
        prv_dir = os.getcwd()
        os.chdir(temp_dir)
        subprocess.run(["ls"])
        subprocess.run(["zip", "-r", "requirements.zip", "."])
        os.chdir(prv_dir)
        print("Requirements zip created successfully.")
    except Exception as e:
        print(f"Error zipping requirements: {e}")

def install_requirements(site_packages_dir):
    try:
        # Install requirements using pip to the site-packages directory
        subprocess.run(["pip", "install", "-r", "requirements.txt", "-t", site_packages_dir])
        print("Requirements installed successfully.")
    except Exception as e:
        print(f"Error installing requirements: {e}")
def create_s3_bucket(stack_name, template_file):
    try:
        # Create S3 bucket stack
        subprocess.run(["aws", "cloudformation", "create-stack", "--stack-name", stack_name, "--template-body", f"file://{template_file}"])
        print(f"S3 bucket stack '{stack_name}' created successfully.")
    except Exception as e:
        print(f"Error creating S3 bucket stack '{stack_name}': {e}")

def upload_lambda_to_s3(zip_file, bucket_name):
    max_retries = 3
    retries = 0
    while retries < max_retries:
        try:
            # Check if bucket exists
            subprocess.run(["aws", "s3", "ls", f"s3://{bucket_name}/"], check=True)
            # Upload lambda_handler.zip to S3 bucket
            subprocess.run(["aws", "s3", "cp", zip_file, f"s3://{bucket_name}/"])
            print(f"Lambda handler zip uploaded to S3 bucket '{bucket_name}' successfully.")
            return
        except subprocess.CalledProcessError:
            retries += 1
            print(f"Bucket '{bucket_name}' does not exist. Retrying in 5 seconds...")
            time.sleep(5)
    print(f"Failed to upload lambda handler zip to S3 bucket '{bucket_name}' after {max_retries} retries.")

def create_cloudformation_stack(stack_name, template_file, capabilities):
    try:
        # Create CloudFormation stack
        subprocess.run(["aws", "cloudformation", "create-stack", "--stack-name", stack_name, "--template-body", f"file://{template_file}", "--capabilities", capabilities])
        print(f"CloudFormation stack '{stack_name}' created successfully.")
    except Exception as e:
        print(f"Error creating CloudFormation stack '{stack_name}': {e}")

if __name__ == "__main__":
    # Define file paths and stack names
    lambda_handler_zip = "lambda_handler.zip"
    requirements_zip = "temp/requirements.zip"
    bucket_template_file = "bucket.yaml"
    bucket_stack_name = "MyLiveStatusBct"
    s3_bucket_name = "live-status-bckt"
    infra_template_file = "infra.yaml"
    infra_stack_name = "MyLiveStatusBStck"
    capabilities = "CAPABILITY_NAMED_IAM"

    # Execute commands
    zip_requirements()
    zip_lambda_handler()
    create_s3_bucket(bucket_stack_name, bucket_template_file)
    upload_lambda_to_s3(lambda_handler_zip, s3_bucket_name)
    upload_lambda_to_s3(requirements_zip, s3_bucket_name)
    create_cloudformation_stack(infra_stack_name, infra_template_file, capabilities)
