# Security Policy

## Supported Versions

FastCRUD is currently in pre-1.0.0 development. During this phase, only the latest version receives security updates and patches.

| Version        | Supported          |
| -------------- | ------------------ |
| Latest Release | :white_check_mark: |
| Older Versions | :x:                |

We strongly recommend always using the latest version of FastCRUD to ensure you have all security fixes and improvements.

## Reporting a Vulnerability

We take the security of FastCRUD seriously. If you believe you have found a security vulnerability, please report it to us as described below.

### Reporting Process

1. **Do Not** disclose the vulnerability publicly until it has been addressed by our team
2. Submit the vulnerability report to our security team via email at:
   igor.magalhaes.r+fastcrud@gmail.com

   For critical vulnerabilities, you may also open a private issue on the repository or contact the maintainers directly.

### What to Include

Please provide detailed information about the vulnerability, including:

- A clear description of the vulnerability
- Steps to reproduce the issue
- Potential impact
- Suggested fix (if available)
- Your contact information for follow-up questions

### Response Timeline

- Initial Response: Within 48 hours
- Status Update: Within 1 week
- Fix Timeline: Based on severity
  - Critical: Within 7 days
  - High: Within 14 days
  - Medium: Within 30 days
  - Low: Within 60 days

### What to Expect

1. **Acknowledgment**: You will receive an acknowledgment of your report within 48 hours
2. **Investigation**: Our team will investigate the issue and determine its impact
3. **Updates**: You will receive updates on the status of your report
4. **Resolution**: Once resolved, you will be notified of the fix
5. **Public Disclosure**: Coordinated disclosure after the fix is released

## Security Considerations

### Database Security

FastCRUD provides direct database access functionality. When using FastCRUD, ensure:

1. Proper input validation and sanitization
2. Restricted database user permissions
3. Use of prepared statements (handled by SQLAlchemy)
4. Implementation of proper authentication and authorization

### API Security

When exposing FastCRUD endpoints, implement:

1. Authentication for all endpoints
2. Proper authorization checks
3. Rate limiting
4. Input validation
5. CORS policies

### Data Protection

1. Never expose sensitive data in error messages
2. Implement proper logging practices
3. Use HTTPS for all API communications
4. Implement proper data encryption at rest
5. Follow data protection regulations (GDPR, CCPA, etc.)

## Best Practices

1. **Always use the latest supported version**
2. Implement proper authentication and authorization
3. Use HTTPS for all API endpoints
4. Regularly update dependencies
5. Follow the principle of least privilege
6. Implement proper error handling
7. Use secure configuration management
8. Regular security audits and testing

## Security Features

FastCRUD includes several security features:

1. **SQL Injection Prevention**: Through SQLAlchemy's query parameterization
2. **Input Validation**: Via Pydantic schemas
3. **Error Handling**: Secure error responses
4. **Soft Delete Support**: For data protection

## Disclaimer

While FastCRUD implements security best practices, it's crucial to properly secure your application as a whole. This includes:

1. Proper authentication implementation
2. Authorization controls
3. Input validation
4. Error handling
5. Secure configuration
6. Regular security updates
7. Monitoring and logging

## Updates and Notifications

Stay informed about security updates:

1. Watch the GitHub repository
2. Follow our security announcements
3. Subscribe to our security mailing list
4. Monitor our release notes

## License

This security policy is part of the FastCRUD project and is subject to the same license terms.
