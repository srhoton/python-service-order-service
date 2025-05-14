Please create a github actions in place for this repository. It should:
* On pull requests:
- Run tests, linting, and formatting, and mypy compliance
- Build the python zip file and push it to the artifact bucket
- Run Terraform fmt, validate, init, and plan
* On push to main:
- Run tests, linting, and formatting, and mypy compliance
- Build the python zip file and push it to the artifact bucket
- Run Terraform fmt, validate, init, plan, and apply
* The pipeline should be setup to use the role defined in the secret "AWS_ROLE_TO_ASSUME" to interact with AWS resources.
