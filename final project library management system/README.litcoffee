# FastAPI Library Book Management System 📚

A complete backend REST API built with FastAPI for managing a library's book inventory and borrow/return workflows. Built as the final project for the FastAPI Internship.

## 🚀 Features Implemented
* **CRUD Operations:** Create, Read, Update, and Delete books from the inventory.
* **Pydantic Validation:** Strict data validation for all incoming POST/PUT requests.
* **Multi-Step Workflows:** Users can borrow books (decreases stock), return books (increases stock), and view their borrow history.
* **Advanced Routing:** Search by keyword, sort by fields, and paginate results all in a single `/books/browse` endpoint.
* **Error Handling:** Graceful 404s and 400s (e.g., trying to borrow an out-of-stock book).

## 🛠️ Tech Stack
* Python 3
* FastAPI
* Pydantic
* Uvicorn

## 🚦 How to Run
1. Install dependencies: `pip install -r requirements.txt`
2. Start the server: `uvicorn main:app --reload`
3. Open Swagger UI: `http://127.0.0.1:8000/docs`