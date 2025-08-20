# Pili Documentation

This directory contains the Sphinx documentation for Pili, the Exercise Tracker Chatbot.

## Quick Start

### Prerequisites

1. Ensure you have the `Pili` conda environment activated:
   ```bash
   conda activate Pili
   ```

2. Install documentation dependencies:
   ```bash
   pip install -r ../requirements.txt
   ```

### Building Documentation

**Option 1: Using the build script (Recommended)**

```bash
# Build documentation
../scripts/build_docs.sh build

# Build and serve locally
../scripts/build_docs.sh serve

# Auto-build with live reload
../scripts/build_docs.sh auto
```

**Option 2: Using Makefile**

```bash
# Build HTML documentation
make html

# Serve locally
make serve

# Live reload development
make auto
```

**Option 3: Direct Sphinx commands**

```bash
# Build HTML
sphinx-build -b html . _build/html

# Serve locally
cd _build/html && python -m http.server 8080
```

## Documentation Structure

```
sphinx_docs/
├── conf.py                 # Sphinx configuration
├── index.rst               # Main documentation index
├── installation.rst        # Installation guide
├── quickstart.rst          # Quick start guide
├── configuration.rst       # Configuration reference
├── _static/                # Static assets (CSS, images)
├── _templates/             # Custom templates
├── architecture/           # Architecture documentation
├── user_guide/            # User guides
├── development/           # Development guides
├── integration/           # Integration guides
├── api/                   # API reference (auto-generated)
├── examples/              # Usage examples
└── _build/                # Generated documentation (git-ignored)
```

## Features

- **Auto-generated API documentation** using Sphinx AutoAPI
- **MyST Markdown support** for mixing .md and .rst files
- **Read the Docs theme** with custom styling
- **Copy button** for code blocks
- **Live reload** during development
- **Link checking** and spell checking
- **PDF generation** support

## Development Workflow

1. **Edit documentation files** (`.rst` or `.md`)
2. **Auto-build with live reload**:
   ```bash
   ../scripts/build_docs.sh auto
   ```
3. **View changes** at http://localhost:8080
4. **Check links and spelling**:
   ```bash
   ../scripts/build_docs.sh check
   ```

## Writing Documentation

### Adding New Pages

1. Create a new `.rst` file in the appropriate directory
2. Add it to the `toctree` in the relevant index file
3. Use the existing files as templates

### Documenting Code

The documentation automatically generates API references from docstrings in the source code. Use Google-style docstrings:

```python
def example_function(param1: str, param2: int) -> bool:
    """Brief description of the function.
    
    Args:
        param1: Description of param1
        param2: Description of param2
        
    Returns:
        Description of return value
        
    Raises:
        ValueError: When param2 is negative
    """
    pass
```

### Adding Examples

Add practical examples to `examples/` directory:
- Use real-world scenarios
- Include both curl commands and responses
- Show error handling

## Customization

### Theme Customization

Edit `_static/custom.css` for styling changes.

### Configuration

Edit `conf.py` for Sphinx configuration:
- Extensions
- Theme options
- AutoAPI settings
- Build options

## Deployment

### GitHub Pages

The documentation can be deployed to GitHub Pages:

1. Build documentation: `make html`
2. Copy `_build/html/*` to `docs/` directory in main branch
3. Enable GitHub Pages in repository settings

### Read the Docs

For Read the Docs deployment:

1. Connect your repository to Read the Docs
2. Set build directory to `sphinx_docs/`
3. Set Python version to 3.8+
4. Add `requirements.txt` path

## Troubleshooting

### Common Issues

**Build Errors**
- Check that all referenced files exist
- Verify toctree entries are correct
- Ensure proper indentation in `.rst` files

**Import Errors**
- Verify conda environment is activated
- Check that project code is importable
- Update Python path in `conf.py` if needed

**Theme Issues**
- Clear build cache: `make clean-all`
- Check custom CSS syntax
- Verify theme dependencies are installed

### Getting Help

- Check the [Sphinx documentation](https://www.sphinx-doc.org/)
- Review existing documentation files for examples
- Use `../scripts/build_docs.sh help` for available commands

## Contributing

When contributing to documentation:

1. Follow the existing structure and style
2. Test builds locally before committing
3. Use descriptive commit messages
4. Update this README if adding new features

---

**Happy documenting!** 📚✨ 