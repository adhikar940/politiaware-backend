# Generic Async GraphQL Engine (`generic_async_graphql`)

An automated, config-driven **Asynchronous GraphQL Engine** for Django powered by **Strawberry GraphQL** with isolated **`async_db_operations.py`** and **`sync_db_operations.py`** service layers.

---

## 🌟 Key Features

1. **Native Asynchronous Execution**:
   - Resolvers run as native `async def` functions under ASGI (Uvicorn / Granian).
   - Non-blocking I/O with high concurrency.

2. **Deterministic, Clean Database Separation**:
   - **`async_db_operations.py`**: All queries run natively asynchronously (`acount()`, `aget()`, `aexists()`, async iterators) with automatic `select_related` relational optimization from GraphQL selection sets.
   - **`sync_db_operations.py`**: All write operations (`sync_create_record`, `sync_update_record`, `sync_partial_update_record`, `sync_delete_record`) run strictly synchronously inside atomic transactions with full model validation (`full_clean()`).
   - Mutations wrap sync operations via thread-sensitive `sync_to_async`.
   - **Zero `SynchronousOnlyOperation` leaks** into the GraphQL resolver tree.

3. **Zero Configuration Support (`"ModelName": {}`)**:
   - Automatically generates list queries (`allPartys`, `allStates`) with top-down nested filters, text search, multi-column ordering, and pagination.
   - Automatically generates full asynchronous CRUD mutations (`create`, `update`, `partialUpdate`, `delete`).

4. **Sole Asynchronous GraphQL Endpoint**:
   - Served via Strawberry's `AsyncGraphQLView` exclusively at `/graphql/async/` (e.g. `http://127.0.0.1:8000/graphql/async/`).

---

## 📁 Architecture Overview

```
politiaware_backend/generic_async_graphql/
├── __init__.py              # Public exports (generate_generic_async_graphql, async/sync db_operations)
├── builder.py               # Assembles Strawberry Query and Mutation types into Schema
├── config_parser.py         # Normalizes GRAPHQL_CONF & resolves hooks/callables
├── model_loader.py          # Django model introspection & field analysis
├── async_db_operations.py   # Centralized native async DB queries & async mutation bridges
├── sync_db_operations.py    # Strictly synchronous write operations (create, update, partial update, delete)
├── type_factory.py          # Dynamic Strawberry types (Model types, Paginated containers, Payloads)
├── filter_factory.py        # Top-down operator filter input types (StringFilter, IntFilter, etc.)
├── input_factory.py         # Dynamic create/update input types
├── query_factory.py         # Generates async list & extra queries calling async_db_operations
└── mutation_factory.py      # Generates async mutations calling async_db_operations
```

---

## 🔍 Example Async Queries

### 1. Paginated Query with Top-Down Filters & Search

```graphql
query {
  allPartys(
    filters: {
      abbreviation: {
        icontains: "BSP"
        in: ["BSP", "INC"]
      }
      partystatus: {
        exact: "National"
      }
    }
    search: "Bahujan"
    orderBy: ["partyname"]
    limit: 10
    offset: 0
  ) {
    total
    offset
    limit
    data {
      id
      partyname
      abbreviation
      partystatus
    }
  }
}
```

---

## ✏️ Example Async Mutations

### 1. Create Record
```graphql
mutation {
  createParty(
    input: {
      partyname: "New Democratic Party"
      abbreviation: "NDP"
      partystatus: "State"
    }
  ) {
    success
    errors
    data {
      id
      partyname
      abbreviation
    }
  }
}
```

### 2. Update Record
```graphql
mutation {
  updateParty(
    id: "1"
    input: {
      partyname: "Updated Democratic Party"
    }
  ) {
    success
    errors
    data {
      id
      partyname
    }
  }
}
```

### 3. Delete Record
```graphql
mutation {
  deleteParty(id: "1") {
    success
    errors
    id
  }
}
```

---

## ⚙️ Configuration (`graphql_conf.py`)

The engine consumes the centralized configuration from `graphql_conf.py`:

```python
GRAPHQL_CONF = {
    # 1. Zero Configuration: Auto-generates allPartys query + create/update/delete mutations
    "Party": {},

    # 2. Custom hooks:
    "LokSabha": {
        "queries": {
            "list": {
                "get_queryset": "myapp.hooks.custom_loksabha_filter",
            }
        },
        "mutations": {
            "create": {
                "before_save": "myapp.hooks.assign_defaults",
                "after_save": "myapp.hooks.notify_admin"
            }
        }
    }
}
```

---

## 🚀 Running the Async Endpoint

### 1. Ensure dependencies are installed
```bash
pip install "strawberry-graphql[django]" "uvicorn[standard]"
```

### 2. Choose Your Server Runner

#### Development (Recommended: Native ASGI with auto-reload)
Run Uvicorn from within the `politiaware_backend` directory:
```bash
uvicorn m.asgi:application --host 0.0.0.0 --port 9000 --reload
```

#### Development (Django default runserver)
```bash
python manage.py runserver 9000
```
*(Sufficient for local functional testing; Django will execute async views inside an event loop per request).*

#### Production (Docker / Production Deployment)
Run Gunicorn using the high-performance Uvicorn worker class:
```bash
gunicorn m.asgi:application -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:9000
```

### 3. Open the GraphiQL Explorer
Navigate in your browser to:
```text
http://127.0.0.1:9000/graphql/async/
```

