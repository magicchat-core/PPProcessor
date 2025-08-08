lambda_handler_zip = "lambda_handler.zip"
requirements_zip = "temp/requirements.zip"
bucket_template_file = "bucket.yaml"
bucket_stack_name = "-PPPBct" #change this
s3_bucket_name = "-ppprocessor-bckt" #change this
infra_template_file = "infra.yaml"
custom_domain_template_file = "custom_domain.yaml"
infra_stack_name = "-PPProcessortck" #change this
capabilities = "CAPABILITY_NAMED_IAM"
custom_stack_name_suffix = "-ppprocessor-custom-domain"

# Define Hosted Zone details
hosted_zone_details = {
    "dev": ("addchat.tech", "Z0864672280UKKODZLY6", "arn:aws:acm:ap-south-1:062093044041:certificate/e52db3c6-a8f7-45d9-b63b-819499a391eb"),
    "prod": ("magicchat.io", "Z10112261IW41B5B2W4P7", "arn:aws:acm:ap-south-1:454363227668:certificate/dd851079-b3ec-4362-8c50-b8d748200c01")
}

# MUST BE CHANGED
# HostedZoneId = "Z0713577I1DBW766CFL9"
# HostedZoneName = "addchat.tech"
# env_name = "dev"
