# Contributing to PyANTDisplay

Thank you for your interest in contributing to PyANTDisplay! This document provides guidelines for contributing to the project.

## Development Setup

1. **Fork and clone the repository:**
   ```bash
   git clone https://github.com/your-username/pyAntDisplay.git
   cd pyAntDisplay
   ```

2. **Set up the development environment:**
   ```bash
   # Linux/macOS
   ./setup.sh
   
   # Windows
   setup.bat
   ```

3. **Install development dependencies:**
   ```bash
   source .venv/bin/activate  # Linux/macOS
   # or
   .venv\Scripts\activate.bat  # Windows
   
   pip install -r requirements-dev.txt
   ```

4. **Set up pre-commit hooks:**
   ```bash
   pre-commit install
   ```

## Development Workflow

1. **Create a feature branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes and write tests:**
   - Add tests for new functionality in the `tests/` directory
   - Ensure all tests pass: `pytest`
   - Check code coverage: `pytest --cov=src`

3. **Run code quality checks:**
   ```bash
   # Format code
   black src tests
   
   # Lint code
   flake8 src tests
   
   # Type checking
   mypy src
   ```

4. **Commit your changes:**
   ```bash
   git add .
   git commit -m "Add your descriptive commit message"
   ```

5. **Push and create a pull request:**
   ```bash
   git push origin feature/your-feature-name
   ```

## Code Style

- Follow PEP 8 style guidelines
- Use Black for code formatting (line length: 88)
- Write type hints for all functions
- Add docstrings for all public functions and classes
- Keep functions small and focused

## Testing

- Write unit tests for all new functionality
- Use pytest for testing
- Mock external dependencies (USB, ANT+ hardware)
- Aim for high test coverage (>90%)
- Test edge cases and error conditions

## Documentation

- Update README.md for user-facing changes
- Add docstrings for new functions/classes
- Update configuration examples if needed
- Document any new dependencies

## Pull Request Guidelines

- Provide a clear description of the changes
- Reference any related issues
- Ensure all tests pass
- Include screenshots/examples if relevant
- Keep pull requests focused and atomic

## Reporting Issues

- Use the GitHub issue tracker
- Provide clear reproduction steps
- Include system information (OS, Python version)
- Specify ANT+ device types if relevant

## Adding New Device Support

When adding support for new ANT+ device types:

1. Create a new module in `src/pyantdisplay/`
2. Follow the existing pattern (HeartRateMonitor, BikeSensor)
3. Add device type to the scanner's supported types
4. Write comprehensive tests
5. Update documentation and examples

## Release Process

1. Update version in `pyproject.toml`
2. Update CHANGELOG.md
3. Create a git tag: `git tag v1.0.0`
4. Push tag: `git push origin v1.0.0`
5. GitHub Actions will handle the release

## Questions?

Feel free to open an issue for questions or discussions about contributing.