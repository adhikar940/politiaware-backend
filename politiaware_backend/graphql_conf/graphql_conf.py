"""
GraphQL configuration per model for generic_async_graphql (Strawberry).

Behavior:
1. Zero Configuration ("ModelName": {}):
   - Automatically generates async list query (e.g. allPartys, allStates) with all data-type filters + pagination + search + ordering, and full async mutations (create, update, partialUpdate, delete).
2. Explicit Configuration:
   - Whitelists only the specified operations and fields.
3. Custom Functions:
   - Use 'resolver', 'get_queryset', 'before_save', 'after_save', or 'mutate' to override or hook into logic.
4. Extra Queries & Mutations:
   - Use '__extra_queries__' and '__extra_mutations__' to add extra domain-specific queries and mutations.
"""

GRAPHQL_CONF = {
    "__extra_queries__": [
        "person.schema.EnumQuery",
    ],
    "Party": {},  # Zero config - full CRUD
    "cm": {},
    "governor": {},
    "State": {},
    "District": {},
    "LoksabhaMP": {},
    "RajyasabhaMP": {},
    "MLA": {},
    "MLC": {},
}