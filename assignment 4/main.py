from fastapi import FastAPI, Query, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, List

app = FastAPI()

# ── 1. DATABASES ─────────────────────────────────────────────
products = [
    {'id': 1, 'name': 'Wireless Mouse', 'price': 499, 'category': 'Electronics', 'in_stock': True },
    {'id': 2, 'name': 'Notebook',       'price':  99, 'category': 'Stationery',  'in_stock': True },
    {'id': 3, 'name': 'USB Hub',        'price': 799, 'category': 'Electronics', 'in_stock': False},
    {'id': 4, 'name': 'Pen Set',        'price':  49, 'category': 'Stationery',  'in_stock': True },
]

feedback = []   
orders_db = []
cart = []       # Database for the shopping cart

# ── 2. PYDANTIC MODELS ───────────────────────────────────────
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

class ProductCreate(BaseModel):
    name: str = Field(..., min_length=2)
    price: int = Field(..., gt=0)
    category: str = Field(..., min_length=2)
    in_stock: bool

# 👈 NEW TASK: Checkout Request Model
class CheckoutRequest(BaseModel):
    customer_name: str = Field(..., min_length=2)
    delivery_address: str = Field(..., min_length=5)


# ── 3. PRODUCT ENDPOINTS ─────────────────────────────────────
@app.get('/')
def home():
    return {'message': 'Welcome to our E-commerce API'}

@app.get('/products')
def get_all_products():
    return {'products': products, 'total': len(products)}

@app.post('/products', status_code=status.HTTP_201_CREATED)
def create_product(prod: ProductCreate):
    for p in products:
        if p['name'].lower() == prod.name.lower():
            raise HTTPException(status_code=400, detail="Product already exists")
    
    new_id = max([p['id'] for p in products], default=0) + 1
    new_product = {"id": new_id, "name": prod.name, "price": prod.price, "category": prod.category, "in_stock": prod.in_stock}
    products.append(new_product)
    return {"message": "Product added", "product": new_product}

@app.put('/products/discount')
def apply_category_discount(category: str = Query(...), discount_percent: int = Query(..., ge=1, le=99)):
    updated_items = []
    for p in products:
        if p['category'].lower() == category.lower():
            p['price'] = int(p['price'] * (1 - discount_percent / 100))
            updated_items.append(p)
    if not updated_items: return {"message": f"No products found in category '{category}'"}
    return {"message": f"Applied {discount_percent}% discount to {len(updated_items)} items", "updated_products": updated_items}

@app.put('/products/{product_id}')
def update_product(product_id: int, price: Optional[int] = Query(None), in_stock: Optional[bool] = Query(None)):
    for p in products:
        if p['id'] == product_id:
            if price is not None: p['price'] = price
            if in_stock is not None: p['in_stock'] = in_stock
            return {"message": "Product updated successfully", "product": p}
    raise HTTPException(status_code=404, detail="Product not found")

@app.delete('/products/{product_id}')
def delete_product(product_id: int):
    for i, p in enumerate(products):
        if p['id'] == product_id:
            name = p['name']
            products.pop(i)
            return {"message": f"Product '{name}' deleted"}
    return JSONResponse(status_code=404, content={"error": "Product not found"})

@app.get('/store/summary')
def get_store_summary():
    total = len(products)
    in_stock_count = sum(1 for p in products if p['in_stock'])
    out_of_stock_count = total - in_stock_count
    categories = list({p['category'] for p in products}) 
    return {"store_name": "My Store", "total_products": total, "in_stock": in_stock_count, "out_of_stock": out_of_stock_count, "categories": categories}

@app.get('/products/summary')
def get_product_summary():
    total = len(products)
    in_stock = sum(1 for p in products if p['in_stock'])
    out_of_stock = total - in_stock
    cheap_item = min(products, key=lambda p: p['price'])
    exp_item = max(products, key=lambda p: p['price'])
    unique_categories = list({p['category'] for p in products})
    return {"total": total, "in_stock": in_stock, "out_of_stock": out_of_stock, "most_expensive": exp_item, "cheapest": cheap_item, "categories": unique_categories}

@app.get('/products/deals')
def get_deals():
    return {"best_deal": min(products, key=lambda p: p['price']), "premium_pick": max(products, key=lambda p: p['price'])}

@app.get('/products/instock')
def get_instock_products():
    instock_items = [p for p in products if p['in_stock']]
    return {"in_stock_products": instock_items, "count": len(instock_items)}

@app.get('/products/filter')
def filter_products(category: str = Query(None), min_price: int = Query(None), max_price: int = Query(None), in_stock: bool = Query(None)):
    result = products
    if category: result = [p for p in result if p['category'].lower() == category.lower()]
    if min_price is not None: result = [p for p in result if p['price'] >= min_price]
    if max_price is not None: result = [p for p in result if p['price'] <= max_price]
    if in_stock is not None: result = [p for p in result if p['in_stock'] == in_stock]
    return {'filtered_products': result, 'count': len(result)}

