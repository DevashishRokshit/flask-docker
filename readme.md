# DevOps Infrastructure Project

A comprehensive infrastructure-as-code project that sets up a scalable Flask application deployment on AWS using Terraform, Auto Scaling Groups, Application Load Balancer, RDS, and CI/CD pipelines.

## 🏗️ Architecture Overview

This project deploys a production-ready Flask application with the following components:

- **VPC & Networking**: Custom VPC with public/private subnets across multiple AZs
- **Auto Scaling Group**: EC2 instances with auto-scaling capabilities
- **Application Load Balancer**: High availability load balancing
- **RDS PostgreSQL**: Managed database service
- **CI/CD Pipeline**: Automated deployment using CodePipeline and CodeDeploy
- **Monitoring**: CloudWatch logs and SNS notifications
- **Security**: IAM roles, security groups, and bastion host access

## 📋 Prerequisites

### System Requirements
- Ubuntu (via VirtualBox, WSL, or native)
- AWS Free Tier account
- Internet connection for package downloads

### Required Tools
- Terraform CLI (latest version)
- AWS CLI v2
- Git
- Docker (optional)
- Python 3 (pre-installed on Ubuntu)

## 🚀 Quick Start

### 1. Environment Setup

#### Install Terraform
```bash
# Update system and install prerequisites
sudo apt-get update && sudo apt-get install -y gnupg software-properties-common curl

# Install HashiCorp GPG key
wget -O- https://apt.releases.hashicorp.com/gpg | \
gpg --dearmor | \
sudo tee /usr/share/keyrings/hashicorp-archive-keyring.gpg > /dev/null

# Add HashiCorp repository
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(grep -oP '(?<=UBUNTU_CODENAME=).*' /etc/os-release || lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list

# Install Terraform
sudo apt update
sudo apt-get install terraform

# Verify installation
terraform -v
```

#### Install AWS CLI
```bash
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Verify installation
aws --version
```

#### Install Git
```bash
sudo apt update
sudo apt install git
git --version
```

#### Install Docker (Optional)
```bash
sudo apt update
sudo apt install apt-transport-https ca-certificates curl software-properties-common

# Add Docker GPG key and repository
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker
sudo apt update
sudo apt install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Add user to docker group (optional)
sudo usermod -aG docker $USER
```

### 2. AWS Configuration

#### Create IAM User
1. Go to AWS Console → IAM → Users → Create user
2. Username: `devops-terraform-user`
3. Set console password: `Test@123`
4. Attach the custom IAM policy (see IAM Policy section below)
5. Create Access Key for programmatic access

#### Configure AWS CLI
```bash
aws configure
```
Enter your:
- Access Key ID
- Secret Access Key
- Default region: `ap-south-1`
- Default output format: `json`

### 3. Project Structure

```
project-root/
├── codes/
│   └── flask-docker/
│       ├── app.py
│       ├── appspec.yml
│       ├── Dockerfile
│       ├── requirements.txt
│       ├── scripts/
│       │   ├── configure_cloudwatch.sh
│       │   ├── install_codedeploy_agent.sh
│       │   └── install_docker.sh
│       └── startup.sh
└── terraform/
    ├── main.tf
    ├── modules/
    │   ├── alb/
    │   ├── asg/
    │   ├── bastion/
    │   ├── cicd/
    │   ├── cloudwatch/
    │   ├── iam/
    │   ├── rds/
    │   ├── sns/
    │   └── vpc/
    ├── outputs.tf
    ├── provider.tf
    ├── security.tf
    ├── terraform.tfvars
    ├── user_data.sh
    └── variables.tf
```

### 4. Deployment

#### Initialize and Deploy Infrastructure
```bash
# Navigate to project root
cd project-root

# Initialize Git repository in Flask app directory
cd codes/flask-docker/
git init
cd ../../

# Initialize Terraform
cd terraform/
terraform init

# Deploy infrastructure
terraform apply -auto-approve
```

