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
    "dev": ("tezkit.com", "Z03262091HLM16BAV8KPT", "arn:aws:acm:ap-south-1:446636409035:certificate/4fda013e-64e3-4312-a775-249dbbf1987a"),
    "prod": ("magicchat.io", "Z051648722RSGAFYGUTGR", "arn:aws:acm:ap-south-1:165672952961:certificate/c4df38ed-6a90-40e6-a509-8079f68f37b1")
}


raz_creds = {

"dev": {

    "api_key" : 'rzp_test_RMogx51YNjGmay',
    "secret" : "I6iGphtRi3o8M333rdJ3SBp1"

    },

    "prod": {


    "api_key" : 'rzp_live_RsjKfKqIOTj4ND',
    "secret" : "pdcYqbBbH6rFM84YyBVT5Ufa"

    },

}




# MUST BE CHANGED
# HostedZoneId = "Z0713577I1DBW766CFL9"
# HostedZoneName = "tezkit.com"
# env_name = "dev"
