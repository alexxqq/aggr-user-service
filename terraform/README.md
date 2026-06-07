# Terraform Infrastructure for User Service

This directory contains Terraform configuration to set up the complete AWS infrastructure for the User Service, including:

- **GitHub Actions OIDC** — Secure AWS authentication from GitHub Actions
- **ECR Repository** — Docker image registry with lifecycle policies
- **ECS Cluster & Service** — Fargate container deployment with auto-scaling
- **CloudWatch Logs** — Centralized logging
- **IAM Roles & Policies** — Fine-grained access control
- **AWS Secrets Manager** — Secure credential storage

## Quick Start

### 1. Install Terraform

```bash
# macOS
brew install terraform

# Linux
wget https://releases.hashicorp.com/terraform/1.7.0/terraform_1.7.0_linux_amd64.zip
unzip terraform_1.7.0_linux_amd64.zip
sudo mv terraform /usr/local/bin/
```

Verify:
```bash
terraform version
```

### 2. Configure AWS Credentials

```bash
# Option A: AWS CLI
aws configure
# Enter: Access Key ID, Secret Access Key, Region, Output format

# Option B: Environment variables
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
export AWS_REGION="us-east-1"

# Option C: AWS SSO (recommended for enterprises)
aws sso login --profile your-profile
export AWS_PROFILE=your-profile
```

### 3. Set Up Terraform Variables

```bash
# Copy the example file
cp terraform.tfvars.example terraform.tfvars

# Edit with your values
vim terraform.tfvars
```

**Variables to set:**
- `aws_region` — AWS region (default: us-east-1)
- `environment` — dev/staging/prod
- `service_name` — aggr-user-service
- `github_repo` — alexxqq/aggr-user-service
- `ecs_cluster_name` — Your ECS cluster name

### 4. Handle Secrets Securely

**Option A: Environment Variables (Dev)**
```bash
export TF_VAR_database_url="postgresql+asyncpg://user:pass@host:5432/db"
export TF_VAR_firebase_credentials='{"type":"service_account",...}'
export TF_VAR_internal_api_secret="your-secret"
```

**Option B: .tfvars File (Local Only)**
```bash
# Create terraform.tfvars (add to .gitignore)
cat > terraform.tfvars <<EOF
database_url = "postgresql+asyncpg://user:pass@host:5432/db"
firebase_credentials = "{\"type\":\"service_account\",...}"
internal_api_secret = "your-secret"
EOF

# Make sure it's ignored
echo "terraform.tfvars" >> ../.gitignore
```

**Option C: AWS Secrets Manager (Production)**
```bash
# Create secrets first
aws secretsmanager create-secret \
  --name aggr-user-service/database-url \
  --secret-string "postgresql+asyncpg://..."

# Then Terraform will reference them
```

### 5. Initialize Terraform

```bash
cd terraform/
terraform init
```

Output should show:
```
Terraform initialized in directory with AWS provider v5.x.x
```

### 6. Review the Plan

```bash
terraform plan
```

This shows what will be created without making any changes. Review carefully:
- ✓ ECR repository
- ✓ ECS cluster/service
- ✓ IAM roles and policies
- ✓ Secrets Manager secrets
- ✓ CloudWatch logs

### 7. Apply the Infrastructure

```bash
terraform apply
```

Type `yes` when prompted. This will:
1. Create ECR repository
2. Set up GitHub Actions OIDC provider (one-time per account)
3. Create IAM roles with proper permissions
4. Create ECS cluster, service, and task definition
5. Create Secrets Manager secrets
6. Configure CloudWatch logging

**Expected time:** 2-3 minutes

### 8. Capture Outputs

After apply completes, note these outputs:
```
ecr_repository_url = "557810226298.dkr.ecr.us-east-1.amazonaws.com/aggr-user-service"
github_actions_role_arn = "arn:aws:iam::557810226298:role/github-actions-aggr-user-service"
```

These are needed for GitHub Actions secrets.

## Post-Terraform Setup

### 1. Set GitHub Actions Secrets

```bash
gh secret set AWS_ROLE_TO_ASSUME --body "arn:aws:iam::557810226298:role/github-actions-aggr-user-service"
gh secret set AWS_REGION --body "us-east-1"
gh secret set ECS_CLUSTER_NAME --body "thesis-cluster"
gh secret set ECS_SERVICE_NAME --body "aggr-user-service"
```

### 2. Update ECS Task Definition with Secrets

