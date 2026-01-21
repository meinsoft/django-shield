# Installation

## Requirements

- Python 3.10 or higher
- Django 4.2 or higher

## Install from GitHub

```bash
pip install git+https://github.com/meinsoft/django-shield.git
```

## Install from Source

Clone the repository and install in development mode:

```bash
git clone https://github.com/meinsoft/django-shield.git
cd django-shield
pip install -e .
```

## Verify Installation

Open a Python shell and check the version:

```python
import django_shield
print(django_shield.__version__)
```

You should see the version number (e.g., `0.2.1`).

## No Configuration Needed

Django Shield works out of the box. You don't need to:

- Add it to `INSTALLED_APPS`
- Run migrations
- Configure any settings

Just import and use:

```python
from django_shield import rule, guard
```

## Optional: Enable Debug Mode

To see detailed permission logs during development, add this to your `settings.py`:

```python
DJANGO_SHIELD = {
    'DEBUG': True
}
```

See [Debug Mode](../guide/debug.md) for more details.

## Next Steps

Continue to the [Quick Start](quickstart.md) guide to create your first protected view.
