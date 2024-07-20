# Introduction
This repository demonstrates a setup for user authentication using LDAP combined with MFA in a Flask web application. The solution involves setting up an LDAP server with Docker, creating and managing users, and integrating an additional security layer using Time-based One-Time Passwords (TOTP) for MFA.

# Prerequisites
* Git
* Docker

# Directory Structure
```
LDAP-setup/
├── Dockerfile
├── docker-compose.yml
├── init.ldif
├── README.md
└── app/
    ├── templates/
    │   ├── login.html
    │   ├── setup_mfa.html
    │   ├── mfa.html
    │   └── welcome.html
    └── app.py
```
