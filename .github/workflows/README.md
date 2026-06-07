# CI/CD Workflows for User Service

This directory contains GitHub Actions workflows for building, testing, and deploying the User Service to AWS ECS Fargate.

## Workflows

### 1. `test.yml` — Unit and Integration Tests
Runs on:
- Push to `main`, `master`, `develop`
- Pull requests to those branches

**Steps:**
1. Spin up PostgreSQL container (test database)
2. Install Python dependencies via UV
3. Run pytest suite
4. Upload test results as artifact

**Environment:**
- PostgreSQL 16 (default credentials: `user_service`/`password`)
- Python 3.12

---

### 2. `build.yml` — Build and Push to ECR
Runs on:
- Push to `main` or `master`
- After successful test workflow

**Steps:**
1. Configure AWS credentials (OIDC role assumption)
2. Authenticate to AWS ECR
3. Build Docker image with commit SHA as tag
4. Push to ECR with both commit SHA and `latest` tags

**Outputs:**
- Docker image in ECR: `ACCOUNT.dkr.ecr.REGION.amazonaws.com/aggr-user-service:COMMIT_SHA`
- Latest tag: `ACCOUNT.dkr.ecr.REGION.amazonaws.com/aggr-user-service:latest`

---

### 3. `deploy.yml` — Deploy to ECS Fargate
Runs on:
- Push to `main` or `master`
- After successful build workflow

**Steps:**
1. Configure AWS credentials (OIDC role assumption)
2. Authenticate to ECR
3. Fetch current ECS task definition
4. Update task definition with new image URI
5. Deploy updated task definition to ECS service
6. Wait for deployment stability (configurable retries)

**Deployment Strategy:**
- Updates the task definition
- Triggers ECS service update
- Waits for all tasks to stabilize
- Verifies new tasks are healthy before marking success

---

## Required GitHub Secrets

Configure these in your GitHub repository settings → Secrets and variables → Actions:

### AWS Configuration
- `AWS_ROLE_TO_ASSUME`: IAM role ARN for OIDC (e.g., `arn:aws:iam::ACCOUNT:role/github-actions-role`)
- `AWS_REGION`: AWS region (e.g., `us-east-1`)

### ECS Configuration
- `ECS_CLUSTER_NAME`: Name of the ECS cluster (e.g., `thesis-prod-cluster`)
- `ECS_SERVICE_NAME`: Name of the ECS service (e.g., `aggr-user-service`)

### Example Setup
```bash
gh secret set AWS_ROLE_TO_ASSUME --body "arn:aws:iam::123456789012:role/github-actions-role"
gh secret set AWS_REGION --body "us-east-1"
gh secret set ECS_CLUSTER_NAME --body "thesis-prod-cluster"
gh secret set ECS_SERVICE_NAME --body "aggr-user-service"
```

---

## AWS Setup Guide

### 1. Create OIDC Provider (One-Time)
```bash
aws iam create-open-id-connect-provider \
  --url https://token.actions.githubusercontent.com \
  --client-id-list sts.amazonaws.com \
  --thumbprint-list 6938fd4d98bab03faadb97b34396831e3780aea1
```

### 2. Create IAM Role for GitHub Actions
```bash
cat > trust-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::ACCOUNT:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
        },
        "StringLike": {
          "token.actions.githubusercontent.com:sub": "repo:alexxqq/aggr-user-service:*"
        }
      }
    }
  ]
}
EOF

aws iam create-role \
  --role-name github-actions-user-service \
  --assume-role-policy-document file://trust-policy.json
```

### 3. Attach Permissions Policy
```bash
cat > permissions-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ecr:GetAuthorizationToken",
        "ecr:GetDownloadUrlForLayer",
        "ecr:BatchGetImage",
        "ecr:BatchCheckLayerAvailability",
        "ecr:PutImage",
        "ecr:InitiateLayerUpload",
        "ecr:UploadLayerPart",
        "ecr:CompleteLayerUpload"
      ],
      "Resource": "arn:aws:ecr:REGION:ACCOUNT:repository/aggr-user-service"
    },
    {
      "Effect": "Allow",
      "Action": "ecr:GetAuthorizationToken",
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "ecs:DescribeServices",
        "ecs:DescribeTaskDefinition",
        "ecs:DescribeTasks",
        "ecs:ListTasks",
        "ecs:RegisterTaskDefinition",
        "ecs:UpdateService"
      ],
      "Resource": [
        "arn:aws:ecs:REGION:ACCOUNT:service/CLUSTER/SERVICE",
        "arn:aws:ecs:REGION:ACCOUNT:task-definition/user-service:*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": "iam:PassRole",
      "Resource": [
        "arn:aws:iam::ACCOUNT:role/ecsTaskExecutionRole",
        "arn:aws:iam::ACCOUNT:role/ecsTaskRole"
      ]
    }
  ]
}
EOF

aws iam put-role-policy \
  --role-name github-actions-user-service \
  --policy-name github-actions-user-service-policy \
  --policy-document file://permissions-policy.json
```

