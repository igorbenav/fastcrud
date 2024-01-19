<p align="center">
  <a href="https://github.com/igorbenav/fastcrud">
    <img src="assets/fastcrud.png" alt="FastCRUD written in white with a drawing of a gear and inside this gear a bolt." width="45%" height="auto">
  </a>
</p>
<p align="center" markdown=1>
  <i>Powerful CRUD methods and automatic endpoint creation for FastAPI.</i>
</p>
<p align="center" markdown=1>
<a href="https://github.com/igorbenav/fastcrud/actions/workflows/python-versions.yml">
  <img src="https://github.com/igorbenav/fastcrud/actions/workflows/python-versions.yml/badge.svg" alt="Python Versions"/>
</a>
<a href="https://github.com/igorbenav/fastcrud/actions/workflows/tests.yml">
  <img src="https://github.com/igorbenav/fastcrud/actions/workflows/tests.yml/badge.svg" alt="Tests"/>
</a>
</p>
<hr>
<p align="justify">
<b>FastCRUD</b> is a Python package for <b>FastAPI</b>, offering robust async CRUD operations and flexible endpoint creation utilities, streamlined through advanced features like <b>auto-detected join</b> conditions, <b>dynamic sorting</b>, and offset and cursor <b>pagination</b>.
</p>
<p><b>Documentation: 🚧 Coming Soon 🚧</b></p>
<hr>
<h2>Features</h2>

- ⚡️ **Fully Async**: Leverages Python's async capabilities for non-blocking database operations.
- 📚 **SQLAlchemy 2.0**: Works with the latest SQLAlchemy version for robust database interactions.
- 🦾 **Powerful CRUD Functionality**: Full suite of efficient CRUD operations with support for joins.
- ⚙️ **Dynamic Query Building**: Supports building complex queries dynamically, including filtering, sorting, and pagination.
- 🤝 **Advanced Join Operations**: Facilitates performing SQL joins with other models with automatic join condition detection.
- 📖 **Built-in Offset Pagination**: Comes with ready-to-use offset pagination.
- ➤ **Cursor-based Pagination**: Implements efficient pagination for large datasets, ideal for infinite scrolling interfaces.
- 🤸‍♂️ **Modular and Extensible**: Designed for easy extension and customization to fit your requirements.
- 🛣️ **Auto-generated Endpoints**: Streamlines the process of adding CRUD endpoints with custom dependencies and configurations.


<h2>Requirements</h2>
<p>Before installing FastCRUD, ensure you have the following prerequisites:</p>
<ul>
  <li><b>Python:</b> Version 3.9 or newer.</li>
  <li><b>FastAPI:</b> FastCRUD is built to work with FastAPI, so having FastAPI in your project is essential.</li>
  <li><b>SQLAlchemy:</b> Version 2.0.21 or newer. FastCRUD uses SQLAlchemy for database operations.</li>
  <li><b>Pydantic:</b> Version 2.4.1 or newer. FastCRUD leverages Pydantic models for data validation and serialization.</li>
  <li><b>SQLAlchemy-Utils:</b> Optional, but recommended for additional SQLAlchemy utilities.</li>
</ul>

<h2>Installing</h2>

🚧 Coming Soon 🚧
<h2>Usage</h2>

FastCRUD offers two primary ways to use its functionalities: 

1. By using `crud_router` for automatic endpoint creation.
2. By integrating `FastCRUD` directly into your FastAPI endpoints for more control.

Below are examples demonstrating both approaches:

<h3>Using crud_router for Automatic Endpoint Creation</h3>

Here's a quick example to get you started:

<h4>Define Your Model and Schema</h4>

```python
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import declarative_base
from pydantic import BaseModel

Base = declarative_base()

class Item(Base):
    __tablename__ = 'items'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    description = Column(String)

class ItemCreateSchema(BaseModel):
    name: str
    description: str

class ItemUpdateSchema(BaseModel):
    name: str
    description: str

```

<h4>Set Up FastAPI and FastCRUD</h4>

```python
from fastapi import FastAPI
from fastcrud import FastCRUD, crud_router
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Database setup (Async SQLAlchemy)
DATABASE_URL = "sqlite+aiosqlite:///./test.db"
engine = create_async_engine(DATABASE_URL, echo=True)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# FastAPI app
app = FastAPI()

# CRUD operations setup
crud = FastCRUD(Item)

# CRUD router setup
item_router = crud_router(
    session=async_session,
    model=Item,
    crud=crud,
    create_schema=ItemCreateSchema,
    update_schema=ItemUpdateSchema,
    path="/items",
    tags=["Items"]
)

app.include_router(item_router)

```

<h3>Using FastCRUD in User-Defined FastAPI Endpoints</h3>

For more control over your endpoints, you can use FastCRUD directly within your custom FastAPI route functions. Here's an example:

