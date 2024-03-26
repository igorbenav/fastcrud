# Using FastCRUD for Enhanced CRUD Operations

FastCRUD is a versatile tool for handling CRUD (Create, Read, Update, Delete) operations in FastAPI applications with SQLAlchemy models. It leverages Pydantic schemas for data validation and serialization, offering a streamlined approach to database interactions.

## Key Features

- Simplified CRUD operations with SQLAlchemy models.
- Data validation and serialization using Pydantic.
- Support for complex queries including joins and pagination.

## Getting Started

### Step 1: Define Models and Schemas

Define your SQLAlchemy models and Pydantic schemas for data representation.

```python
# SQLAlchemy models and Pydantic schema definitions
```

### Step 2: Initialize FastCRUD

Create a FastCRUD instance for your model to handle CRUD operations.

```python
from fastcrud import FastCRUD

# Creating a FastCRUD instance
my_model_crud = FastCRUD(MyModel)
```

### Step 3: Pick your Method

Then you just pick the method you need and use it like this:

```python
# Creating a new record
new_record = await my_model_crud.create(db_session, create_schema_instance)
```

More on available methods below.

---

## Understanding FastCRUD Methods

FastCRUD offers a comprehensive suite of methods for CRUD operations, each designed to handle different aspects of database interactions efficiently.

### 1. Create

```python
create(
    db: AsyncSession,
    object: CreateSchemaType
) -> ModelType
```

**Purpose**: To create a new record in the database.  
**Usage Example**: Creates an item with name 'New Item'.

```python
new_item = await item_crud.create(db, ItemCreateSchema(name="New Item"))
```

### 2. Get

```python
get(
    db: AsyncSession,
    schema_to_select: Optional[type[BaseModel]] = None,
    return_as_model: bool = False,
    **kwargs: Any
) -> Optional[Union[dict, BaseModel]]
```

**Purpose**: To fetch a single record based on filters, with an option to select specific columns using a Pydantic schema.  
**Usage Example**: Fetches the item with item_id as its id.

```python
item = await item_crud.get(db, id=item_id)
```

### 3. Exists

```python
exists(
    db: AsyncSession,
    **kwargs: Any
) -> bool
```

**Purpose**: To check if a record exists based on provided filters.  
**Usage Example**: Checks whether an item with name 'Existing Item' exists.

```python
exists = await item_crud.exists(db, name="Existing Item")
```

### 4. Count

```python
count(
    db: AsyncSession,
    joins_config: Optional[list[JoinConfig]] = None,
    **kwargs: Any
) -> int
```

**Purpose**: To count the number of records matching provided filters.  
**Usage Example**: Counts the number of items with the 'Books' category.

```python
count = await item_crud.count(db, category="Books")
```

### 5. Get Multi

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

**Purpose**: To fetch multiple records with optional sorting, pagination, and model conversion.  
**Usage Example**: Fetches a subset of 5 items, starting from the 11th item in the database.

```python
items = await item_crud.get_multi(db, offset=10, limit=5)
```

### 6. Update

```python
update(
    db: AsyncSession, 
    object: Union[UpdateSchemaType, dict[str, Any]], 
    allow_multiple: bool = False,
    **kwargs: Any
) -> None
```

**Purpose**: To update an existing record in the database.  
**Usage Example**: Updates the description of the item with item_id as its id.

```python
await item_crud.update(db, ItemUpdateSchema(description="Updated"), id=item_id)
```

### 7. Delete

```python
delete(
    db: AsyncSession, 
    db_row: Optional[Row] = None, 
    allow_multiple: bool = False,
    **kwargs: Any
) -> None
```

**Purpose**: To delete a record from the database, with support for soft delete.  
**Usage Example**: Deletes the item with item_id as its id, performs a soft delete if the model has the 'is_deleted' column.

```python
await item_crud.delete(db, id=item_id)
```

### 8. Hard Delete

```python
db_delete(
    db: AsyncSession, 
    allow_multiple: bool = False,
    **kwargs: Any
) -> None
```

**Purpose**: To hard delete a record from the database.  
**Usage Example**: Hard deletes the item with item_id as its id.

```python
await item_crud.db_delete(db, id=item_id)
```

---

## Advanced Methods for Complex Queries and Joins

FastCRUD extends its functionality with advanced methods tailored for complex query operations and handling joins. These methods cater to specific use cases where more sophisticated data retrieval and manipulation are required.

### 1. Get Multi

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

