# Security Policy

## Supported Versions

| Version   | Supported          |
|-----------|--------------------|
| latest    | :white_check_mark: |
| < latest  | :x:                |

We recommend always using the latest version of AEGIS SUPERSTACK to benefit from
the most recent security patches and improvements.

---

## Reporting a Vulnerability

The AEGIS SUPERSTACK team takes security vulnerabilities seriously. We appreciate
your efforts to responsibly disclose any issues you find.

### How to Report

**DO NOT open a public GitHub issue for security vulnerabilities.**

Instead, please report vulnerabilities via email:

- **Email:** IRSTAXBYJORGE@GMAIL.COM
- **Subject Line:** "AEGIS SUPERSTACK - Security Vulnerability Report"

### What to Include

To help us triage and respond quickly, please include the following in your report:

1. **Description:** A clear description of the vulnerability and its potential impact.
2. **Reproduction Steps:** Detailed steps to reproduce the issue, including any
   relevant configuration, environment details, or prerequisites.
3. **Affected Components:** Which modules, files, or APIs are affected.
4. **Severity Assessment:** Your assessment of the severity (Critical, High, Medium, Low).
5. **Proof of Concept:** If available, a proof-of-concept exploit or demonstration
   (please do not include actual malicious payloads).
6. **Suggested Fix:** If you have a proposed fix or mitigation, please include it.

### Response Timeline

| Action                          | Timeframe           |
|---------------------------------|---------------------|
| Acknowledgment of report        | Within 48 hours     |
| Initial assessment and triage   | Within 5 business days |
| Status update to reporter       | Within 10 business days |
| Patch release (critical issues) | Within 14 days      |
| Patch release (other issues)    | Within 30 days      |

### Disclosure Policy

- We follow a **coordinated disclosure** model. We ask that you do not publicly
  disclose the vulnerability until we have had a reasonable opportunity to address it.
- Once a fix is released, we will publicly acknowledge the vulnerability and credit
  the reporter (unless anonymity is requested).
- We will not pursue legal action against security researchers who act in good faith
  and follow this policy.

### Scope

The following are **in scope** for security reports:

- Authentication and authorization bypasses
- Remote code execution vulnerabilities
- SQL injection, XSS, CSRF, and other injection attacks
- Sensitive data exposure
- Privilege escalation
- Cryptographic weaknesses
- Dependency vulnerabilities with exploitable attack vectors

The following are **out of scope:**

- Denial-of-service attacks (unless they reveal an underlying vulnerability)
- Social engineering attacks
- Issues in third-party services or dependencies without a clear exploit path
- Issues that require physical access to the user's device
- Reports from automated scanners without manual verification

### Safe Harbor

We consider security research conducted in accordance with this policy to be:

- Authorized and not subject to legal action under applicable anti-hacking laws
- Exempt from DMCA restrictions on circumvention of technological measures
- Conducted in good faith

We will not pursue civil or criminal action against researchers who comply with
this policy.

---

## Security Best Practices for Users

1. **Keep Updated:** Always run the latest version of the Software.
2. **Environment Variables:** Never commit API keys, secrets, or credentials to
   version control. Use environment variables or a secrets manager.
3. **Access Control:** Follow the principle of least privilege when configuring
   access to the Software and its components.
4. **Network Security:** Deploy behind appropriate firewalls and use TLS for all
   network communications.
5. **Monitoring:** Enable logging and monitoring to detect anomalous behavior.

---

## Contact

For all security-related inquiries:

- **Email:** IRSTAXBYJORGE@GMAIL.COM
- **GitHub:** [github.com/irstabyjorge](https://github.com/irstabyjorge)

---

**Copyright (c) 2024-2026 Jorge Francisco Paredes (irstabyjorge). All rights reserved.**
