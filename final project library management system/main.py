from fastapi import FastAPI, Query, Response, status
from pydantic import BaseModel, Field
from typing import Optional

# ── Q1: Setup & Home Route (Day 1) ─────────────────────────────────────────
app = FastAPI()

@app.get('/')
def home():
    return {'message': 'Welcome to City Public Library'}

# ── Q6, Q9, Q11: Pydantic Models (Day 2, Day 4) ────────────────────────────
class BorrowRequest(BaseModel):
    member_name: str = Field(..., min_length=2)
    book_id: int = Field(..., gt=0)
    # Pydantic allows up to 60 for premium, regular is capped in the helper logic
    borrow_days: int = Field(..., gt=0, le=60) 
    member_id: str = Field(..., min_length=4)
    member_type: str = Field(default='regular') # Q9 addition

class NewBook(BaseModel):
    title: str = Field(..., min_length=2)
    author: str = Field(..., min_length=2)
    genre: str = Field(..., min_length=2)
    is_available: bool = True

# ── Q2, Q4, Q14: Databases (Day 1, Day 5) ──────────────────────────────────
books = [
    {'id': 1, 'title': 'The Martian', 'author': 'Andy Weir', 'genre': 'Science', 'is_available': True},
    {'id': 2, 'title': '1984', 'author': 'George Orwell', 'genre': 'Fiction', 'is_available': False},
    {'id': 3, 'title': 'Sapiens', 'author': 'Yuval Noah Harari', 'genre': 'History', 'is_available': True},
    {'id': 4, 'title': 'Clean Code', 'author': 'Robert C. Martin', 'genre': 'Tech', 'is_available': True},
    {'id': 5, 'title': 'Dune', 'author': 'Frank Herbert', 'genre': 'Fiction', 'is_available': True},
    {'id': 6, 'title': 'Guns, Germs, and Steel', 'author': 'Jared Diamond', 'genre': 'History', 'is_available': False}
]

borrow_records = []
record_counter = 1
queue = []

# ── Q7, Q9, Q10: Helper Functions (Day 3) ──────────────────────────────────
def find_book(book_id: int):
    for b in books:
        if b['id'] == book_id:
            return b
    return None

def calculate_due_date(borrow_days: int, member_type: str = 'regular'):
    # Q9: Premium gets up to 60, regular is capped at 30
    if member_type.lower() == 'regular' and borrow_days > 30:
        borrow_days = 30
    elif member_type.lower() == 'premium' and borrow_days > 60:
        borrow_days = 60
    return f'Return by: Day {15 + borrow_days}'

def filter_books_logic(genre=None, author=None, is_available=None):
    result = books
    if genre is not None:
        result = [b for b in result if b['genre'].lower() == genre.lower()]
    if author is not None:
        result = [b for b in result if b['author'].lower() == author.lower()]
    if is_available is not None:
        result = [b for b in result if b['is_available'] == is_available]
    return result

# ══ FIXED ROUTES (MUST GO ABOVE VARIABLE ROUTES) ═══════════════════════════

# ── Q2: Get all books (Day 1) ──────────────────────────────────────────────
@app.get('/books')
def get_all_books():
    available = sum(1 for b in books if b['is_available'])
    return {
        'books': books, 
        'total': len(books), 
        'available_count': available
    }

# ── Q4: Get Borrow Records (Day 1) ─────────────────────────────────────────
@app.get('/borrow-records')
def get_borrow_records():
    return {'records': borrow_records, 'total': len(borrow_records)}

# ── Q19: Borrow Records Search & Page (Day 6) ──────────────────────────────
@app.get('/borrow-records/search')
def search_borrow_records(member_name: str = Query(...)):
    results = [r for r in borrow_records if member_name.lower() in r['member_name'].lower()]
    return {"results": results, "total_found": len(results)}

