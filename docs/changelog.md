# Changelog

All notable changes to Django Shield are documented here.

## [0.2.1] - 2024

### Fixed
- Minor bug fixes and improvements

## [0.2.0] - 2024

### Added
- **Class-based View Support**: `@guard` now works with Django CBVs
- **Expression Syntax**: Write inline permission checks like `'obj.author == user'`
- **guard.all()**: Require all rules to pass
- **guard.any()**: Require at least one rule to pass
- **Debug Mode**: Enable detailed permission logging with `DJANGO_SHIELD['DEBUG'] = True`
- **Comparison Operators**: `==`, `!=`, `>`, `<`, `>=`, `<=`
- **Boolean Operators**: `and`, `or`, `not`
- **List Membership**: `in` operator for checking list membership
- **Null Comparison**: Compare with `null` or `None`

### Changed
- Improved error messages for permission failures
- Better exception handling with detailed context

## [0.1.0] - 2024

### Added
- Initial release
- `@rule` decorator for defining permission rules
- `@guard` decorator for protecting function-based views
- Object-level permissions with `model` parameter
- Custom lookup fields with `lookup` and `lookup_field`
- Auto-inject objects with `inject` parameter
- `RuleRegistry` for managing rules
- `PermissionDenied` exception with context

## Roadmap

### 0.3.0 (Planned)
- Queryset filtering based on rules
- SQL compilation for database-level filtering

### 0.4.0 (Planned)
- Django REST Framework integration
- Serializer-level permissions

### 1.0.0 (Planned)
- Async view support
- Permission caching
- Production hardening
- Full test coverage across all Django versions

## Compatibility

| Django Shield | Python | Django |
|--------------|--------|--------|
| 0.2.x | 3.10+ | 4.2, 5.0, 5.1 |
| 0.1.x | 3.10+ | 4.2, 5.0, 5.1 |

## Upgrading

### From 0.1.x to 0.2.x

No breaking changes. All existing code continues to work.

New features are additive:
- Use expression syntax as an alternative to named rules
- Add `@guard` to class-based views
- Use `guard.all()` and `guard.any()` for multiple rules
