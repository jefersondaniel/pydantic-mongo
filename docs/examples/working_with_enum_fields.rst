# Working with Enum Fields

When working with MongoDB and Pydantic models, handling Enum fields can be tricky because BSON doesn't automatically serialize Python Enum values. This guide explains two approaches to handle this situation.

## The Problem

By default, when you try to save a Pydantic model with an Enum field to MongoDB, you might encounter serialization issues because BSON doesn't know how to handle Python Enum types directly.

```python
from enum import Enum
from pydantic import BaseModel

class OrderStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"

class Order(BaseModel):
    status: OrderStatus  # This might cause BSON serialization issues
```

## Solution 1: Using EnumAnnotation

The recommended approach is to use the `EnumAnnotation` provided by pydantic-mongo. This allows you to work with regular Enum classes while ensuring proper BSON serialization:

```python
from enum import Enum
from typing_extensions import Annotated
from pydantic import BaseModel
from pydantic_mongo import EnumAnnotation

class OrderStatus(Enum):  # Regular Enum, no str inheritance needed
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"

class Order(BaseModel):
    status: Annotated[OrderStatus, EnumAnnotation[OrderStatus]]

# Usage
order = Order(status=OrderStatus.PENDING)
# Will serialize correctly to BSON
# The value will be stored as "pending" in MongoDB

# You can also create from string values
order = Order(status="pending")  # Will be converted to OrderStatus.PENDING
```

The `EnumAnnotation` approach provides works with any Enum class (no need to inherit from `str`).

## Solution 2: String-based Enums

An alternative approach is to make your Enum class inherit from `str`. This makes the enum values serialize as strings automatically:

```python
from enum import Enum
from pydantic import BaseModel

class OrderStatus(str, Enum):  # Note the str inheritance
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"

class Order(BaseModel):
    status: OrderStatus

# Usage
order = Order(status=OrderStatus.PENDING)
# Will serialize correctly to BSON
# The value will be stored as "pending" in MongoDB
```

While this approach is simpler, it requires modifying your enum classes and might not be suitable if you're working with third-party enum classes
