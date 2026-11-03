# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 1.0.x   | Yes       |

## Reporting a Vulnerability

If you discover a security vulnerability in localShare, please report it
privately before opening a public issue.

- Email: ahmedthebest31@gmail.com
- Subject: `[security] localShare: <short description>`

Include:
- A clear description of the issue
- Steps to reproduce
- Affected version(s)
- Any suggested mitigation

You will receive an acknowledgement within 72 hours. Once a fix is available,
a coordinated disclosure and release will be published. Please do not
disclose the issue publicly until a fix has been released.

## Security Notes

localShare binds a web server to `0.0.0.0` on the chosen port and shares the
selected folder with any device on the local network. Treat the shared folder
as publicly readable by anyone on that network unless password protection is
enabled. Do not share folders containing secrets or sensitive data.