```python
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from fastcrud import FastCRUD
from yourapp.models import Item
from yourapp.schemas import ItemCreateSchema, ItemUpdateSchema

app = FastAPI()

# Assume async_session is already set up as per the previous example

# Instantiate FastCRUD with your model
item_crud = FastCRUD(Item)

@app.post("/custom/items/")
async def create_item(item_data: ItemCreateSchema, db: AsyncSession = Depends(async_session)):
    return await item_crud.create(db, item_data)

@app.get("/custom/items/{item_id}")
async def read_item(item_id: int, db: AsyncSession = Depends(async_session)):
    item = await item_crud.get(db, id=item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

# You can add more routes for update and delete operations in a similar fashion
```

In this example, we define custom endpoints for creating and reading items using FastCRUD directly, providing more flexibility in how the endpoints are structured and how the responses are handled.

<h2>Understanding FastCRUD Methods</h2>
<p>FastCRUD offers a comprehensive suite of methods for CRUD operations, each designed to handle different aspects of database interactions efficiently.</p>

<h3>1. Create</h3>

```python
create(
    db: AsyncSession, 
    object: CreateSchemaType
) -> ModelType
```

<p><b>Purpose</b>: To create a new record in the database.</p>
<p><b>Usage Example</b>:</p>

```python
# creates an item with name 'New Item'
new_item = await item_crud.create(db, ItemCreateSchema(name="New Item"))
```

<h3>2. Get</h3>

```python
get(
    db: AsyncSession, 
    schema_to_select: Optional[Union[type[BaseModel], list]] = None, 
    **kwargs: Any
) -> Optional[dict]
```
<p><b>Purpose</b>: To fetch a single record based on filters, with an option to select specific columns using a Pydantic schema.</p>
<p><b>Usage Example</b>:</p>

```python
# fetches the item with item_id as its id
item = await item_crud.get(db, id=item_id)
```

<h3>3. Exists</h3>

```python
exists(
    db: AsyncSession, 
    **kwargs: Any
) -> bool
```
<p><b>Purpose</b>: To check if a record exists based on provided filters.</p>
<p><b>Usage Example</b>:</p>

```python
# checks whether an item with name 'Existing Item' exists
exists = await item_crud.exists(db, name="Existing Item")
```

<h3>4. Count</h3>

```python
count(
    db: AsyncSession, 
    **kwargs: Any
) -> int
```
<p><b>Purpose</b>: To count the number of records matching provided filters.</p>
<p><b>Usage Example</b>:</p>

```python
# counts the number of items with the 'Books' category
count = await item_crud.count(db, category="Books")
```

<h3>5. Get Multi</h3>

```python
get_multi(
    db: AsyncSession, 
    offset: int = 0, 
    limit: int = 100, 
    schema_to_select: Optional[type[BaseModel]] = None, 
    sort_columns: Optional[Union[str, list[str]]] = None, 
    sort_orders: Optional[Union[str, list[str]]] = None, 
    return_as_model: bool = False, 
    **kwargs: Any
) -> dict[str, Any]</
```
<p><b>Purpose</b>: To fetch multiple records with optional sorting, pagination, and model conversion.</p>
<p><b>Usage Example</b>:</p>

```python
# fetches a subset of 5 items, starting from the 11th item in the database.
items = await item_crud.get_multi(db, offset=10, limit=5)
```

<h3>6. Update</h3>

```python
update(
    db: AsyncSession, 
    object: Union[UpdateSchemaType, dict[str, Any]], 
    **kwargs: Any
) -> None
```
<p><b>Purpose</b>: To update an existing record in the database.</p>
<p><b>Usage Example</b>:</p>

```python
# updates the description of the item with item_id as its id
await item_crud.update(db, ItemUpdateSchema(description="Updated"), id=item_id)
```

<h3>7. Delete</h3>

```python
delete(
    db: AsyncSession, 
    db_row: Optional[Row] = None, 
    **kwargs: Any
) -> None
```
<p><b>Purpose</b>: To delete a record from the database, with support for soft delete.</p>
<p><b>Usage Example</b>:</p>

```python
# deletes the item with item_id as its id
# it performs a soft_delete if the model has the 'is_deleted' column
await item_crud.delete(db, id=item_id)
```

<h3>8. Hard Delete</h3>

```python
db_delete(
    db: AsyncSession, 
    **kwargs: Any
) -> None
```
<p><b>Purpose</b>: To hard delete a record from the database.</p>
<p><b>Usage Example</b>:</p>

```python
# hard deletes the item with item_id as its id
await item_crud.db_delete(db, id=item_id)
```

<h3>Advanced Methods for Complex Queries and Joins</h3>
<p>FastCRUD also provides advanced methods for more complex operations like querying multiple records with filters, sorting, pagination (<code>get_multi</code>), handling join operations (<code>get_joined</code>, <code>get_multi_joined</code>), and cursor-based pagination (<code>get_multi_by_cursor</code>).</p>

