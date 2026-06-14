# Security Policy

## Scope

This repository is a **reference architecture** for educational use. It ships no
production credentials and, by default, makes no network calls — the core runs
entirely on the Python standard library with a deterministic offline model.

## Reporting a vulnerability

If you find a security issue (e.g. in the optional Vertex AI adapter, the safe
expression evaluator, or a dependency), please **do not open a public issue**.

Use GitHub's [private vulnerability reporting](https://docs.github.com/en/code-security/security-advisories/guidance-on-reporting-and-writing-information-about-vulnerabilities/privately-reporting-a-security-vulnerability)
(the **Security → Report a vulnerability** tab on this repo). I aim to acknowledge
reports within 5 business days.

## Notes for adopters

- The `calculator` tool uses a restricted AST walker — never replace it with `eval()`.
- Any tool that calls out or mutates state should be marked `side_effecting=True`
  so the human-in-the-loop gate can review it.
- Never commit a real `.env`; use `.env.example` as the template.
