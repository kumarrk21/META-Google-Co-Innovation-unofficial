import json
import os
import random
from google.cloud import bigquery
from yaml_parser import YAMLParser


#------------------------------------------------------------------------------------#
# Create Loyalty Table
#------------------------------------------------------------------------------------#
def create_loyalty_table(client: bigquery.Client, project_id: str, dataset_id: str, loyalty_table_name:str) -> None:
    """Create and populate the loyalty program table."""
    table_id = f"{project_id}.{dataset_id}.loyalty_program"

    table_id = f"{project_id}.{dataset_id}.{loyalty_table_name}"

    try:
        client.get_table(table_id)
        print(f"Table {table_id} already exists")
        return
    except Exception:
        pass

    schema = [
        bigquery.SchemaField("customer_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("customer_name", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("tier", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("discount_percent", "INTEGER", mode="REQUIRED"),
        bigquery.SchemaField("points_balance", "INTEGER"),
        bigquery.SchemaField("free_shipping", "BOOLEAN"),
        bigquery.SchemaField("member_since", "DATE"),
    ]

    table = bigquery.Table(table_id, schema=schema)
    table = client.create_table(table, exists_ok=True)
    print(f"Created/verified table: {table_id}")

    # Sample loyalty customers
    customers = [
        {"customer_id": "CUST-1001", "customer_name": "Amara Johnson", "tier": "Platinum", "discount_percent": 20, "points_balance": 4850, "free_shipping": True, "member_since": "2022-03-15"},
        {"customer_id": "CUST-1002", "customer_name": "Luca Moretti", "tier": "Gold", "discount_percent": 15, "points_balance": 3200, "free_shipping": True, "member_since": "2023-01-20"},
        {"customer_id": "CUST-1003", "customer_name": "Sophia Chen", "tier": "Silver", "discount_percent": 10, "points_balance": 1800, "free_shipping": False, "member_since": "2023-08-10"},
        {"customer_id": "CUST-1004", "customer_name": "James Okonkwo", "tier": "Gold", "discount_percent": 15, "points_balance": 2750, "free_shipping": True, "member_since": "2022-11-05"},
        {"customer_id": "CUST-1005", "customer_name": "Elena Vasquez", "tier": "Bronze", "discount_percent": 5, "points_balance": 650, "free_shipping": False, "member_since": "2024-06-22"},
        {"customer_id": "CUST-1006", "customer_name": "Yuki Tanaka", "tier": "Platinum", "discount_percent": 20, "points_balance": 5100, "free_shipping": True, "member_since": "2021-12-01"},
        {"customer_id": "CUST-1007", "customer_name": "Marcus Schmidt", "tier": "Silver", "discount_percent": 10, "points_balance": 1400, "free_shipping": False, "member_since": "2024-02-14"},
        {"customer_id": "CUST-1008", "customer_name": "Priya Patel", "tier": "Gold", "discount_percent": 15, "points_balance": 3600, "free_shipping": True, "member_since": "2023-04-30"},
        {"customer_id": "CUST-1009", "customer_name": "Oliver Brooks", "tier": "Bronze", "discount_percent": 5, "points_balance": 320, "free_shipping": False, "member_since": "2025-01-10"},
        {"customer_id": "CUST-1010", "customer_name": "Camille Dubois", "tier": "Platinum", "discount_percent": 20, "points_balance": 4200, "free_shipping": True, "member_since": "2022-07-18"},
        {"customer_id": "CUST-1042", "customer_name": "Alex Rivera", "tier": "Gold", "discount_percent": 15, "points_balance": 2900, "free_shipping": True, "member_since": "2023-05-12"},
        {"customer_id": "CUST-1050", "customer_name": "Zara Mitchell", "tier": "Silver", "discount_percent": 10, "points_balance": 1100, "free_shipping": False, "member_since": "2024-09-01"},
    ]

    # Clear existing data and insert
    try:    
        errors = client.insert_rows_json(table_id, customers)
        if errors:
            print(f"Errors inserting loyalty data: {errors}")
        else:
            print(f"Inserted {len(customers)} loyalty data")
    except Exception as e:
        print(f"Error inserting loyalty data: {e}")


#------------------------------------------------------------------------------------#
# Create Inventory Table
#------------------------------------------------------------------------------------#
def create_inventory_table(client: bigquery.Client, catalog: list, project_id: str, dataset_id: str, inventory_table_name: str) -> None:
    """Create and populate the inventory table with stock for all 30 products."""
    table_id = f"{project_id}.{dataset_id}.{inventory_table_name}"

    try:
        client.get_table(table_id)
        print(f"Table {table_id} already exists")
        return
    except Exception:
        pass

    schema = [
        bigquery.SchemaField("sku", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("product_name", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("category", "STRING"),
        bigquery.SchemaField("size", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("quantity_in_stock", "INTEGER", mode="REQUIRED"),
        bigquery.SchemaField("price", "FLOAT", mode="REQUIRED"),
        bigquery.SchemaField("color", "STRING"),
        bigquery.SchemaField("material", "STRING"),
    ]

    
    table = bigquery.Table(table_id, schema=schema)
    table = client.create_table(table, exists_ok=False)
    print(f"Created table: {table_id}")

    # Generate inventory rows
    rows = []
    random.seed(42)  # Reproducible data
    for product in catalog:
        for size in product["sizes"]:
            qty = random.randint(0, 20)
            # Make some items low stock for demo purposes
            if product["sku"] in ["SKU-005", "SKU-015", "SKU-018"]:
                qty = random.randint(0, 3)
            rows.append({
                "sku": product["sku"],
                "product_name": product["name"],
                "category": product["category"],
                "size": size,
                "quantity_in_stock": qty,
                "price": product["price"],
                "color": product.get("color", ""),
                "material": product.get("material", ""),
            })

    try:    
        errors = client.insert_rows_json(table_id, rows)
        if errors:
            print(f"Errors inserting inventory: {errors}")
        else:
            print(f"Inserted {len(rows)} inventory rows")
    except Exception as e:
        print(f"Error inserting inventory rows: {e}")


#------------------------------------------------------------------------------------#
# Setup BQ for catalog and inventory data
#------------------------------------------------------------------------------------#
def load(parser: YAMLParser) -> None:

    project_id = parser.PROJECT_ID
    dataset_id = parser.AGENT_DS_BQ_DATASET_ID
    dataset_location = parser.AGENT_DS_DATASET_LOC
    dataset_desc = parser.AGENT_DS_DATASET_DESC
    inventory_table_name = parser.AGENT_DS_INVENTORY_TABLE_NAME
    loyalty_table_name = parser.AGENT_DS_LOYALTY_TABLE_NAME

    
    print("=" * 60)
    print("Vogue Concierge — BigQuery Setup")
    print("=" * 60)

    # Load Catalog
    dir_path = os.path.dirname(os.path.realpath(__file__))
    products_file = dir_path + "/data/products.json"
    with open(products_file, 'r') as f:
        catalog = json.load(f)
    
    print(f"Loaded {len(catalog)} products from catalog")

    # Create BQ dataset if not already available
    client = bigquery.Client(project=project_id)
    dataset_ref = bigquery.Dataset(f"{project_id}.{dataset_id}")
    dataset_ref.location = dataset_location
    dataset_ref.description = dataset_desc

    try:
        client.get_dataset(dataset_ref)
        print(f"Dataset {dataset_id} already exists")
    except Exception:
        client.create_dataset(dataset_ref)
        print(f"Created dataset {dataset_id}")

    create_inventory_table(client, catalog, project_id, dataset_id, inventory_table_name)
    create_loyalty_table(client, project_id, dataset_id, loyalty_table_name)
    
    print("\nBigQuery setup complete!")
    print(f"  Dataset: {project_id}.{dataset_id}")
    print(f"  Tables: inventory, loyalty_program")