<h2>Advanced Methods for Complex Queries and Joins</h2>
<p>FastCRUD extends its functionality with advanced methods tailored for complex query operations and handling joins. These methods cater to specific use cases where more sophisticated data retrieval and manipulation are required.</p>

<h3>1. Get Multi</h3>

```python
get_multi(
    db: AsyncSession, 
    offset: int = 0, 
    limit: int = 100, 
    schema_to_select: Optional[type[BaseModel]] = None, 
    sort_columns: Optional[Union[str, list[str]]] = None, 
    sort_orders: Optional[Union[str, list[str]]] = None, 
    return_as_model: bool = False, 
    **kwargs: Any
) -> dict[str, Any]
```
<p><b>Purpose</b>: To fetch multiple records based on specified filters, with options for sorting and pagination. Ideal for listing views and tables.</p>
<p><b>Usage Example</b>:</p>

```python
# gets the first 10 items sorted by 'name' in ascending order
items = await item_crud.get_multi(db, offset=0, limit=10, sort_columns=['name'], sort_orders=['asc'])
```
<h3>2. Get Joined</h3>

```python
get_joined(
    db: AsyncSession, 
    join_model: type[ModelType], 
    join_prefix: Optional[str] = None, 
    join_on: Optional[Union[Join, None]] = None, 
    schema_to_select: Optional[Union[type[BaseModel], list]] = None, 
    join_schema_to_select: Optional[Union[type[BaseModel], list]] = None, 
    join_type: str = "left", **kwargs: Any
) -> Optional[dict[str, Any]]
```
<p><b>Purpose</b>: To fetch a single record while performing a join operation with another model. This method is useful when data from related tables is needed.</p>
<p><b>Usage Example</b>:</p>

```python
# fetches order details for a specific order by joining with the Customer table, 
# selecting specific columns as defined in OrderSchema and CustomerSchema.
order_details = await order_crud.get_joined(
    db, 
    join_model=Customer, 
    schema_to_select=OrderSchema, 
    join_schema_to_select=CustomerSchema, 
    id=order_id
)
```

<h3>3. Get Multi Joined</h3>

```python
get_multi_joined(
    db: AsyncSession, 
    join_model: type[ModelType], 
    join_prefix: Optional[str] = None, 
    join_on: Optional[Join] = None, 
    schema_to_select: Optional[type[BaseModel]] = None, 
    join_schema_to_select: Optional[type[BaseModel]] = None, 
    join_type: str = "left", 
    offset: int = 0, 
    limit: int = 100, 
    sort_columns: Optional[Union[str, list[str]]] = None, 
    sort_orders: Optional[Union[str, list[str]]] = None, 
    return_as_model: bool = False, 
    **kwargs: Any
) -> dict[str, Any]
```
<p><b>Purpose</b>: Similar to <code>get_joined</code>, but for fetching multiple records. Supports pagination and sorting on the joined tables.</p>
<p><b>Usage Example</b>:</p> 

```python
# retrieves a paginated list of orders (up to 5), joined with the Customer table, 
# using specified schemas for selective column retrieval from both tables.
orders = await order_crud.get_multi_joined(
    db, 
    join_model=Customer, 
    offset=0, 
    limit=5, 
    schema_to_select=OrderSchema, 
    join_schema_to_select=CustomerSchema
)
```

<h3>4. Get Multi By Cursor</h3>

```python
get_multi_by_cursor(
    db: AsyncSession, 
    cursor: Any = None, 
    limit: int = 100, 
    schema_to_select: Optional[type[BaseModel]] = None, 
    sort_column: str = "id", 
    sort_order: str = "asc", 
    **kwargs: Any
) -> dict[str, Any]
```
<p><b>Purpose</b>: Implements cursor-based pagination for efficient data retrieval in large datasets. This is particularly useful for infinite scrolling interfaces.</p>
<p><b>Usage Example</b>:</p>

```python
# fetches the next 10 items after the last cursor for efficient pagination, 
# sorted by creation date in descending order.
paginated_items = await item_crud.get_multi_by_cursor(
    db, 
    cursor=last_cursor, 
    limit=10, 
    sort_column='created_at', 
    sort_order='desc'
)
```

<p>These advanced methods enhance FastCRUD's capabilities, allowing for more tailored and optimized interactions with the database, especially in scenarios involving complex data relationships and large datasets.</p>


## References

This project was heavily inspired by CRUDBase in [`FastAPI Microservices`](https://github.com/Kludex/fastapi-microservices) by @kludex.

## 10. License

[`MIT`](LICENSE.md)

## 11. Contact

Igor Magalhaes – [@igormagalhaesr](https://twitter.com/igormagalhaesr) – igormagalhaesr@gmail.com
[github.com/igorbenav](https://github.com/igorbenav/)
