from fastapi import FastAPI, Query
from pydantic import BaseModel, Field
from typing import Optional, List

app = FastAPI()

# ── 1. DATABASES (Temporary Storage) ─────────────────────────
products = [
    {'id': 1, 'name': 'Wireless Mouse',      'price': 499,  'category': 'Electronics', 'in_stock': True },
    {'id': 2, 'name': 'Notebook',            'price':  99,  'category': 'Stationery',  'in_stock': True },
    {'id': 3, 'name': 'USB Hub',             'price': 799,  'category': 'Electronics', 'in_stock': False},
    {'id': 4, 'name': 'Pen Set',             'price':  49,  'category': 'Stationery',  'in_stock': True },
    {'id': 5, 'name': 'Laptop Stand',        'price': 1299, 'category': 'Electronics', 'in_stock': True },
    {'id': 6, 'name': 'Mechanical Keyboard', 'price': 2499, 'category': 'Electronics', 'in_stock': True },
    {'id': 7, 'name': 'Webcam',              'price': 1599, 'category': 'Electronics', 'in_stock': False},
]

feedback = []   # Stores customer reviews
orders_db = []  # Stores trackable orders

# ── 2. PYDANTIC MODELS (Validation) ──────────────────────────
class CustomerFeedback(BaseModel):
    customer_name: str = Field(..., min_length=2)
    product_id: int = Field(..., gt=0)
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = Field(None, max_length=300)

class OrderItem(BaseModel):
    product_id: int = Field(..., gt=0)
    quantity: int = Field(..., ge=1, le=50)

class BulkOrder(BaseModel):
    company_name: str = Field(..., min_length=2)
    contact_email: str = Field(..., min_length=5)
    items: List[OrderItem] = Field(..., min_length=1)

class StandardOrder(BaseModel):
    product_id: int = Field(..., gt=0)
    quantity: int = Field(..., ge=1)

# ── 3. ROOT & DASHBOARD ENDPOINTS ────────────────────────────
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

@app.get('/products/summary')
def get_product_summary():
    total = len(products)
    in_stock = sum(1 for p in products if p['in_stock'])
    out_of_stock = total - in_stock
    cheap_item = min(products, key=lambda p: p['price'])
    exp_item = max(products, key=lambda p: p['price'])
    unique_categories = list({p['category'] for p in products})
    
    return {
        "total_products": total,
        "in_stock_count": in_stock,
        "out_of_stock_count": out_of_stock,
        "most_expensive": {"name": exp_item['name'], "price": exp_item['price']},
        "cheapest": {"name": cheap_item['name'], "price": cheap_item['price']},
        "categories": unique_categories
    }

@app.get('/products/deals')
def get_deals():
    cheapest = min(products, key=lambda p: p['price'])
    most_expensive = max(products, key=lambda p: p['price'])
    return {
        "best_deal": cheapest,
        "premium_pick": most_expensive
    }

@app.get('/products/instock')
def get_instock_products():
    instock_items = [p for p in products if p['in_stock']]
    return {"in_stock_products": instock_items, "count": len(instock_items)}

# ── 4. FILTER & SEARCH ENDPOINTS ─────────────────────────────
@app.get('/products/filter')
def filter_products(
    category:  str  = Query(None, description='Electronics or Stationery'),
    min_price: int  = Query(None, description='Minimum price'),
    max_price: int  = Query(None, description='Maximum price'),
    in_stock:  bool = Query(None, description='True = in stock only')
):
    result = products
    if category:
        result = [p for p in result if p['category'].lower() == category.lower()]
    if min_price is not None:
        result = [p for p in result if p['price'] >= min_price]
    if max_price is not None:
        result = [p for p in result if p['price'] <= max_price]
    if in_stock is not None:
        result = [p for p in result if p['in_stock'] == in_stock]
    return {'filtered_products': result, 'count': len(result)}

@app.get('/products/search/{keyword}')
def search_products(keyword: str):
    matched_products = [p for p in products if keyword.lower() in p['name'].lower()]
    if not matched_products:
        return {"message": "No products matched your search"}
    return {"matched_products": matched_products, "total": len(matched_products)}

@app.get('/products/category/{category_name}')
def get_category(category_name: str):
    filtered_products = [p for p in products if p['category'].lower() == category_name.lower()]
    if not filtered_products:
        return {"error": "No products found in this category"}
    return {"products": filtered_products, "count": len(filtered_products)}

# ── 5. SINGLE PRODUCT ENDPOINTS ──────────────────────────────
@app.get('/products')
def get_all_products():
    return {'products': products, 'total': len(products)}

@app.get('/products/{product_id}/price')
def get_product_price(product_id: int):
    for product in products:
        if product['id'] == product_id:
            return {"name": product['name'], "price": product['price']}
    return {"error": "Product not found"}

@app.get('/products/{product_id}')
def get_product(product_id: int):
    for product in products:
        if product['id'] == product_id:
            return {'product': product}
    return {'error': 'Product not found'}

# ── 6. POST ENDPOINTS (Orders & Feedback) ────────────────────
@app.post('/feedback')
def submit_feedback(fb: CustomerFeedback):
    fb_dict = fb.dict()
    feedback.append(fb_dict)
    return {
        "message": "Feedback submitted successfully",
        "feedback": fb_dict,
        "total_feedback": len(feedback)
    }

@app.post('/orders/bulk')
def place_bulk_order(order: BulkOrder):
    confirmed = []
    failed = []
    grand_total = 0

    for item in order.items:
        found_product = next((p for p in products if p['id'] == item.product_id), None)
        
        if not found_product:
            failed.append({"product_id": item.product_id, "reason": "Product not found"})
            continue
            
        if not found_product['in_stock']:
            failed.append({"product_id": item.product_id, "reason": f"{found_product['name']} is out of stock"})
            continue
            
        subtotal = found_product['price'] * item.quantity
        grand_total += subtotal
        confirmed.append({"product": found_product['name'], "qty": item.quantity, "subtotal": subtotal})

    return {"company": order.company_name, "confirmed": confirmed, "failed": failed, "grand_total": grand_total}

# ── 7. ORDER TRACKER ENDPOINTS (Task 6) ──────────────────────
@app.post('/orders')
def create_order(order: StandardOrder):
    new_order = {
        "order_id": len(orders_db) + 1,  
        "product_id": order.product_id,
        "quantity": order.quantity,
        "status": "pending"              
    }
    orders_db.append(new_order)
    return new_order

@app.get('/orders/{order_id}')
def get_order(order_id: int):
    for o in orders_db:
        if o['order_id'] == order_id:
            return o
    return {"error": "Order not found"}

@app.patch('/orders/{order_id}/confirm')
def confirm_order(order_id: int):
    for o in orders_db:
        if o['order_id'] == order_id:
            o['status'] = "confirmed"
            return {"message": "Order approved by warehouse", "order": o}
    return {"error": "Order not found"}