#### ⚠️ **MANDATORY: Install CodeDeploy Agent on EC2 Instances**

**This step is REQUIRED for CI/CD pipeline to function properly. Without the CodeDeploy agent, deployments will fail.**

**📌 IMPORTANT DISTINCTION:**
- **WITHOUT CodeDeploy Agent**: ALB will work and show a sample page from `user_data.sh` script
- **WITH CodeDeploy Agent**: You get full CI/CD capability to deploy your actual Flask application from GitHub

**The infrastructure will appear "working" through the ALB even without the agent, but you won't be able to deploy your real application!**

After your infrastructure is deployed, you MUST install the CodeDeploy agent on all EC2 instances in your Auto Scaling Group:

1. **Get your running instance IDs:**
```bash
aws ec2 describe-instances \
  --filters "Name=tag:Name,Values=*devops-app-asg*" "Name=instance-state-name,Values=running" \
  --query 'Reservations[*].Instances[*].InstanceId' \
  --output text
```

2. **Install CodeDeploy agent using SSM (replace with your actual instance IDs):**
```bash
aws ssm send-command \
  --document-name "AWS-RunShellScript" \
  --instance-ids i-077f21068fcd27499 i-01a58c077b2f6a625 \
  --region ap-south-1 \
  --comment "Install CodeDeploy agent" \
  --parameters commands='
    yum update -y
    yum install ruby wget -y
    cd /home/ec2-user
    wget https://aws-codedeploy-ap-south-1.s3.ap-south-1.amazonaws.com/latest/install
    chmod +x ./install
    ./install auto
    systemctl enable codedeploy-agent
    systemctl start codedeploy-agent
  ' \
  --output text
```

3. **Verify CodeDeploy agent installation:**
```bash
aws ssm send-command \
  --document-name "AWS-RunShellScript" \
  --instance-ids i-077f21068fcd27499 i-01a58c077b2f6a625 \
  --region ap-south-1 \
  --comment "Check CodeDeploy agent status" \
  --parameters commands='systemctl status codedeploy-agent' \
  --output text
```

**Important Notes:**
- The CodeDeploy agent must be installed on ALL instances in your Auto Scaling Group
- If you scale up and get new instances, you'll need to install the agent on those too
- Consider adding the CodeDeploy agent installation to your Launch Template user data for automatic installation on new instances

**Alternative: Add to Launch Template User Data**
To automatically install CodeDeploy agent on new instances, add this to your `user_data.sh`:
```bash
#!/bin/bash
# ... existing user data commands ...

# Install CodeDeploy agent
yum update -y
yum install ruby wget -y
cd /home/ec2-user
wget https://aws-codedeploy-ap-south-1.s3.ap-south-1.amazonaws.com/latest/install
chmod +x ./install
./install auto
systemctl enable codedeploy-agent
systemctl start codedeploy-agent
```

## 🔐 IAM Policy

Create a custom IAM policy named `TerraformIAMPolicy` with the following permissions:

