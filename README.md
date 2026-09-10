# Gitstar

[![PyPI version](https://img.shields.io/pypi/v/gitstar.svg)](https://pypi.org/project/gitstar/)
[![Python versions](https://img.shields.io/pypi/pyversions/gitstar.svg)](https://pypi.org/project/gitstar/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A fast, lightweight, zero-dependency command-line tool to calculate the total number of stars earned by any GitHub user or organization.

---

## Features

- **Fast & Zero Dependencies**: Built entirely with Python's standard library. No external runtime dependencies.
- **Cross-Platform**: Full support for Linux, macOS, and Windows (with safe terminal encoding fallbacks).
- **Authentication & Rate-Limit Friendly**: Supports GitHub Personal Access Tokens (`--token` or `GITHUB_TOKEN` / `GH_TOKEN` environment variables) to bypass the unauthenticated 60 requests/hour limit.
- **Informative Output**: Clean tabular layout ranking repositories by stars.

---

## Installation

Install via pip:

```bash
pip install gitstar
```

Or upgrade to the latest version:

```bash
pip install --upgrade gitstar
```

---

## Usage

### Basic Usage

Find the total stars for any GitHub user or organization:

```bash
gitstar <username>
```

Example:

```bash
gitstar torvalds
```

### Limiting Results

Display only the top $N$ starred repositories:

```bash
# Using positional shorthand:
gitstar torvalds 5

# Or using the -l / --limit flag:
gitstar torvalds --limit 5
```

### Output Example

```text
Total ⭐️ 234120
https://github.com/torvalds/linux       ⭐️ 186400
https://github.com/torvalds/subsurface  ⭐️ 3150
https://github.com/torvalds/pesconvert  ⭐️ 285
```

---

## Authentication & Rate Limits

By default, unauthenticated GitHub API requests are limited to **60 requests per hour** per IP address.

To increase your limit to **5,000 requests per hour**, provide a GitHub Personal Access Token using either:

1. **Environment Variable** (recommended):
   ```bash
   export GITHUB_TOKEN="ghp_your_token_here"
   gitstar torvalds
   ```
   *(On Windows PowerShell: `$env:GITHUB_TOKEN="ghp_your_token_here"`)*

2. **CLI Option**:
   ```bash
   gitstar torvalds --token ghp_your_token_here
   ```

---

## CLI Options Reference

```text
usage: gitstar [-h] [-l LIMIT] [-t TOKEN] [-v] [username] [limit]

Calculate the total stars earned by a GitHub user or organization.

positional arguments:
  username           GitHub username or organization
  limit              Number of top repositories to display (positional shorthand)

options:
  -h, --help         show this help message and exit
  -l, --limit LIMIT  Number of top repositories to display
  -t, --token TOKEN  GitHub Personal Access Token (defaults to GITHUB_TOKEN or GH_TOKEN)
  -v, --version      show program's version number and exit
```

---

## License

This project is licensed under the [MIT License](LICENSE).