Uncomment the `secrets` section in `ecs.tf` once Secrets Manager secrets are created:

```hcl
secrets = [
  {
    name      = "DATABASE_URL"
    valueFrom = "arn:aws:secretsmanager:${var.aws_region}:${data.aws_caller_identity.current.account_id}:secret:${var.service_name}/database-url"
  }
]
```

Then reapply:
```bash
terraform apply
```

### 3. Test the Deployment

Push to the repository to trigger GitHub Actions:
```bash
git push origin master
```

Monitor in Actions tab.

## File Structure

```
terraform/
├── main.tf                   # GitHub OIDC, IAM roles, ECR
├── ecs.tf                    # ECS cluster, service, task definition
├── secrets.tf                # Secrets Manager secrets
├── variables.tf              # Input variables
├── secrets-variables.tf      # Secret input variables
├── terraform.tfvars.example  # Example configuration
└── README.md                 # This file
```

## Common Commands

```bash
# Show current infrastructure
terraform show

# Show specific resource
terraform show aws_ecs_service.service

# Update infrastructure
terraform apply

# Destroy infrastructure
terraform destroy

# Format code
terraform fmt -recursive

# Validate syntax
terraform validate

# Show costs (with Infracost)
terraform plan -json | infracost breakdown --path /dev/stdin
```

## Updating Secrets

### Update database URL
```bash
# Via Terraform
export TF_VAR_database_url="new-url"
terraform apply -target aws_secretsmanager_secret_version.database_url

# Via AWS CLI
aws secretsmanager update-secret \
  --secret-id aggr-user-service/database-url-XXXXX \
  --secret-string "new-url"
```

### Update ECS task definition version
```bash
# Force new deployment with latest image
terraform apply -target aws_ecs_service.service \
  -var 'image_tag=latest'
```

## Troubleshooting

### Error: Invalid provider configuration
```
Error: Invalid provider configuration
```

**Fix:** Run `aws configure` or set AWS credentials via environment variables.

### Error: Repository already exists
```
Error: RepositoryAlreadyExistsException
```

**Fix:** Either:
1. Import existing repo: `terraform import aws_ecr_repository.service aggr-user-service`
2. Change `service_name` variable
3. Destroy: `terraform destroy`

### Error: OIDC provider already exists
```
Error: OpenIDConnectProviderAlreadyExistsException
```

**Fix:** The OIDC provider is shared across all services. Remove from `main.tf` or use `terraform import`:
```bash
terraform import aws_iam_openid_connect_provider.github \
  arn:aws:iam::557810226298:oidc-provider/token.actions.githubusercontent.com
```

### ECS Service keeps replacing task definition
```
Warning: aws_ecs_service.service: Replacement triggered
```

**Fix:** Set `force_new_deployment = false` in `ecs.tf` (already done).

## Remote State (Production)

For team collaboration, use S3 backend:

```hcl
# terraform/backend.tf
terraform {
  backend "s3" {
    bucket         = "your-terraform-state-bucket"
    key            = "aggr-user-service/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}
```

Setup:
```bash
# Create S3 bucket
aws s3api create-bucket --bucket your-terraform-state-bucket --region us-east-1

# Enable versioning
aws s3api put-bucket-versioning \
  --bucket your-terraform-state-bucket \
  --versioning-configuration Status=Enabled

# Create DynamoDB table for locks
aws dynamodb create-table \
  --table-name terraform-locks \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5
```

## Cost Estimation

With default configuration:
- **ECR:** $0.10 per GB stored (usually <1GB for Python service)
- **ECS:** Free (you pay for underlying compute)
- **Fargate (1 task, 256 CPU, 512 MB):** ~$15-20/month
- **CloudWatch Logs:** $0.50 per GB ingested
- **Secrets Manager:** $0.40 per secret/month

**Total:** ~$20-30/month for single dev task

Reduce costs:
- Use `FARGATE_SPOT` for dev (60% cheaper)
- Set `ecs_desired_count = 0` to stop tasks
- Reduce `log_retention_days`

## Next Steps

1. ✅ Run `terraform init`
2. ✅ Set variables in `terraform.tfvars`
3. ✅ Run `terraform plan` to review
4. ✅ Run `terraform apply`
5. ✅ Set GitHub Actions secrets
6. ✅ Update `.github/workflows/deploy.yml` with ECR URL
7. ✅ Push to GitHub to test

See [main README](../README.md) for deployment workflow.
