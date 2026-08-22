# Contributing

Thanks for your interest in improving landlab-triangle! Contributions of all
kinds are welcome: bug reports, documentation, and new features.

By participating in this project, you agree to abide by our
[Code of Conduct](CODE-OF-CONDUCT.md).

## Reporting bugs and requesting features

Open an issue on the
[issue tracker](https://github.com/ethan-pierce/landlab-triangle/issues).

For bug reports, please include:

- a minimal example that reproduces the problem,
- the `triangle_opts` string you passed,
- the full traceback, and
- your operating system and Python version.

If you're not sure whether something is a bug, open an issue and ask. See also
[SUPPORT.md](SUPPORT.md).

## Setting up a development environment

This project uses [pixi](https://pixi.sh) to manage environments. After cloning:

```bash
pixi install
pixi run -e dev pre-commit install
```

`pre-commit install` wires up the ruff hooks so linting and formatting run
automatically on each commit.

## Making changes

1. Create a branch for your work (`git switch -c my-feature`).
2. Make your change, keeping commits focused.
3. Match the surrounding code style. Formatting and linting are handled by
   [ruff](https://docs.astral.sh/ruff/):

   ```bash
   pixi run -e dev format      # apply formatting
   pixi run -e dev lint-fix    # apply lint autofixes
   ```

4. Add or update tests for your change, and run the full suite:

   ```bash
   pixi run -e test pytest
   ```

5. Update the README or docstrings if you've changed behavior, and add an entry
   to [CHANGES.md](CHANGES.md) under the unreleased section.

## Submitting a pull request

- Push your branch and open a pull request against `main`.
- Describe what the change does and why; link any related issue.
- Make sure CI is green. The same ruff checks run in
  [continuous integration](.github/workflows/lint.yml).
- A maintainer will review your PR. Once merged, you'll be added to
  [CREDITS.md](CREDITS.md).

## Code style

- Python 3.13+, formatted and linted with ruff (line length 100).
- Generally follows the Google Python [style guide](https://google.github.io/styleguide/pyguide.html)