@app.get('/products/search/{keyword}')
def search_products(keyword: str):
    matched = [p for p in products if keyword.lower() in p['name'].lower()]
    if not matched: return {"message": "No products matched"}
    return {"matched_products": matched, "total": len(matched)}

@app.get('/products/category/{category_name}')
def get_category(category_name: str):
    filtered = [p for p in products if p['category'].lower() == category_name.lower()]
    if not filtered: return {"error": "Not found"}
    return {"products": filtered, "count": len(filtered)}

@app.get('/products/audit')
def get_inventory_audit():
    in_stock_items = [p for p in products if p['in_stock']]
    out_of_stock_names = [p['name'] for p in products if not p['in_stock']]
    total_value = sum(p['price'] * 10 for p in in_stock_items)
    expensive_item = max(products, key=lambda p: p['price'])
    return {"total_products": len(products), "in_stock_count": len(in_stock_items), "out_of_stock_names": out_of_stock_names, "total_stock_value": total_value, "most_expensive": {"name": expensive_item['name'], "price": expensive_item['price']}}

@app.get('/products/{product_id}/price')
def get_product_price(product_id: int):
    for p in products:
        if p['id'] == product_id: return {"name": p['name'], "price": p['price']}
    return {"error": "Not found"}

@app.get('/products/{product_id}')
def get_product(product_id: int):
    for p in products:
        if p['id'] == product_id: return {'product': p}
    raise HTTPException(status_code=404, detail="Product not found")


# ── 4. CART ENDPOINTS ────────────────────────────────────────

@app.post('/cart/add')
def add_to_cart(product_id: int = Query(...), quantity: int = Query(..., ge=1)):
    found_product = None
    for p in products:
        if p['id'] == product_id:
            found_product = p
            break
            
    if not found_product:
        raise HTTPException(status_code=404, detail="Product not found")
        
    if not found_product['in_stock']:
        raise HTTPException(status_code=400, detail=f"{found_product['name']} is out of stock")
    
    for item in cart:
        if item['product_id'] == product_id:
            item['quantity'] += quantity
            item['subtotal'] = item['quantity'] * item['unit_price']
            return {"message": "Cart updated", "cart_item": item}
            
    subtotal = found_product['price'] * quantity
    cart_item = {"product_id": product_id, "product_name": found_product['name'], "quantity": quantity, "unit_price": found_product['price'], "subtotal": subtotal}
    cart.append(cart_item)
    return {"message": "Added to cart", "cart_item": cart_item}

# 👈 NEW TASK: Checkout Endpoint
@app.post('/cart/checkout')
def checkout_cart(req: CheckoutRequest):
    if not cart:
        raise HTTPException(status_code=400, detail="Cart is empty")
        
    grand_total = sum(item['subtotal'] for item in cart)
    
    new_order = {
        "order_id": len(orders_db) + 1,
        "customer_name": req.customer_name,
        "delivery_address": req.delivery_address,
        "items": list(cart),
        "grand_total": grand_total,
        "status": "pending"
    }
    
    orders_db.append(new_order)
    cart.clear() # Empties the cart!
    
    return {"message": "Checkout successful", "orders_placed": 1, "grand_total": grand_total, "order_details": new_order}

# 👈 NEW TASK: Remove from Cart
@app.delete('/cart/{product_id}')
def remove_from_cart(product_id: int):
    for i, item in enumerate(cart):
        if item['product_id'] == product_id:
            cart.pop(i)
            return {"message": f"Item {product_id} removed from cart"}
    return JSONResponse(status_code=404, content={"error": "Item not found in cart"})

# 👈 UPDATED: View Cart (Handles empty state)
@app.get('/cart')
def view_cart():
    if not cart:
        return {"message": "Cart is empty", "items": [], "item_count": 0, "grand_total": 0}
        
    grand_total = sum(item['subtotal'] for item in cart)
    return {"items": cart, "item_count": len(cart), "grand_total": grand_total}


# ── 5. ORDERS & FEEDBACK ENDPOINTS ───────────────────────────

# 👈 NEW TASK: Get all Orders
@app.get('/orders')
def get_all_orders():
    return {"orders": orders_db, "total": len(orders_db)}

@app.post('/feedback')
def submit_feedback(fb: CustomerFeedback):
    feedback.append(fb.dict())
    return {"message": "Success", "total": len(feedback)}

@app.post('/orders/bulk')
def place_bulk_order(order: BulkOrder):
    return {"message": "Bulk order placed"}

@app.post('/orders')
def create_order(order: StandardOrder):
    new_order = {"order_id": len(orders_db) + 1, "product_id": order.product_id, "quantity": order.quantity, "status": "pending"}
    orders_db.append(new_order)
    return new_order

@app.get('/orders/{order_id}')
def get_order(order_id: int):
    for o in orders_db:
        if o['order_id'] == order_id: return o
    return {"error": "Not found"}

@app.patch('/orders/{order_id}/confirm')
def confirm_order(order_id: int):
    for o in orders_db:
        if o['order_id'] == order_id:
            o['status'] = "confirmed"
            return {"message": "Approved", "order": o}
    return {"error": "Not found"}