@app.get('/borrow-records/page')
def page_borrow_records(page: int = Query(1, ge=1), limit: int = Query(3, ge=1)):
    start = (page - 1) * limit
    end = start + limit
    paged = borrow_records[start:end]
    total = len(borrow_records)
    return {
        "total": total,
        "total_pages": 0 if total == 0 else -(-total // limit),
        "page": page,
        "limit": limit,
        "records": paged
    }

# ── Q5: Books Summary (Day 1) ──────────────────────────────────────────────
@app.get('/books/summary')
def get_books_summary():
    available = sum(1 for b in books if b['is_available'])
    borrowed = len(books) - available
    
    # Create genre breakdown dict
    genre_breakdown = {}
    for b in books:
        genre = b['genre']
        genre_breakdown[genre] = genre_breakdown.get(genre, 0) + 1
        
    return {
        'total_books': len(books),
        'available_count': available,
        'borrowed_count': borrowed,
        'genre_breakdown': genre_breakdown
    }

# ── Q10: Books Filter (Day 3) ──────────────────────────────────────────────
@app.get('/books/filter')
def filter_books(
    genre: str = Query(None), 
    author: str = Query(None), 
    is_available: bool = Query(None)
):
    result = filter_books_logic(genre, author, is_available)
    return {'filtered_books': result, 'count': len(result)}

# ── Q16: Books Search (Day 6) ──────────────────────────────────────────────
@app.get('/books/search')
def search_books(keyword: str = Query(...)):
    results = [
        b for b in books 
        if keyword.lower() in b['title'].lower() or keyword.lower() in b['author'].lower()
    ]
    return {"results": results, "total_found": len(results)}

# ── Q17: Books Sort (Day 6) ────────────────────────────────────────────────
@app.get('/books/sort')
def sort_books(sort_by: str = Query('title'), order: str = Query('asc')):
    if sort_by not in ['title', 'author', 'genre']:
        return {"error": "sort_by must be 'title', 'author', or 'genre'"}
    if order not in ['asc', 'desc']:
        return {"error": "order must be 'asc' or 'desc'"}
        
    reverse_sort = (order == 'desc')
    sorted_books = sorted(books, key=lambda b: b[sort_by], reverse=reverse_sort)
    return {"sort_by": sort_by, "order": order, "books": sorted_books}

# ── Q18: Books Page (Day 6) ────────────────────────────────────────────────
@app.get('/books/page')
def page_books(page: int = Query(1, ge=1), limit: int = Query(3, ge=1)):
    start = (page - 1) * limit
    end = start + limit
    paged = books[start:end]
    total = len(books)
    return {
        "total": total,
        "total_pages": -(-total // limit),
        "page": page,
        "limit": limit,
        "books": paged
    }

# ── Q20: Books Browse (Day 6) ──────────────────────────────────────────────
@app.get('/books/browse')
def browse_books(
    keyword: str = Query(None),
    sort_by: str = Query('title'),
    order: str = Query('asc'),
    page: int = Query(1, ge=1),
    limit: int = Query(3, ge=1)
):
    result = books
    
    # Filter
    if keyword:
        result = [b for b in result if keyword.lower() in b['title'].lower() or keyword.lower() in b['author'].lower()]
        
    # Sort
    if sort_by not in ['title', 'author', 'genre']:
        return {"error": "sort_by must be 'title', 'author', or 'genre'"}
    if order not in ['asc', 'desc']:
        return {"error": "order must be 'asc' or 'desc'"}
    reverse_sort = (order == 'desc')
    result = sorted(result, key=lambda b: b[sort_by], reverse=reverse_sort)
    
    # Paginate
    total_found = len(result)
    start = (page - 1) * limit
    end = start + limit
    paged = result[start:end]
    
    return {
        "keyword_used": keyword,
        "sort_settings": {"sort_by": sort_by, "order": order},
        "pagination": {
            "page": page, 
            "limit": limit, 
            "total_found": total_found, 
            "total_pages": 0 if total_found == 0 else -(-total_found // limit)
        },
        "results": paged
    }

# ── Q11: Add Book (Day 4) ──────────────────────────────────────────────────
@app.post('/books', status_code=status.HTTP_201_CREATED)
def add_book(new_book: NewBook, response: Response):
    for b in books:
        if b['title'].lower() == new_book.title.lower():
            response.status_code = status.HTTP_400_BAD_REQUEST
            return {"error": "Book title already exists"}
            
    new_id = max((b['id'] for b in books), default=0) + 1
    book_dict = {
        "id": new_id,
        "title": new_book.title,
        "author": new_book.author,
        "genre": new_book.genre,
        "is_available": new_book.is_available
    }
    books.append(book_dict)
    return {"message": "Book added successfully", "book": book_dict}

# ── Q8, Q9: Borrow Book (Day 2 & Day 3) ────────────────────────────────────
@app.post('/borrow')
def borrow_book(req: BorrowRequest):
    global record_counter
    book = find_book(req.book_id)
    
    if not book:
        return {"error": "Book not found"}
    if not book['is_available']:
        return {"error": "Book is already borrowed"}
        
    book['is_available'] = False
    due_date = calculate_due_date(req.borrow_days, req.member_type)
    
    record = {
        "record_id": record_counter,
        "member_name": req.member_name,
        "member_id": req.member_id,
        "book_id": req.book_id,
        "due_date": due_date
    }
    borrow_records.append(record)
    record_counter += 1
    return {"message": "Borrow confirmed", "record": record}

# ── Q14: Queue System (Day 5) ──────────────────────────────────────────────
@app.post('/queue/add')
def add_to_queue(member_name: str = Query(...), book_id: int = Query(...)):
    book = find_book(book_id)
    if not book:
        return {"error": "Book not found"}
    if book['is_available']:
        return {"error": "Book is currently available, you can borrow it directly!"}
        
    queue.append({"member_name": member_name, "book_id": book_id})
    return {"message": f"{member_name} added to waitlist for {book['title']}"}

@app.get('/queue')
def get_queue():
    return {"waitlist": queue, "total_waiting": len(queue)}

# ── Q15: Return Book Workflow (Day 5) ──────────────────────────────────────
@app.post('/return/{book_id}')
def return_book(book_id: int):
    global record_counter
    book = find_book(book_id)
    if not book:
        return {"error": "Book not found"}
        
    book['is_available'] = True
    
    # Check queue for this book
    for i, q_item in enumerate(queue):
        if q_item['book_id'] == book_id:
            waiting_member = queue.pop(i) # Remove from queue
            
            # Automatically create borrow record
            book['is_available'] = False
            due_date = calculate_due_date(15, 'regular') # Default 15 days for queue assignments
            
            new_record = {
                "record_id": record_counter,
                "member_name": waiting_member['member_name'],
                "book_id": book_id,
                "due_date": due_date
            }
            borrow_records.append(new_record)
            record_counter += 1
            
            return {
                "message": "returned and re-assigned", 
                "assigned_to": waiting_member['member_name'], 
                "record": new_record
            }

    return {"message": "returned and available"}


# ══ VARIABLE ROUTES (MUST BE AT THE VERY BOTTOM) ═══════════════════════════

# ── Q3: Get book by ID (Day 1) ─────────────────────────────────────────────
@app.get('/books/{book_id}')
def get_book_by_id(book_id: int):
    book = find_book(book_id)
    if not book:
        return {'error': 'Book not found'}
    return book

# ── Q12: Update Book (Day 4) ───────────────────────────────────────────────
@app.put('/books/{book_id}')
def update_book(
    book_id: int, 
    response: Response, 
    genre: str = Query(None), 
    is_available: bool = Query(None)
):
    book = find_book(book_id)
    if not book:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {"error": "Book not found"}
        
    if genre is not None:
        book['genre'] = genre
    if is_available is not None:
        book['is_available'] = is_available
        
    return {"message": "Book updated", "book": book}

# ── Q13: Delete Book (Day 4) ───────────────────────────────────────────────
@app.delete('/books/{book_id}')
def delete_book(book_id: int, response: Response):
    book = find_book(book_id)
    if not book:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {"error": "Book not found"}
        
    title = book['title']
    books.remove(book)
    return {"message": f"Successfully deleted '{title}'"}
