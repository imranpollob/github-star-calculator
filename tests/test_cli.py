import io
import sys
import unittest
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError, URLError

from gitstar.core import (
    VERSION,
    build_parser,
    fetch,
    get_star_symbol,
    main,
)


class TestGitstarCLI(unittest.TestCase):
    def test_parser_basic(self):
        parser = build_parser()
        args = parser.parse_args(["octocat"])
        self.assertEqual(args.username, "octocat")
        self.assertIsNone(args.pos_limit)
        self.assertIsNone(args.limit)
        self.assertIsNone(args.token)

    def test_parser_positional_limit(self):
        parser = build_parser()
        args = parser.parse_args(["octocat", "5"])
        self.assertEqual(args.username, "octocat")
        self.assertEqual(args.pos_limit, 5)

    def test_parser_flag_limit(self):
        parser = build_parser()
        args = parser.parse_args(["octocat", "-l", "10"])
        self.assertEqual(args.username, "octocat")
        self.assertEqual(args.limit, 10)

    def test_parser_token(self):
        parser = build_parser()
        args = parser.parse_args(["octocat", "--token", "ghp_secret"])
        self.assertEqual(args.token, "ghp_secret")

    def test_get_star_symbol(self):
        symbol = get_star_symbol()
        self.assertIn(symbol, ("⭐️", "★", "*"))

    def test_main_no_args_shows_help(self):
        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            with self.assertRaises(SystemExit) as cm:
                main([])
            self.assertEqual(cm.exception.code, 0)
            self.assertIn("Calculate the total stars", mock_stdout.getvalue())

    @patch("gitstar.core.fetch")
    def test_main_success(self, mock_fetch):
        # Mock user info and repos
        mock_fetch.side_effect = [
            {"public_repos": 2},
            [
                {"html_url": "https://github.com/test/repo1", "stargazers_count": 25},
                {"html_url": "https://github.com/test/repo2", "stargazers_count": 10},
            ],
        ]

        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            main(["testuser"])
            output = mock_stdout.getvalue()
            self.assertIn("Total", output)
            self.assertIn("35", output)
            self.assertIn("https://github.com/test/repo1", output)
            self.assertIn("25", output)
            self.assertIn("https://github.com/test/repo2", output)
            self.assertIn("10", output)

    @patch("gitstar.core.fetch")
    def test_main_with_limit(self, mock_fetch):
        mock_fetch.side_effect = [
            {"public_repos": 3},
            [
                {"html_url": "https://github.com/test/repo1", "stargazers_count": 100},
                {"html_url": "https://github.com/test/repo2", "stargazers_count": 50},
                {"html_url": "https://github.com/test/repo3", "stargazers_count": 10},
            ],
        ]

        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            main(["testuser", "1"])
            output = mock_stdout.getvalue()
            self.assertIn("Total", output)
            self.assertIn("160", output)
            self.assertIn("https://github.com/test/repo1", output)
            self.assertNotIn("https://github.com/test/repo2", output)
            self.assertNotIn("https://github.com/test/repo3", output)

    @patch("gitstar.core.fetch")
    def test_main_no_public_repos(self, mock_fetch):
        mock_fetch.return_value = {"public_repos": 0}

        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            with self.assertRaises(SystemExit) as cm:
                main(["emptyuser"])
            self.assertEqual(cm.exception.code, 0)
            self.assertIn("does not have any public repositories", mock_stdout.getvalue())

    @patch("gitstar.core.urlopen")
    def test_fetch_user_not_found(self, mock_urlopen):
        err = HTTPError(
            url="https://api.github.com/users/nonexistent",
            code=404,
            msg="Not Found",
            hdrs={},
            fp=io.BytesIO(b"{}"),
        )
        mock_urlopen.side_effect = err

        with patch("sys.stderr", new_callable=io.StringIO) as mock_stderr:
            with self.assertRaises(SystemExit) as cm:
                fetch("users/nonexistent")
            self.assertEqual(cm.exception.code, 1)
            self.assertIn("not found", mock_stderr.getvalue())

    @patch("gitstar.core.urlopen")
    def test_fetch_rate_limit_exceeded(self, mock_urlopen):
        headers = {
            "x-ratelimit-remaining": "0",
            "x-ratelimit-reset": "1700000000",
        }
        err = HTTPError(
            url="https://api.github.com/users/ratelimited",
            code=403,
            msg="Forbidden",
            hdrs=headers,
            fp=io.BytesIO(b"{}"),
        )
        mock_urlopen.side_effect = err

        with patch("sys.stderr", new_callable=io.StringIO) as mock_stderr:
            with self.assertRaises(SystemExit) as cm:
                fetch("users/ratelimited")
            self.assertEqual(cm.exception.code, 1)
            stderr_val = mock_stderr.getvalue()
            self.assertIn("rate limit exceeded", stderr_val)
            self.assertIn("Tip:", stderr_val)

    @patch("gitstar.core.urlopen")
    def test_fetch_network_error(self, mock_urlopen):
        mock_urlopen.side_effect = URLError("DNS lookup failed")

        with patch("sys.stderr", new_callable=io.StringIO) as mock_stderr:
            with self.assertRaises(SystemExit) as cm:
                fetch("users/test")
            self.assertEqual(cm.exception.code, 1)
            self.assertIn("Network connection failed", mock_stderr.getvalue())


if __name__ == "__main__":
    unittest.main()

