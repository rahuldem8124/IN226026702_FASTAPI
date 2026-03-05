from fastapi import FastAPI, Query

app = FastAPI()

products = [
    {'id': 1, 'name': 'Wireless Mouse',      'price': 499,  'category': 'Electronics', 'in_stock': True },
    {'id': 2, 'name': 'Notebook',            'price':  99,  'category': 'Stationery',  'in_stock': True },
    {'id': 3, 'name': 'USB Hub',             'price': 799,  'category': 'Electronics', 'in_stock': False},
    {'id': 4, 'name': 'Pen Set',             'price':  49,  'category': 'Stationery',  'in_stock': True },
    {'id': 5, 'name': 'Laptop Stand',        'price': 1299, 'category': 'Electronics', 'in_stock': True },
    {'id': 6, 'name': 'Mechanical Keyboard', 'price': 2499, 'category': 'Electronics', 'in_stock': True },
    {'id': 7, 'name': 'Webcam',              'price': 1599, 'category': 'Electronics', 'in_stock': False},
]

@app.get('/')
def home():
    return {'message': 'Welcome to our E-commerce API'}

@app.get('/store/summary')
def get_store_summary():
    total = len(products)
    in_stock_count = sum(1 for p in products if p['in_stock'])
    out_of_stock_count = total - in_stock_count
    categories = list({p['category'] for p in products}) 
    return {
        "store_name": "My E-commerce Store",
        "total_products": total,
        "in_stock": in_stock_count,
        "out_of_stock": out_of_stock_count,
        "categories": categories
    }

@app.get('/products')
def get_all_products():
    return {'products': products, 'total': len(products)}

@app.get('/products/filter')
def filter_products(
    category:  str  = Query(None, description='Electronics or Stationery'),
    max_price: int  = Query(None, description='Maximum price'),
    in_stock:  bool = Query(None, description='True = in stock only')
):
    result = products
    if category:
        result = [p for p in result if p['category'].lower() == category.lower()]
    if max_price:
        result = [p for p in result if p['price'] <= max_price]
    if in_stock is not None:
        result = [p for p in result if p['in_stock'] == in_stock]
    return {'filtered_products': result, 'count': len(result)}

@app.get('/products/instock')
def get_instock_products():
    instock_items = [p for p in products if p['in_stock']]
    return {"in_stock_products": instock_items, "count": len(instock_items)}

# ── Bonus Task: Deals Endpoint ───────────────────────────────
@app.get('/products/deals')
def get_deals():
    cheapest = min(products, key=lambda p: p['price'])
    most_expensive = max(products, key=lambda p: p['price'])
    return {
        "best_deal": cheapest,
        "premium_pick": most_expensive
    }

@app.get('/products/category/{category_name}')
def get_category(category_name: str):
    filtered_products = [p for p in products if p['category'].lower() == category_name.lower()]
    if not filtered_products:
        return {"error": "No products found in this category"}
    return {"products": filtered_products, "count": len(filtered_products)}

@app.get('/products/search/{keyword}')
def search_products(keyword: str):
    matched_products = [p for p in products if keyword.lower() in p['name'].lower()]
    if not matched_products:
        return {"message": "No products matched your search"}
    return {"matched_products": matched_products, "total": len(matched_products)}

@app.get('/products/{product_id}')
def get_product(product_id: int):
    for product in products:
        if product['id'] == product_id:
            return {'product': product}
    return {'error': 'Product not found'}