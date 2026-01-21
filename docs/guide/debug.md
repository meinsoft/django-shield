# Debug Mode

Debug mode shows detailed logs of permission checks. Use it during development to understand why permissions pass or fail.

## Enabling Debug Mode

Add to your `settings.py`:

```python
DJANGO_SHIELD = {
    'DEBUG': True
}
```

Only enable this in development. Disable in production.

## What Gets Logged

When debug mode is enabled, every permission check logs:

1. The rule or expression being checked
2. User information (username, ID)
3. Object information (if any)
4. The result (ALLOWED or DENIED)

## Log Output

Example output when checking permissions:

```
[Django Shield] Checking: is_author
[Django Shield] User: john (id=1)
[Django Shield] Object: Post "My First Post" (id=42)
[Django Shield] Result: ALLOWED
```

When permission is denied:

```
[Django Shield] Checking: is_admin
[Django Shield] User: jane (id=2)
[Django Shield] Object: None
[Django Shield] Result: DENIED
```

## Multiple Rules

With `guard.all()`:

```
[Django Shield] Checking: is_authenticated
[Django Shield] User: john (id=1)
[Django Shield] Object: None
[Django Shield] Result: ALLOWED
[Django Shield] Checking: is_verified
[Django Shield] User: john (id=1)
[Django Shield] Object: None
[Django Shield] Result: DENIED
```

With `guard.any()`:

```
[Django Shield] Checking: is_owner
[Django Shield] User: john (id=1)
[Django Shield] Object: Document "Report" (id=5)
[Django Shield] Result: DENIED
[Django Shield] Checking: is_admin
[Django Shield] User: john (id=1)
[Django Shield] Object: Document "Report" (id=5)
[Django Shield] Result: ALLOWED
```

## Environment-based Configuration

Enable debug mode only in development:

```python
# settings.py
import os

DJANGO_SHIELD = {
    'DEBUG': os.environ.get('DJANGO_SHIELD_DEBUG', 'false').lower() == 'true'
}
```

Or use Django's DEBUG setting:

```python
# settings.py
DJANGO_SHIELD = {
    'DEBUG': DEBUG  # Uses Django's DEBUG setting
}
```

## Tips for Debugging

### 1. Check User Attributes

If permissions fail unexpectedly, log user attributes:

```python
@rule
def is_verified(user):
    print(f"User verified: {user.email_verified}")  # Debug
    return user.email_verified
```

### 2. Check Object State

Verify the object has expected values:

```python
@rule
def is_author(user, post):
    print(f"Post author: {post.author}, User: {user}")  # Debug
    return post.author == user
```

### 3. Test Rules Directly

Test rules without HTTP requests:

```python
from myapp.permissions import is_author
from myapp.models import Post
from django.contrib.auth import get_user_model

User = get_user_model()
user = User.objects.get(pk=1)
post = Post.objects.get(pk=42)

# Check the rule directly
result = is_author.predicate(user, post)
print(f"is_author: {result}")
```

### 4. Use Django Shell

Test permissions interactively:

```bash
python manage.py shell
```

```python
from django_shield import RuleRegistry

rule = RuleRegistry.get('is_author')
print(rule.check(user, post))
```

## Production Considerations

Always disable debug mode in production:

1. **Security**: Logs may contain sensitive information
2. **Performance**: Logging adds overhead
3. **Log volume**: High traffic creates massive logs

```python
# settings/production.py
DJANGO_SHIELD = {
    'DEBUG': False
}
```

Or ensure the setting doesn't exist:

```python
# No DJANGO_SHIELD setting = debug disabled
```
