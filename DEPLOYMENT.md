# AWS Deployment Guide

This guide walks through deploying the FinAI Risk Platform to AWS using **ECS Fargate** (recommended for simplicity) or **EC2**.

## Prerequisites

- AWS account with credentials configured locally (`~/.aws/credentials`)
- Docker image pushed to ECR (via CI/CD or manually)
- RDS PostgreSQL instance (with pgvector extension)
- VPC security groups configured

---

## Option A: ECS Fargate (Recommended)

### 1. Create RDS PostgreSQL Instance

```bash
# Using AWS CLI
aws rds create-db-instance \
  --db-instance-identifier finai-postgres \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --engine-version 16.1 \
  --master-username finai \
  --master-user-password <STRONG_PASSWORD> \
  --allocated-storage 20 \
  --storage-type gp3 \
  --publicly-accessible false \
  --vpc-security-group-ids sg-xxxxx
```

After creation, enable the vector extension:

```bash
psql -h <RDS_ENDPOINT> -U finai -d finai
CREATE EXTENSION IF NOT EXISTS vector;
\q
```

Run migrations:

```bash
DATABASE_URL=postgresql://finai:<PASSWORD>@<RDS_ENDPOINT>:5432/finai \
  poetry run alembic upgrade head
```

### 2. Create ECR Repository

```bash
aws ecr create-repository --repository-name finai-risk-platform --region us-east-1
```

Push your Docker image:

```bash
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com

docker tag finai-risk-platform:latest <ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/finai-risk-platform:latest

docker push <ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/finai-risk-platform:latest
```

### 3. Create ECS Cluster

```bash
aws ecs create-cluster --cluster-name finai-prod --region us-east-1
```

### 4. Create IAM Role for ECS Task Execution

```bash
# Create trust policy file
cat > ecs-trust-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "ecs-tasks.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

aws iam create-role \
  --role-name ecsTaskExecutionRole \
  --assume-role-policy-document file://ecs-trust-policy.json

aws iam attach-role-policy \
  --role-name ecsTaskExecutionRole \
  --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy
```

### 5. Register Task Definition

Create `ecs-task-definition.json`:

```json
{
  "family": "finai-task",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "256",
  "memory": "512",
  "containerDefinitions": [
    {
      "name": "finai-backend",
      "image": "<ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/finai-risk-platform:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "hostPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "APP_ENV",
          "value": "prod"
        },
        {
          "name": "LOG_LEVEL",
          "value": "INFO"
        },
        {
          "name": "DATABASE_URL",
          "value": "postgresql://finai:<PASSWORD>@<RDS_ENDPOINT>:5432/finai"
        }
      ],
      "secrets": [
        {
          "name": "GROQ_API_KEY",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:<ACCOUNT_ID>:secret:finai/groq-api-key"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/finai",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ],
  "executionRoleArn": "arn:aws:iam::<ACCOUNT_ID>:role/ecsTaskExecutionRole"
}
```

Register it:

```bash
aws ecs register-task-definition \
  --cli-input-json file://ecs-task-definition.json
```

### 6. Create ECS Service

```bash
aws ecs create-service \
  --cluster finai-prod \
  --service-name finai-api \
  --task-definition finai-task \
  --desired-count 1 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxxxx],securityGroups=[sg-xxxxx],assignPublicIp=ENABLED}" \
  --load-balancers targetGroupArn=arn:aws:elasticloadbalancing:...,containerName=finai-backend,containerPort=8000
```

### 7. (Optional) Set Up Auto Scaling

```bash
aws application-autoscaling register-scalable-target \
  --service-namespace ecs \
  --resource-id service/finai-prod/finai-api \
  --scalable-dimension ecs:service:DesiredCount \
  --min-capacity 1 \
  --max-capacity 3

aws application-autoscaling put-scaling-policy \
  --policy-name finai-scale-out \
  --service-namespace ecs \
  --resource-id service/finai-prod/finai-api \
  --scalable-dimension ecs:service:DesiredCount \
  --policy-type TargetTrackingScaling \
  --target-tracking-scaling-policy-configuration "TargetValue=70.0,PredefinedMetricSpecification={PredefinedMetricType=ECSServiceAverageCPUUtilization}"
```

---

## Option B: Single EC2 Instance (Simpler Alternative)

### 1. Launch EC2 Instance

```bash
aws ec2 run-instances \
  --image-id ami-0c55b159cbfafe1f0 \
  --instance-type t3.micro \
  --security-groups finai-sg \
  --key-name my-key-pair \
  --region us-east-1
```

### 2. SSH and Install Docker

```bash
ssh -i my-key.pem ec2-user@<INSTANCE_IP>

sudo yum update -y
sudo yum install docker -y
sudo systemctl start docker
sudo usermod -a -G docker ec2-user
```

### 3. Pull and Run Docker Container

```bash
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com

docker pull <ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/finai-risk-platform:latest

docker run -d \
  --name finai-api \
  -p 8000:8000 \
  -e DATABASE_URL="postgresql://finai:password@<RDS_ENDPOINT>:5432/finai" \
  -e GROQ_API_KEY="$GROQ_API_KEY" \
  <ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/finai-risk-platform:latest
```

### 4. Set Up Nginx Reverse Proxy (Optional)

```bash
sudo yum install nginx -y

# Edit /etc/nginx/nginx.conf to add upstream and server block:
upstream finai {
  server localhost:8000;
}

server {
  listen 80;
  server_name your-domain.com;

  location / {
    proxy_pass http://finai;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
  }
}

sudo systemctl start nginx
```

---

## Environment Variables (Production)

Store these in AWS Secrets Manager or Systems Manager Parameter Store:

```bash
aws secretsmanager create-secret \
  --name finai/groq-api-key \
  --secret-string "gsk_..."
```

---

## Monitoring & Logging

CloudWatch integration is automatically configured in the ECS task definition (`awslogs-group`). View logs:

```bash
aws logs tail /ecs/finai --follow
```

Use CloudWatch to set up alarms on:
- Error rate
- Latency (p95)
- Container restarts

---

## Updating the Deployment

When you push a new image to ECR:

1. **ECS Fargate**: Update the task definition, then update the service to use the new version.
2. **EC2**: Pull the new image and restart the container.

### ECS Update Example

```bash
aws ecs update-service \
  --cluster finai-prod \
  --service finai-api \
  --force-new-deployment
```

---

## Health Check

Once deployed, verify the API:

```bash
curl -H "X-API-Key: your-key" https://your-api.example.com/health
```

You should see:

```json
{"status": "ok"}
```

---

## Troubleshooting

**Task won't start:**
- Check CloudWatch Logs for errors
- Verify DATABASE_URL and GROQ_API_KEY are set
- Ensure security groups allow database access

**High latency:**
- Check RDS instance type
- Monitor LLM token usage via `/metrics`
- Consider increasing ECS task memory

**Database connection refused:**
- Verify RDS security group allows inbound on port 5432
- Check DATABASE_URL formatting
- Test connection locally before deploying
