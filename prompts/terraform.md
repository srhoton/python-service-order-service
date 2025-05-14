In a terraform directory in the root of the project, please create the following:
* A backend configuration that uses the S3 bucket 'srhoton-tfstate'. It should not use dynamodb locking.
* An AppConfiguration resource that can be used to get the AppConfig requirements of the python lambda function in this project.
* A DynamoDB table created as it is defined in the python lambda function.
* It should be able to build and deploy the lambda function, using an S3 bucket for the zip file of the lambda function. Create the S3 bucket as well.
* Segment the files according to best practices.
* Make sure all the code you write successfully passes 'terraform fmt', 'terraform validate', and 'tflint'.
* Update the README.md file with instructions on how to use the terraform configuration.
