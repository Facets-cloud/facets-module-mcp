# Building Facets Modules with AI: A Practical Guide

This guide demonstrates how to collaborate with AI to efficiently build infrastructure modules on the Facets platform,
using a secure S3 bucket module as our example.

## The Conversation Flow

Building effective Facets modules through AI collaboration follows a predictable flow:

1. **Express your requirements**
2. **Refine the design**
3. **Review the implementation**
4. **Validate and test**
5. **Iterate as needed**

Let's see how this works in practice with our S3 bucket example.

## Case Study: S3 Bucket for Banking

### 1. Express Your Requirements

Start by clearly stating your need and any specific constraints:

```
YOU: "I am working with a banking company. I want to create a module for S3 
provisioning with recommended default security posture and give developers 
the ability to define lifecycle policy as short, long, or compliant, and 
whether versioning is enabled or not."
```

**Key elements included:**

- Industry context (banking)
- Primary resource (S3 bucket)
- Security expectations (recommended posture)
- Developer-facing options (lifecycle policy types, versioning toggle)

### 2. Refine the Design

After the AI proposes an initial design, guide it toward your specific needs:

```
AI: [Presents module with detailed configuration options]

YOU: "This is a dev-centric module."

AI: "I understand this is intended to be a developer-centric module. Let me 
revise the facets.yaml to better align with this approach by simplifying 
the options..."

[AI shows simplified design with three options]

YOU: "This looks better, but can we make 'compliance' the default storage 
type since we're building this for a banking company?"
```

**Effective refinement techniques:**

- Clarifying the audience ("dev-centric module")
- Requesting simplification
- Adjusting defaults for your specific context

### 3. Review the Implementation

As the AI implements the module, ask questions to understand key design decisions:

```
YOU: "Can you explain how the storage types affect the lifecycle policies?"

AI: "Each storage type configures different lifecycle rules:

Short-term: Transitions to Standard-IA after 30 days, Glacier after 60 days, 
expires after 90 days.

Long-term: Transitions through storage classes and expires after 7 years.

Compliance: Never expires objects, enforces versioning, and enables access 
logging automatically."
```

**Effective review techniques:**

- Ask about implementation details
- Request explanations of design choices
- Understand security implications

### 4. Validate and Test

After implementation, validate the module and prepare for testing:

```
YOU: "Validate the input types."

AI: [Checks input types and finds issues]
"I've identified that we need to update the AWS provider input type from 
@outputs/aws_provider to @outputs/custom_aws_provider and add the providers 
section to specify that we need the AWS provider."

YOU: "Preview the module."

AI: [Runs module preview]
"The module has been successfully previewed and is available at the provided URL. 
All validation checks have passed."
```

**Key validation actions:**

- Validate specific components (input types, outputs)
- Preview the module to verify platform compatibility
- Check for any validation errors

### 5. Iterate as Needed

Continue refining the module based on validation results and testing feedback:

```
YOU: "The validation failed with this error about the provider configuration."

AI: "I see the issue. The error indicates we need to update the provider reference 
format. Let me explain what's happening and propose a fix..."

YOU: "Run the preview command again."

AI: [Shows preview results]
"The preview is successful! The module has passed all validation checks and is 
available at the provided URL."
```

**Important clarification on capabilities:**

- AI **cannot create** test projects
- AI **cannot add resources** to projects
- AI **can perform** deployments of existing resources
- AI **can check** deployment logs
- AI **can fix** code based on error messages

Typical testing workflow:

```
YOU: "The deployment failed with this error message from the logs."

AI: "I see the issue in the logs. The S3 bucket creation is failing because
the lifecycle configuration syntax is incorrect. Let me fix the code in the
main.tf file..."

[AI updates the code]

YOU: "Deploy it again and check the logs."

AI: [Performs deployment and checks logs]
"The deployment was successful! The logs show that the S3 bucket was created
with the correct lifecycle configuration."
```

## Key Conversation Patterns

### Be Specific About Your Goals

```
"I need a secure S3 bucket module for a banking company"
```

