# Security Policy

## Reporting a vulnerability

Please report security issues privately to security@stapel.dev. Do not open a
public issue for a suspected vulnerability.

Include a description, reproduction steps, and the affected version. We aim to
acknowledge reports within a few business days and will coordinate a fix and
disclosure timeline with you.

## Scope

`stapel-taskspecs` is a pure-Python schema library with no network, filesystem
mutation, or code-execution surface at runtime. The most relevant classes of
issue are:

- Schema definitions that accept clearly invalid artifacts or reject valid
  ones in a way that could mislead a consuming validator.
- Parsing behaviour (front matter / JSON) that could be abused for
  resource exhaustion.

Note: the library parses YAML front matter with `yaml.safe_load` only —
arbitrary object construction is never enabled.
