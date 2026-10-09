# AWS access setup — owner actions, no deployment yet

Current result: AWS CLI/profile absent; user reports root console access only.
Target region: **ap-south-1 (Mumbai)**. Permissions, credits, budget and costs are
not verified. No resources have been provisioned. Root credentials are never
requested, used, copied or stored by JalSanket.

1. Complete your root password rotation and root MFA setup yourself. While in
   your owner session, open **Billing and Cost Management → Bills**, **Credits**
   and **Free Tier**. Check current charges, credit amount/expiry and service
   restrictions. Record only whether funding covers the intended deployment;
   do not send payment details or credentials.
2. Open **Budgets → Create budget → Use a template → Zero spend budget**. Add
   your own alert email and review/create the notification-only budget. Later,
   approve an explicit maximum deployment spend before a resource is created.
   A budget alert is delayed monitoring, not a hard spending cap. See
   [AWS budget setup](https://docs.aws.amazon.com/cost-management/latest/userguide/budgets-create.html)
   and [budget pricing](https://aws.amazon.com/aws-cost-management/aws-budgets/pricing/).
3. In the standard IAM console, choose **Users → Create user**. Name it
   `jalsanket-readiness`; enable console access and choose the IAM-user option.
   Set its password privately. Do **not** create access keys. If your console
   uses AWS's new team/project experience and does not permit IAM console users,
   stop this path and report that screen; do not use root for development.
4. Choose **Policies → Create policy → JSON** and paste the policy below.
   Review it, name it `JalSanketReadiness`, and attach it to the new user.
   Also attach AWS's **SignInLocalDevelopmentAccess** managed policy.
   Do not attach AdministratorAccess, PowerUserAccess or broad service-full-access
   policies. This readiness policy cannot deploy or change IAM permissions.
5. Open **Users → jalsanket-readiness → Security credentials → Assign MFA device**
   and enroll your device yourself. Sign out of root and sign in as this IAM user.
   [AWS IAM user instructions](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_users_create.html).
6. Install the current official AWS CLI v2 (minimum **2.32.0**). In your terminal,
   run `aws login --profile jalsanket-readiness`, select the **IAM user session**,
   and choose `ap-south-1`. This uses temporary console-login credentials; it is
   not SSO and needs no long-lived access key. Never select the root session.
   [AWS console-login instructions](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-sign-in.html).
7. Tell the agent the profile is ready and confirm your approved spend ceiling
   and credit expiry. We will check identity (reject root), region, read access
   and quotas without printing credentials. Read success does not establish
   deployment permissions. Resource-scoped deployment and runtime roles will
   be reviewed separately once names, budget and deployment scope are approved.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "MumbaiReadinessMetadata",
      "Effect": "Allow",
      "Action": [
        "lambda:ListFunctions",
        "lambda:GetAccountSettings",
        "logs:DescribeLogGroups",
        "cloudwatch:ListMetrics",
        "servicequotas:ListServiceQuotas"
      ],
      "Resource": "*",
      "Condition": {"StringEquals": {"aws:RequestedRegion": "ap-south-1"}}
    },
    {
      "Sid": "MumbaiApiInventory",
      "Effect": "Allow",
      "Action": "apigateway:GET",
      "Resource": [
        "arn:aws:apigateway:ap-south-1::/restapis",
        "arn:aws:apigateway:ap-south-1::/apis"
      ]
    },
    {
      "Sid": "GlobalInventoryOnly",
      "Effect": "Allow",
      "Action": ["s3:ListAllMyBuckets", "cloudfront:ListDistributions"],
      "Resource": "*"
    }
  ]
}
```

The wildcard resources above support account-level list/account APIs. There is
no S3 object read, function-code read, secret read, log-content read, write,
provisioning, billing mutation or IAM-management grant. Billing remains an owner
check at this stage. This proposed policy has not been applied or tested against
the account; any organization restrictions still take precedence.

## Deployment sequence after approval

1. Verify the non-root principal and `ap-south-1`, then perform the permitted
   service inventory/quota checks. The owner confirms credits, expiry and budget.
2. Review an exact deployment-role policy using chosen JalSanket resource names.
   Limit `iam:PassRole` to the named Lambda execution roles and Lambda service;
   no IAM user/key creation. Runtime roles get only their specific S3 prefixes
   and CloudWatch log groups. Account-list APIs do not prove create permissions.
3. Create one private S3 bucket with snapshot/manifest, derived evidence and
   frontend prefixes. Keep public access blocked. Use CloudFront origin access
   control for frontend reads; never expose raw snapshot storage publicly.
4. Use one manually invoked ingestion Lambda for official acquisition and
   derived evidence, and one read-only API Lambda for stored evidence. The
   adapter must preserve the same tested contracts and checksum validation.
   Do not enable a recurring ingestion schedule for the historical demo.
5. Connect API Gateway and CloudFront, restrict backend access/CORS to the
   intended frontend, and use bounded Lambda concurrency, request limits and
   short log retention. Verify actual browser/API/S3/log flows and failure states.
6. Re-run tests and review an explicit teardown procedure and resource inventory.
   Costs to quote before approval: Lambda requests/duration, S3 storage/requests,
   API Gateway requests, CloudFront transfer/requests, CloudWatch ingestion and
   retention. No numeric cost estimate is asserted before sizing and current
   regional pricing are checked. No deployment resources exist yet.
