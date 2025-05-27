lambda_handler_zip = "lambda_handler.zip"
requirements_zip = "temp/requirements.zip"
bucket_template_file = "bucket.yaml"
bucket_stack_name = "-MyLiveStatusBct"
s3_bucket_name = "-live-status-bckt"
infra_template_file = "infra.yaml"
custom_domain_template_file = "custom_domain.yaml"
infra_stack_name = "-MyLiveStatusBStck"
capabilities = "CAPABILITY_NAMED_IAM"
custom_stack_name_suffix = "-livestatus-custom-domain"

# Define Hosted Zone details
hosted_zone_details = {
    "dev": ("addchat.tech", "Z0713577I1DBW766CFL9", "arn:aws:acm:ap-south-1:454363227668:certificate/7f80f53d-5aa9-41c7-ba62-f8bc913a03ab"),
    "prod": ("magicchat.io", "Z10112261IW41B5B2W4P7", "arn:aws:acm:ap-south-1:454363227668:certificate/a040e2f9-60f9-48e1-9736-2e71df666222")
}

# MUST BE CHANGED
# HostedZoneId = "Z0713577I1DBW766CFL9"
# HostedZoneName = "addchat.tech"
# env_name = "dev"
