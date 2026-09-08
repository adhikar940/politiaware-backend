"""
Verification test script for generic_async_graphql.
Tests async schema introspection, nested relation querying, filtering,
async query helpers (aget, acount, aexists), and sync write operations (create, update, partial update, delete).
"""

import os
import sys
import asyncio
import django

# Setup Django environment
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "m.settings")
django.setup()

from asgiref.sync import sync_to_async
from politiaware_backend.m.async_schema import async_schema
from party.models import Party
from cm.models import cm
from politiaware_backend.generic_async_graphql.async_db_operations import (
    async_fetch_list,
    async_get_record,
    async_count_records,
    async_check_exists
)
from politiaware_backend.generic_async_graphql.sync_db_operations import (
    sync_create_record,
    sync_update_record,
    sync_partial_update_record,
    sync_delete_record
)


def run_sync_tests():
    """Tests all synchronous write operations in pure synchronous context."""
    print("\n--- Testing Synchronous Write Operations (sync_db_operations) ---")
    test_party_name = "Test Sync Engine Party"
    test_party_abbr = "TSEP"
    # Clean up any leftover test data
    Party.objects.filter(abbreviation=test_party_abbr).delete()

    # 1. sync_create_record
    inst, errs = sync_create_record(
        model_cls=Party,
        input_data={
            "partyname": test_party_name,
            "abbreviation": test_party_abbr,
            "partystatus": "Regional",
            "foundeddate": "2020-01-01"
        },
        create_cols=["partyname", "abbreviation", "partystatus", "foundeddate"],
        required_cols=["partyname", "abbreviation", "foundeddate"]
    )
    assert errs is None, f"sync_create_record failed: {errs}"
    assert inst is not None
    created_id = inst.pk
    print(f"✅ sync_create_record created Party id={created_id}")

    # 2. sync_update_record
    inst_upd, errs = sync_update_record(
        model_cls=Party,
        pk_val=created_id,
        input_data={"partyname": "Updated Test Party", "abbreviation": test_party_abbr, "partystatus": "National"},
        update_cols=["partyname", "abbreviation", "partystatus"]
    )
    assert errs is None, f"sync_update_record failed: {errs}"
    assert inst_upd.partyname == "Updated Test Party"
    assert inst_upd.partystatus == "National"
    print("✅ sync_update_record updated successfully")

    # 3. sync_partial_update_record
    inst_part, errs = sync_partial_update_record(
        model_cls=Party,
        pk_val=created_id,
        input_data={"partyname": "Partial Updated Party"},
        update_cols=["partyname", "partystatus"]
    )
    assert errs is None, f"sync_partial_update_record failed: {errs}"
    assert inst_part.partyname == "Partial Updated Party"
    assert inst_part.partystatus == "National"  # unchanged
    print("✅ sync_partial_update_record updated only supplied fields")

    # 4. sync_delete_record
    del_id, success, errs = sync_delete_record(
        model_cls=Party,
        pk_val=created_id
    )
    assert success is True, f"sync_delete_record failed: {errs}"
    assert del_id == created_id
    assert not Party.objects.filter(pk=created_id).exists()
    print("✅ sync_delete_record deleted successfully")


async def run_async_tests():
    """Tests all asynchronous queries, relation fetching, and GraphQL schema in async context."""
    print("\n--- 1. Testing Schema Introspection ---")
    query_fields = list(async_schema._schema.query_type.fields.keys())
    mutation_fields = list(async_schema._schema.mutation_type.fields.keys()) if async_schema._schema.mutation_type else []

    print("Query fields available:", query_fields)
    print("Mutation fields available:", mutation_fields)

    assert "allPartys" in query_fields, "Missing allPartys list query"
    assert "allCms" in query_fields, "Missing allCms list query"
    assert "allGovernors" in query_fields, "Missing allGovernors list query"

    print("✅ Schema introspection succeeded!")

    print("\n--- 2. Testing Nested Relationship Query (ForeignKeys) ---")
    query_cm = """
    query TestCmWithParty {
        allCms(filters: {party: {abbreviation: {icontains: "b"}}}) {
            total
            offset
            limit
            data {
                name
                party {
                    abbreviation
                    partyname
                }
                rulingstate {
                    Statename
                }
            }
        }
    }
    """
    res = await async_schema.execute(query_cm)
    assert res.errors is None, f"Query failed with errors: {res.errors}"
    assert res.data is not None, "Query returned no data"
    cms = res.data["allCms"]["data"]
    assert len(cms) > 0, "Expected at least 1 CM returned"
    first_cm = cms[0]
    assert first_cm["party"] is not None, "Expected party to be populated"
    assert "abbreviation" in first_cm["party"], "Expected abbreviation in party"
    print(f"✅ Successfully resolved {len(cms)} CMs with nested party & state without SynchronousOnlyOperation!")

    print("\n--- 3. Testing Relationship Query on Districts with State ---")
    query_districts = """
    query TestDistricts {
        allDistricts(limit: 5) {
            total
            data {
                districtName
                state {
                    Statename
                }
            }
        }
    }
    """
    res_dist = await async_schema.execute(query_districts)
    assert res_dist.errors is None, f"Districts query failed with errors: {res_dist.errors}"
    assert len(res_dist.data["allDistricts"]["data"]) > 0
    print("✅ Districts with nested state resolved successfully!")

    print("\n--- 4. Testing Native Async Query Operations (async_db_operations) ---")
    # Async count
    party_count = await async_count_records(Party)
    assert party_count > 0, "Expected party count > 0"
    print(f"✅ async_count_records: {party_count}")

    # Async exists
    party_exists = await async_check_exists(Party, filters_data={"abbreviation": {"icontains": "b"}})
    assert party_exists is True, "Expected party with 'b' to exist"
    print("✅ async_check_exists: True")

    # Async get record with relations
    first_cm_obj = await cm.objects.afirst()
    if first_cm_obj:
        loaded_cm, err = await async_get_record(cm, first_cm_obj.pk, select_paths=["party", "rulingstate"])
        assert err is None, f"async_get_record error: {err}"
        assert loaded_cm is not None
        assert hasattr(loaded_cm, "name")
        print(f"✅ async_get_record with select_paths: {loaded_cm.name}")

    print("\n--- 5. Testing Async Mutations via GraphQL Schema ---")
    create_mutation = """
    mutation CreateTestParty {
        createParty(input: {partyname: "GQL Async Party", abbreviation: "GAP", partystatus: "Regional", foundeddate: "2020-01-01"}) {
            success
            errors
            data {
                id
                partyname
                abbreviation
            }
        }
    }
    """
    mut_res = await async_schema.execute(create_mutation)
    assert mut_res.errors is None, f"createParty mutation errors: {mut_res.errors}"
    assert mut_res.data["createParty"]["success"] is True
    gql_party_id = mut_res.data["createParty"]["data"]["id"]
    print(f"✅ GraphQL createParty mutation succeeded: id={gql_party_id}")

    # Clean up GraphQL created party using sync_to_async
    await sync_to_async(lambda: Party.objects.filter(pk=gql_party_id).delete(), thread_sensitive=True)()

    print("\n🎉 ALL ASYNC & SYNC DATABASE OPERATION TESTS PASSED!")


if __name__ == "__main__":
    run_sync_tests()
    asyncio.run(run_async_tests())