### 4. Create ECR Repository
```bash
aws ecr create-repository \
  --repository-name aggr-user-service \
  --region us-east-1
```

### 5. Create ECS Task Definition
Ensure you have a task definition named `user-service` with:
- Container name: `user-service`
- Image: Will be updated by workflow
- Port: 8002 (as per Dockerfile)
- Environment variables configured

Example task definition structure:
```json
{
  "family": "user-service",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "256",
  "memory": "512",
  "containerDefinitions": [
    {
      "name": "user-service",
      "image": "ACCOUNT.dkr.ecr.REGION.amazonaws.com/aggr-user-service:latest",
      "portMappings": [
        {
          "containerPort": 8002,
          "hostPort": 8002,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "DATABASE_URL",
          "value": "postgresql+asyncpg://user:pass@host:5432/db"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/user-service",
          "awslogs-region": "REGION",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ],
  "executionRoleArn": "arn:aws:iam::ACCOUNT:role/ecsTaskExecutionRole",
  "taskRoleArn": "arn:aws:iam::ACCOUNT:role/ecsTaskRole"
}
```

---

## Local Testing

### Run Tests Locally
```bash
# Install dependencies
uv pip install -r requirements.txt

# Start PostgreSQL
docker run -d \
  --name test-postgres \
  -e POSTGRES_DB=user_service_db \
  -e POSTGRES_USER=user_service \
  -e POSTGRES_PASSWORD=password \
  -p 5432:5432 \
  postgres:16-alpine

# Run tests
DATABASE_URL="postgresql+asyncpg://user_service:password@localhost:5432/user_service_db" \
pytest tests/ -v

# Clean up
docker stop test-postgres && docker rm test-postgres
```

### Build and Test Docker Image
```bash
# Build
docker build -t aggr-user-service:test .

# Run container
docker run -d \
  --name user-service-test \
  -e DATABASE_URL="postgresql://..." \
  -p 8002:8002 \
  aggr-user-service:test

# Test health
curl http://localhost:8002/health

# Clean up
docker stop user-service-test && docker rm user-service-test
```

---

## Troubleshooting

### Deployment Stuck on Stability Check
- Check ECS service health: `aws ecs describe-services --cluster CLUSTER --services SERVICE`
- Check task logs: `aws logs tail /ecs/user-service --follow`
- Verify task definition has correct image URI
- Ensure security groups allow port 8002

### ECR Authentication Fails
- Verify OIDC provider is configured
- Check IAM role trust policy includes `token.actions.githubusercontent.com`
- Verify ECR repository exists: `aws ecr describe-repositories --repository-names aggr-user-service`

### Tests Fail in Workflow but Pass Locally
- Check PostgreSQL service is healthy: logs show `database system is ready to accept connections`
- Verify test database URL matches: `postgresql+asyncpg://user_service:password@localhost:5432/user_service_db`
- Check for environmental differences (Python version, UV cache)

---

## Next Steps

1. **Configure secrets** in GitHub (see "Required GitHub Secrets" above)
2. **Set up AWS** infrastructure (see "AWS Setup Guide" above)
3. **Test the workflow** by pushing to `main` or creating a PR
4. **Monitor deployment** in GitHub Actions tab
5. **Verify service** is running in ECS Fargate

---

## Resources

- [GitHub Actions - AWS Credentials](https://github.com/aws-actions/configure-aws-credentials)
- [AWS ECS Task Definition](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task_definitions.html)
- [ECS Fargate](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/ECS_AWSFIPS_endpoints.html)
- [ECR Best Practices](https://docs.aws.amazon.com/AmazonECR/latest/userguide/best-practices.html)