<details>
<summary>Click to view IAM Policy JSON</summary>

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "EC2Full",
            "Effect": "Allow",
            "Action": [
                "ec2:*",
                "elasticloadbalancing:*",
                "autoscaling:*"
            ],
            "Resource": "*"
        },
        {
            "Sid": "RDS",
            "Effect": "Allow",
            "Action": [
                "rds:*"
            ],
            "Resource": "*"
        },
        {
            "Sid": "CodeDeployAndS3",
            "Effect": "Allow",
            "Action": [
                "codedeploy:*",
                "s3:*"
            ],
            "Resource": "*"
        },
        {
            "Sid": "CloudWatchAndSNS",
            "Effect": "Allow",
            "Action": [
                "cloudwatch:*",
                "logs:*",
                "sns:*"
            ],
            "Resource": "*"
        },
        {
            "Sid": "IAMScoped",
            "Effect": "Allow",
            "Action": [
                "iam:Get*",
                "iam:List*",
                "iam:CreateRole",
                "iam:AttachRolePolicy",
                "iam:CreateInstanceProfile",
                "iam:AddRoleToInstanceProfile"
            ],
            "Resource": "*"
        },
        {
            "Sid": "PassRolesForTerraform",
            "Effect": "Allow",
            "Action": "iam:PassRole",
            "Resource": [
                "arn:aws:iam::*:role/ec2-instance-role-codedeploy",
                "arn:aws:iam::*:role/codedeploy-role",
                "arn:aws:iam::*:role/*ssm-role*"
            ],
            "Condition": {
                "StringEqualsIfExists": {
                    "iam:PassedToService": [
                        "ec2.amazonaws.com",
                        "codedeploy.amazonaws.com",
                        "autoscaling.amazonaws.com"
                    ]
                }
            }
        },
        {
            "Sid": "CreateServiceLinkedRoles",
            "Effect": "Allow",
            "Action": "iam:CreateServiceLinkedRole",
            "Resource": "*",
            "Condition": {
                "StringLike": {
                    "iam:AWSServiceName": [
                        "autoscaling.amazonaws.com",
                        "codedeploy.amazonaws.com",
                        "elasticloadbalancing.amazonaws.com",
                        "rds.amazonaws.com"
                    ]
                }
            }
        },
        {
            "Sid": "SSMAccess",
            "Effect": "Allow",
            "Action": [
                "ssm:*",
                "ssmmessages:*"
            ],
            "Resource": "*"
        },
        {
            "Sid": "CodePipelineFullAccess",
            "Effect": "Allow",
            "Action": [
                "codepipeline:*",
                "codebuild:*",
                "codestar-connections:*",
                "iam:PassRole"
            ],
            "Resource": "*"
        },
        {
            "Sid": "IAMInstanceProfileManagement",
            "Effect": "Allow",
            "Action": [
                "iam:DeleteInstanceProfile",
                "iam:RemoveRoleFromInstanceProfile"
            ],
            "Resource": "*"
        },
        {
            "Sid": "DetachPolicy",
            "Effect": "Allow",
            "Action": [
                "iam:DetachRolePolicy"
            ],
            "Resource": "*"
        },
        {
            "Sid": "DeleteIAMRoles",
            "Effect": "Allow",
            "Action": [
                "iam:DeleteRole"
            ],
            "Resource": "*"
        },
        {
            "Sid": "DisassociateAndReleaseEIP",
            "Effect": "Allow",
            "Action": [
                "ec2:DisassociateAddress",
                "ec2:ReleaseAddress"
            ],
            "Resource": "*"
        },
        {
            "Sid": "DeleteSecurityGroupAndENI",
            "Effect": "Allow",
            "Action": [
                "ec2:DeleteSecurityGroup",
                "ec2:DeleteNetworkInterface",
                "ec2:DetachNetworkInterface"
            ],
            "Resource": "*"
        },
        {
            "Sid": "DeleteSubnetAndRoute",
            "Effect": "Allow",
            "Action": [
                "ec2:DeleteSubnet",
                "ec2:DeleteRoute",
                "ec2:DeleteRouteTable",
                "ec2:DisassociateRouteTable"
            ],
            "Resource": "*"
        },
        {
            "Sid": "DeleteNATGateway",
            "Effect": "Allow",
            "Action": [
                "ec2:DeleteNatGateway"
            ],
            "Resource": "*"
        },
        {
            "Sid": "DeleteDBSubnetGroup",
            "Effect": "Allow",
            "Action": [
                "rds:DeleteDBSubnetGroup"
            ],
            "Resource": "*"
        }
    ]
}