**Purpose**: To fetch multiple records based on specified filters, with options for sorting and pagination.  
**Usage Example**: Gets the first 10 items sorted by 'name' in ascending order.

```python
items = await item_crud.get_multi(db, offset=0, limit=10, sort_columns=['name'], sort_orders=['asc'])
```

### 2. Get Joined

```python
get_joined(
    db: AsyncSession,
    join_model: Optional[type[DeclarativeBase]] = None,
    join_prefix: Optional[str] = None,
    join_on: Optional[Union[Join, BinaryExpression]] = None,
    schema_to_select: Optional[type[BaseModel]] = None,
    join_schema_to_select: Optional[type[BaseModel]] = None,
    join_type: str = "left",
    join_filters: Optional[dict] = None,
    joins_config: Optional[list[JoinConfig]] = None,
    **kwargs: Any,
) -> Optional[dict[str, Any]]
```

**Purpose**: To fetch a single record with one or multiple joins on other models.
**Usage Example**: Fetches order details for a specific order by joining with the Customer table, selecting specific columns as defined in OrderSchema and CustomerSchema.

```python
order_details = await order_crud.get_joined(
    db,
    join_model=Customer,
    schema_to_select=OrderSchema,
    join_schema_to_select=CustomerSchema,
    id=order_id
)
```

### 3. Get Multi Joined

```python
get_multi_joined(
    db: AsyncSession,
    join_model: Optional[type[ModelType]] = None,
    join_prefix: Optional[str] = None,
    join_on: Optional[Any] = None,
    schema_to_select: Optional[type[BaseModel]] = None,
    join_schema_to_select: Optional[type[BaseModel]] = None,
    join_type: str = "left",
    alias: Optional[str] = None,
    join_filters: Optional[dict] = None,
    offset: int = 0,
    limit: int = 100,
    sort_columns: Optional[Union[str, list[str]]] = None,
    sort_orders: Optional[Union[str, list[str]]] = None,
    return_as_model: bool = False,
    joins_config: Optional[list[JoinConfig]] = None,
    **kwargs: Any,
) -> dict[str, Any]
```

**Purpose**: Similar to `get_joined`, but for fetching multiple records.  
**Usage Example**: Retrieves a paginated list of orders (up to 5), joined with the Customer table, using specified schemas for selective column retrieval from both tables.

```python
orders = await order_crud.get_multi_joined(
    db,
    join_model=Customer,
    offset=0,
    limit=5,
    schema_to_select=OrderSchema,
    join_schema_to_select=CustomerSchema
)
```

### 4. Get Multi By Cursor

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

**Purpose**: Implements cursor-based pagination for efficient data retrieval in large datasets.  
**Usage Example**: Fetches the next 10 items after the last cursor for efficient pagination, sorted by creation date in descending order.

```python
paginated_items = await item_crud.get_multi_by_cursor(
    db,
    cursor=last_cursor,
    limit=10,
    sort_column='created_at',
    sort_order='desc'
)
```

### 5. Select

```python
async def select(
    db: AsyncSession,
    schema_to_select: Optional[type[BaseModel]] = None,
    sort_columns: Optional[Union[str, list[str]]] = None,
    sort_orders: Optional[Union[str, list[str]]] = None,
    **kwargs: Any
) -> Selectable
```

**Purpose**: Constructs a SQL Alchemy Select statement with optional column selection, filtering, and sorting.
**Usage Example**: Selects all items, filtering by 'name' and sorting by 'id'. Returns the `select` statement.

```python
stmt = await item_crud.select(schema_to_select=ItemSchema, sort_columns='id', name='John')
# Note: This method returns a SQL Alchemy Selectable object, not the actual query result.
```

### 6. Count for Joined Models

```python
count(
    db: AsyncSession,
    joins_config: Optional[list[JoinConfig]] = None,
    **kwargs: Any
) -> int
```

**Purpose**: To count records that match specified filters, especially useful in scenarios involving joins between models. This method supports counting unique entities across relationships, a common requirement in many-to-many or complex relationships.
**Usage Example**: Count the number of unique projects a participant is involved in, considering a many-to-many relationship between Project and Participant models.

```python
# Assuming a Project model related to a Participant model through a many-to-many relationship
projects_count = await project_crud.count(
    db=session,
    joins_config=[
        JoinConfig(
            model=Participant,
            join_on=ProjectsParticipantsAssociation.project_id == Project.id,
            join_type="inner"
        )
    ],
    participant_id=specific_participant_id
)
```

## Error Handling

FastCRUD provides mechanisms to handle common database errors, ensuring robust API behavior.
