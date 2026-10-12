# Nuclio

Start the Nuclio dashboard (requires Docker):

```sh
docker compose up -d
```

The dashboard is available at http://localhost:8070. Stop it with:

```sh
docker compose down
```

## Functions

### runner

`nuclio/runner` is an ad hoc Python runner. It uses `uv` to run scripts and tools.

Deploy it with `nuctl` (the dashboard at http://localhost:8070 also works):

```sh
nuctl deploy --path nuclio/runner --project-name kangaroo
```

Run a Python script. Put any dependencies in a PEP 723 header:

```sh
curl -X POST <function-url> -d '{"code": "# /// script\n# dependencies = [\"requests\"]\n# ///\nimport requests\nprint(requests.get(\"https://example.com\").status_code)"}'
```

Run a packaged tool with `uvx`:

```sh
curl -X POST <function-url> -d '{"tool": "pycowsay", "args": ["moo"]}'
```

The response is JSON with `stdout`, `stderr` and `exit_code`. Scripts time out after 120 seconds.

**Warning:** anyone who can reach this function can run arbitrary code in its container. Do not expose it publicly.
