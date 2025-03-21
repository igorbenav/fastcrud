# Advanced Filtering

The `_parse_filters` method in FastCRUD supports complex filtering operations including OR and NOT conditions.

## Basic Usage

Filters are specified as keyword arguments in the format `field_name__operator=value`:

```python
# Simple equality filter
results = await crud.get_multi(db, name="John")

# Comparison operators
results = await crud.get_multi(db, age__gt=18)
```

## OR Operations

Use the `__or` suffix to apply multiple conditions to the same field with OR logic:

```python
# Find users aged under 18 OR over 65
results = await crud.get_multi(
    db,
    age__or={
        "lt": 18,
        "gt": 65
    }
)
# Generates: WHERE age < 18 OR age > 65
```

## NOT Operations

Use the `__not` suffix to negate multiple conditions on the same field:

```python
# Find users NOT aged 20 AND NOT between 30-40
results = await crud.get_multi(
    db,
    age__not={
        "eq": 20,
        "between": (30, 40)
    }
)
# Generates: WHERE NOT age = 20 AND NOT (age BETWEEN 30 AND 40)
```

## Supported Operators

- Comparison: `eq`, `gt`, `lt`, `gte`, `lte`, `ne`
- Null checks: `is`, `is_not`
- Text matching: `like`, `notlike`, `ilike`, `notilike`, `startswith`, `endswith`, `contains`, `match`
- Collections: `in`, `not_in`, `between`
- Logical: `or`, `not`

## Examples

```python
# Complex age filtering
results = await crud.get_multi(
    db,
    age__or={
        "between": (20, 30),
        "eq": 18
    },
    status__not={
        "in": ["inactive", "banned"]
    }
)

# Text search with OR conditions
results = await crud.get_multi(
    db,
    name__or={
        "startswith": "A",
        "endswith": "smith"
    }
)
```

## Error Handling

- Invalid column names raise `ValueError`
- Invalid operators are ignored
- Invalid value types for operators (e.g., non-list for `between`) raise `ValueError`