Including industry and security context helps the AI prioritize appropriate defaults.

### Focus on User Experience

```
"This is a dev-centric module"
```

Clearly stating your audience guides the AI to create appropriate abstractions.

### Request Simplification When Needed

```
"This seems complex. Can we simplify it?"
```

Don't hesitate to ask for simpler interfaces when designs become too complex.

### Ask About Implementation Details

```
"How will the storage types affect lifecycle policies?"
```

Understanding implementation details helps you verify that the module behaves as expected.

### Request Validation and Testing

```
"Validate this module"
"Preview this module"
"Can you explain what these validation errors mean?"
```

Regular validation ensures your module meets platform standards before manual testing.

### Troubleshoot Deployment Issues

When deployments encounter problems, AI can help diagnose and fix them:

```
YOU: "The deployment failed. Here are the logs showing the error."

AI: "Looking at the logs, I can see the S3 bucket creation failed because 
of a naming conflict. Let's update the bucket naming logic to include more 
randomization to prevent conflicts."
```

```
YOU: "Can you fix the Terraform syntax causing this deployment error?"

AI: "Yes, I'll update the dynamic block syntax in the lifecycle configuration.
The error occurs because we're not properly handling the empty case."
```

## What Makes an Effective Module

Through this conversation process, we created an S3 bucket module with:

1. **Simple Developer Interface**
    - Just three configuration options instead of dozens
    - Clear, descriptive option names

2. **Secure Defaults**
    - "Compliance" as the default storage type
    - Versioning enabled by default
    - Automatic security settings based on storage type

3. **Abstracted Complexity**
    - Complex lifecycle policies hidden behind simple choices
    - Security best practices applied automatically
    - Terraform configuration generated correctly

4. **Validated Implementation**
    - Checked against Facets platform standards
    - Verified working with AWS provider
    - Confirmed compatible with existing VPC resources

## Testing Capabilities and Deployment

It's important to understand what AI can and cannot do when testing Facets modules:

### AI Limitations

- **Cannot create test projects**: You must use existing projects for testing
- **Cannot add resources to projects**: You must manually add the module as a resource

### AI Capabilities

- **Can perform deployments**: Once resources are added to a project, AI can deploy them
- **Can check deployment logs**: AI can review logs to identify issues
- **Can fix code based on errors**: AI can update module code to resolve problems

### Effective Testing Workflow

1. **You manually create/select a test project**
   ```
   Use an existing project or create a new one in your Facets platform
   ```

2. **You manually add the module as a resource**
   ```
   Add the new module to your test project
   Connect it to required providers
   Configure parameters
   ```

3. **AI can deploy the resources**
   ```
   YOU: "Deploy the resources in the test project."
   
   AI: [Performs deployment]
   "The deployment has been initiated. I'll monitor the progress..."
   ```

4. **AI can check logs and troubleshoot**
   ```
   YOU: "Check the deployment logs and see if there are any issues."
   
   AI: [Retrieves and analyzes logs]
   "I found an error in the logs: 'Invalid lifecycle rule configuration.'
   The issue is in the transition days parameter..."
   ```

5. **AI can fix code problems**
   ```
   YOU: "Can you fix the lifecycle configuration error?"
   
   AI: "Yes, I'll update the main.tf file to fix the lifecycle rules..."
   [AI modifies the code]
   ```

This collaborative approach combines your ability to set up test projects with AI's ability to deploy, monitor, and fix
code issues.

## Summary

Building Facets modules with AI follows a natural conversation flow:

1. **Express requirements** clearly with industry and audience context
2. **Refine designs** by requesting simplification and appropriate defaults
3. **Review implementations** by asking about important details
4. **Validate and test** to ensure platform compatibility
5. **Troubleshoot and fix** by sharing deployment logs and errors

Remember that while AI can help develop, validate, and fix module code, you must handle the actual deployment, testing,
and verification in your environment. By combining the AI's ability to rapidly generate and modify code with your
ability to test in real environments, you can efficiently create high-quality infrastructure modules for your
organization.