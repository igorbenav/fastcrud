---
name: FastCRUD Issue
about: Issue Template for FastCRUD
title: ''
labels: ''
assignees: ''

---

**Describe the bug or question**
A clear and concise description of what the bug or question is.

**To Reproduce**
Please provide a self-contained, minimal, and reproducible example of your use case
```python
from fastapi import FastAPI
from fastcrud import FastCRUD, crud_router
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "sqlite+aiosqlite:///./test.db"
engine = create_async_engine(DATABASE_URL, echo=True)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

app = FastAPI()

item_router = crud_router(
    session=async_session,
    model=Item,
    crud=FastCRUD(Item),
    create_schema=ItemCreateSchema,
    update_schema=ItemUpdateSchema,
    path="/items",
    tags=["Items"]
)

app.include_router(item_router)
```

**Description**
Describe the problem, question, or error you are facing. Include both the expected output for your input and the actual output you're observing.

**Screenshots**
If applicable, add screenshots to help explain your problem.

**Additional context**
Add any other context about the problem here.
