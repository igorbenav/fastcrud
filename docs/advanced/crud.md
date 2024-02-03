
# Advanced Use of FastCRUD

FastCRUD offers a flexible and powerful approach to handling CRUD operations in FastAPI applications, leveraging the SQLAlchemy ORM. Beyond basic CRUD functionality, FastCRUD provides advanced features like `allow_multiple` for updates and deletes, and support for advanced filters (e.g., less than, greater than). These features enable more complex and fine-grained data manipulation and querying capabilities.

## Allow Multiple Updates and Deletes

One of FastCRUD's advanced features is the ability to update or delete multiple records at once based on specified conditions. This is particularly useful for batch operations where you need to modify or remove several records that match certain criteria.

### Updating Multiple Records

To update multiple records, you can set the `allow_multiple=True` parameter in the `update` method. This allows FastCRUD to apply the update to all records matching the given filters.

```python
# Assuming setup for FastCRUD instance `item_crud` and SQLAlchemy async session `db`

# Update all items priced below $10 to a new price
await item_crud.update(
    db=db,
    object={"price": 9.99},
    allow_multiple=True,
    price__lt=10
)
```

### Deleting Multiple Records

Similarly, you can delete multiple records by using the `allow_multiple=True` parameter in the `delete` or `db_delete` method, depending on whether you're performing a soft or hard delete.

```python
# Soft delete all items not sold in the last year
await item_crud.delete(
    db=db,
    allow_multiple=True,
    last_sold__lt=datetime.datetime.now() - datetime.timedelta(days=365)
)
```

## Advanced Filters

FastCRUD supports advanced filtering options, allowing you to query records using operators such as greater than (`__gt`), less than (`__lt`), and their inclusive counterparts (`__gte`, `__lte`). These filters can be used in any method that retrieves or operates on records, including `get`, `get_multi`, `exists`, `count`, `update`, and `delete`.

### Using Advanced Filters

The following examples demonstrate how to use advanced filters for querying and manipulating data:

#### Fetching Records with Advanced Filters

```python
# Fetch items priced between $5 and $20
items = await item_crud.get_multi(
    db=db,
    price__gte=5,
    price__lte=20
)
```

#### Counting Records

```python
# Count items added in the last month
item_count = await item_crud.count(
    db=db,
    added_at__gte=datetime.datetime.now() - datetime.timedelta(days=30)
)
```

## Conclusion

The advanced features of FastCRUD, such as `allow_multiple` and support for advanced filters, empower developers to efficiently manage database records with complex conditions. By leveraging these capabilities, you can build more dynamic, robust, and scalable FastAPI applications that effectively interact with your data model.
