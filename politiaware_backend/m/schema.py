"""
Main GraphQL Schema for Politiaware Backend.
Powered by generic_async_graphql and Strawberry GraphQL.
"""

from .async_schema import async_schema

# Primary Strawberry async schema
schema = async_schema