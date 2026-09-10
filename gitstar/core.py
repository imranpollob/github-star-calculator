import argparse
import datetime
import json
import math
import os
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

VERSION = "1.1.0"


def configure_terminal_encoding():
    """Ensure standard output streams handle UTF-8 without crashing on Windows."""
    if sys.platform == "win32":
        for stream in (sys.stdout, sys.stderr):
            if hasattr(stream, "reconfigure"):
                try:
                    stream.reconfigure(encoding="utf-8", errors="replace")
                except Exception:
                    pass


def get_star_symbol() -> str:
    """Return a star symbol compatible with the current terminal encoding."""
    for symbol in ("⭐️", "★", "*"):
        try:
            encoding = getattr(sys.stdout, "encoding", None) or "utf-8"
            symbol.encode(encoding)
            return symbol
        except (UnicodeEncodeError, LookupError):
            continue
    return "*"


def fetch(endpoint: str, token: str = None):
    """Fetch JSON from GitHub API with proper headers, timeout, and error handling."""
    url = f"https://api.github.com/{endpoint.lstrip('/')}"
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": f"gitstar/{VERSION}",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    request = Request(url, headers=headers)

    try:
        with urlopen(request, timeout=15) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as e:
        try:
            e.close()
        except Exception:
            pass
        if e.code == 404:
            print(f"Error: GitHub user or organization not found.", file=sys.stderr)
        elif e.code == 403:
            reset_time = e.headers.get("x-ratelimit-reset")
            if reset_time:
                try:
                    reset_dt = datetime.datetime.fromtimestamp(
                        int(reset_time), tz=datetime.timezone.utc
                    )
                    reset_str = reset_dt.strftime("%Y-%m-%d %H:%M:%S UTC")
                except Exception:
                    reset_str = reset_time
                print(
                    f"Error: GitHub API rate limit exceeded.\n"
                    f"Rate limit resets at: {reset_str}\n"
                    f"Tip: Provide a GitHub token using --token or the GITHUB_TOKEN environment variable.",
                    file=sys.stderr,
                )
            else:
                print(
                    f"Error: Access forbidden (HTTP 403).\n"
                    f"Reason: {e.reason}\n"
                    f"Tip: If you hit the rate limit, provide a GitHub token using --token or GITHUB_TOKEN.",
                    file=sys.stderr,
                )
        elif e.code == 401:
            print(
                "Error: Unauthorized (HTTP 401). Please check your GitHub token.",
                file=sys.stderr,
            )
        else:
            print(f"Error: GitHub API request failed ({e.code} {e.reason}).", file=sys.stderr)
        sys.exit(1)
    except URLError as e:
        print(
            f"Error: Network connection failed ({e.reason}). Please check your internet connection.",
            file=sys.stderr,
        )
        sys.exit(1)
    except TimeoutError:
        print("Error: Request timed out while connecting to GitHub.", file=sys.stderr)
        sys.exit(1)


def build_parser() -> argparse.ArgumentParser:
    """Build command-line argument parser."""
    parser = argparse.ArgumentParser(
        prog="gitstar",
        description="Calculate the total stars earned by a GitHub user or organization.",
    )
    parser.add_argument(
        "username",
        nargs="?",
        default=None,
        help="GitHub username or organization",
    )
    parser.add_argument(
        "pos_limit",
        nargs="?",
        type=int,
        default=None,
        metavar="limit",
        help="Number of top repositories to display (positional shorthand)",
    )
    parser.add_argument(
        "-l",
        "--limit",
        type=int,
        default=None,
        help="Number of top repositories to display",
    )
    parser.add_argument(
        "-t",
        "--token",
        type=str,
        default=None,
        help="GitHub Personal Access Token (defaults to GITHUB_TOKEN or GH_TOKEN environment variable)",
    )
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"%(prog)s {VERSION}",
    )
    return parser


def main(argv=None):
    configure_terminal_encoding()
    parser = build_parser()

    if argv is None:
        argv = sys.argv[1:]

    # Show friendly help when invoked with no arguments
    if len(argv) == 0:
        parser.print_help()
        sys.exit(0)

    args = parser.parse_args(argv)

    if not args.username:
        parser.print_help()
        sys.exit(0)

    # Determine limit (flag has priority over positional shorthand)
    limit = args.limit if args.limit is not None else args.pos_limit
    if limit is not None and limit < 0:
        parser.error("Limit must be a non-negative integer.")

    # Determine token: CLI flag -> GITHUB_TOKEN -> GH_TOKEN
    token = (
        args.token
        or os.environ.get("GITHUB_TOKEN")
        or os.environ.get("GH_TOKEN")
    )

    username = args.username.strip()
    user = fetch(f"users/{quote(username)}", token=token)

    public_repos = user.get("public_repos", 0)
    if not public_repos:
        print(f"'{username}' does not have any public repositories.")
        sys.exit(0)

    pages = math.ceil(public_repos / 100)
    total_stars = 0
    repo_star_map = {}
    highest_name = 0

    for page in range(1, pages + 1):
        repos = fetch(
            f"users/{quote(username)}/repos?per_page=100&page={page}",
            token=token,
        )
        if not repos:
            break

        for repo in repos:
            repo_url = repo.get("html_url", repo.get("name", "unknown"))
            stars = repo.get("stargazers_count", 0)
            repo_star_map[repo_url] = stars
            total_stars += stars
            highest_name = max(highest_name, len(repo_url))

    star_symbol = get_star_symbol()
    print(f"Total {star_symbol} {total_stars}")

    if limit != 0 and repo_star_map:
        sorted_repos = sorted(
            repo_star_map.items(), key=lambda x: x[1], reverse=True
        )
        if limit is not None:
            sorted_repos = sorted_repos[:limit]

        for repo, stars in sorted_repos:
            print(f"{repo:<{highest_name}}  {star_symbol} {stars}")


if __name__ == "__main__":
    main()
