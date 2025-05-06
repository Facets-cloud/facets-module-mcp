# Instructions for AI: Writing Concise README Files for Terraform Modules

When writing a README for a Terraform module using write_readme_file() tool, follow these guidelines:

## Structure

1. **Title & Badge Section**
   - Module name and version 
   - Status badges (if applicable)

2. **Overview** (2-3 sentences)
   - What the module does
   - Primary use case
   
3. **Environment as Dimension**
   - **Environment awareness of module what things will change/differ per environment.**
   - Determine it by inspecting usage of `var.environment`

4. **Resources Created** (bulleted list)
   - List all cloud resources in plain English
   - No technical details, just what users need to understand

5. **Security Considerations** (if applicable)
   - Any security implications users should know


## Writing Style

- Use present tense, active voice
- Omit unnecessary words and phrases
- Keep paragraphs to 3 sentences maximum
- Use headers effectively to organize content
- Aim for 70% explanation, 30% examples
- Avoid jargon when plain language works
- Dont show Usage Example

## Example Size

Complete README should be 50-250 lines total, depending on module complexity.