```
</details>

## 🔧 Configuration

### Terraform Variables
Customize your deployment by modifying `terraform.tfvars`:

```hcl
# Example configuration
region = "ap-south-1"
vpc_cidr = "10.0.0.0/16"
environment = "dev"
instance_type = "t3.micro"
min_size = 2
max_size = 6
desired_capacity = 2
```

### Environment Variables
Set the following environment variables:
```bash
export AWS_REGION=ap-south-1
export AWS_DEFAULT_REGION=ap-south-1
```

## ⚡ Critical Success Factors

### 🔴 **MUST DO: CodeDeploy Agent Installation**
**Your CI/CD pipeline will NOT work without this step!**

Before pushing any code or expecting deployments to work:
1. ✅ Deploy infrastructure with `terraform apply`
2. ✅ **Install CodeDeploy agent on ALL EC2 instances** (see mandatory section above)
3. ✅ Verify agent is running on all instances
4. ✅ Only then push code to trigger deployments

### 🟡 **Pipeline Dependencies**
- GitHub repository must be properly connected to CodePipeline
- S3 bucket for CodeDeploy artifacts must exist
- All IAM roles must have correct permissions
- Auto Scaling Group instances must be healthy and running

### 🔵 **What Works Without CodeDeploy Agent:**
- ✅ Infrastructure deployment (VPC, ALB, ASG, RDS)
- ✅ ALB health checks pass
- ✅ Sample page displays via ALB (from user_data.sh)
- ✅ Basic infrastructure monitoring

### 🔴 **What DOESN'T Work Without CodeDeploy Agent:**
- ❌ CI/CD pipeline deployments
- ❌ Deploying your actual Flask application
- ❌ GitHub-triggered deployments
- ❌ CodeDeploy application revisions
- ❌ Automatic application updates

**Bottom Line: You'll see a "working" website, but it's just the sample page. Your real application won't deploy until you install the CodeDeploy agent.**

The project includes automated CI/CD using AWS CodePipeline and CodeDeploy:

1. **Source Stage**: Monitors GitHub repository for changes
2. **Build Stage**: Uses CodeBuild to build the Docker image
3. **Deploy Stage**: Uses CodeDeploy to deploy to Auto Scaling Group

### Triggering Deployments
Push changes to your GitHub repository to trigger automatic deployments:

```bash
git add .
git commit -m "Update application"
git push origin main
```

Monitor progress in:
- AWS CodePipeline console
- AWS CodeDeploy console
- CloudWatch logs

## 🎯 Understanding the Deployment Flow

### Phase 1: Infrastructure Only (After `terraform apply`)
```
Internet → ALB → EC2 Instances → Sample Page (from user_data.sh)
```
- ✅ ALB is accessible and shows a basic sample page
- ✅ Infrastructure is healthy
- ❌ No CI/CD capability yet

### Phase 2: Complete CI/CD Setup (After CodeDeploy Agent Installation)
```
GitHub Push → CodePipeline → CodeBuild → CodeDeploy → EC2 Instances → Your Flask App
```
- ✅ Full CI/CD pipeline operational
- ✅ Your actual Flask application deployed
- ✅ GitHub integration working
- ✅ Automated deployments on code changes

**Key Insight**: Many users think their setup is complete after Phase 1 because the ALB works, but they're only seeing the sample page, not their actual application!

## 🎯 Scope & Features
- **VPC**: Custom Virtual Private Cloud with public/private subnets
- **EC2**: Auto Scaling Group with Launch Templates
- **ALB**: Application Load Balancer for high availability
- **RDS**: PostgreSQL database under Private Subnet
- **IAM**: Roles and policies for secure access
- **S3**: Storage for CodeDeploy artifacts
- **CloudWatch**: Monitoring and logging
- **SNS**: Notifications for scaling events
- **SSM**: Systems Manager for instance management


## 🧹 Cleanup

To destroy the infrastructure and avoid AWS charges:

```bash
cd terraform/
terraform destroy -auto-approve
```

⚠️ **Warning**: This will permanently delete all resources created by Terraform.
