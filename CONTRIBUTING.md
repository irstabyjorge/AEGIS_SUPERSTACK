# Contributing to AEGIS SUPERSTACK

Thank you for your interest in contributing to AEGIS SUPERSTACK! We welcome
contributions from the community and appreciate your effort to help improve
this project.

---

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How to Contribute](#how-to-contribute)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Pull Request Process](#pull-request-process)
- [Coding Standards](#coding-standards)
- [Reporting Bugs](#reporting-bugs)
- [Requesting Features](#requesting-features)
- [License](#license)

---

## Code of Conduct

By participating in this project, you agree to uphold a welcoming, inclusive, and
respectful environment for everyone. We expect all contributors to:

- Be respectful and constructive in all communications
- Welcome newcomers and help them get oriented
- Focus on what is best for the community and the project
- Accept constructive criticism gracefully
- Refrain from any form of harassment, discrimination, or personal attacks

Violations of the code of conduct may result in removal from the project.

---

## How to Contribute

There are many ways to contribute to AEGIS SUPERSTACK:

1. **Report Bugs:** Found a bug? Open an issue with a detailed description.
2. **Suggest Features:** Have an idea? Open a feature request issue.
3. **Submit Pull Requests:** Fix bugs, add features, or improve documentation.
4. **Improve Documentation:** Help us make the docs clearer and more complete.
5. **Write Tests:** Help improve test coverage and reliability.
6. **Review Pull Requests:** Help review and provide feedback on open PRs.

---

## Getting Started

1. **Fork the repository** on GitHub.

2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/AEGIS_SUPERSTACK.git
   cd AEGIS_SUPERSTACK
   ```

3. **Add the upstream remote:**
   ```bash
   git remote add upstream https://github.com/irstabyjorge/AEGIS_SUPERSTACK.git
   ```

4. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

5. **Create a feature branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```

---

## Development Workflow

1. **Sync with upstream** before starting work:
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. **Make your changes** in small, focused commits with clear messages.

3. **Test your changes** thoroughly before submitting.

4. **Keep your branch up to date** with the main branch:
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

---

## Pull Request Process

1. **Ensure your code follows** the project's coding standards (see below).

2. **Write a clear PR description** that explains:
   - What the change does
   - Why the change is needed
   - How it was tested
   - Any breaking changes or migration steps

3. **Link related issues** in the PR description using keywords like
   "Fixes #123" or "Closes #456".

4. **Keep PRs focused.** One PR should address one concern. If you have
   multiple unrelated changes, submit separate PRs.

5. **Respond to review feedback** promptly and constructively.

6. **Squash commits** if requested by the maintainers before merging.

### PR Checklist

Before submitting your PR, please verify:

- [ ] Code compiles/runs without errors
- [ ] All existing tests pass
- [ ] New tests are added for new functionality
- [ ] Documentation is updated if needed
- [ ] No sensitive information (API keys, passwords, etc.) is included
- [ ] Commit messages are clear and descriptive
- [ ] The branch is up to date with the main branch

---

## Coding Standards

- **Language:** Follow the conventions of the language used in the file you are
  editing (Python PEP 8, etc.).
- **Naming:** Use clear, descriptive variable and function names.
- **Comments:** Write comments to explain "why," not "what." The code should be
  self-explanatory for the "what."
- **Documentation:** Update docstrings and README sections as appropriate.
- **No Secrets:** Never commit API keys, passwords, tokens, or other secrets.
  Use environment variables or configuration files that are listed in `.gitignore`.
- **Dependencies:** If adding new dependencies, update `requirements.txt` and
  document why the dependency is needed.

---

## Reporting Bugs

When reporting a bug, please include:

1. **Summary:** A clear, concise description of the bug.
2. **Steps to Reproduce:** Detailed steps to reproduce the behavior.
3. **Expected Behavior:** What you expected to happen.
4. **Actual Behavior:** What actually happened.
5. **Environment:** Operating system, Python version, relevant dependency versions.
6. **Logs/Screenshots:** Any relevant error messages, logs, or screenshots.

Use the "Bug Report" issue template if one is available.

---

## Requesting Features

When requesting a feature, please include:

1. **Problem Statement:** What problem does this feature solve?
2. **Proposed Solution:** How do you envision the feature working?
3. **Alternatives Considered:** Have you considered alternative approaches?
4. **Additional Context:** Any mockups, examples, or references.

Use the "Feature Request" issue template if one is available.

---

## Security Vulnerabilities

**DO NOT open a public issue for security vulnerabilities.** Please refer to our
[Security Policy](SECURITY.md) for responsible disclosure instructions.

---

## License

By contributing to AEGIS SUPERSTACK, you agree that your contributions will be
licensed under the same terms as the project. See the [LICENSE](LICENSE) file for
details. Note that commercial use requires a separate commercial license -- see
[COMMERCIAL_LICENSE.md](COMMERCIAL_LICENSE.md) for terms.

---

## Questions?

If you have questions about contributing, feel free to:

- Open a discussion on GitHub
- Email us at IRSTAXBYJORGE@GMAIL.COM

Thank you for helping make AEGIS SUPERSTACK better!

---

**Copyright (c) 2024-2026 Jorge Francisco Paredes (irstabyjorge). All rights reserved.**
