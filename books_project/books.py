import dataclasses
from typing import Optional

from fastapi import FastAPI
from fastapi import HTTPException
from fastapi import Path
from fastapi import Query
from pydantic import BaseModel
from pydantic import Field
from starlette import status


app = FastAPI()


@dataclasses.dataclass
class Book:
    title: str
    author: str
    description: str
    rating: int
    id: int | None = None


class BookRequest(BaseModel):
    title: str = Field(min_length=3, description="Title of the book")
    author: str = Field(min_length=1, description="Author of the book")
    description: Optional[str] = Field(max_length=150, description="Short book description")
    rating: int = Field(ge=1, le=10)

    model_config = {
        "json_schema_extra": {
            "example": {
                "title": "A new book",
                "author": "Coder 1",
                "description": "A new book example",
                "rating": 10
            }
        }
    }


BOOKS = [
    Book(**{
        "id": i,
        "title": f"Title {i}",
        "author": f"Author {i}",
        "description": f"Description {i}",
        "rating": i % 10,
    }) for i in range(10)
]


@app.get("/books-all/", status_code=status.HTTP_200_OK)
async def read_all_books() -> list[Book]:
    return BOOKS


@app.get("/books/{book_id}", status_code=status.HTTP_200_OK)
async def get_book_by_id(book_id: int = Path(ge=0)) -> Book:
    for book in BOOKS:
        if str(book.id) == str(book_id):
            return book
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)


@app.get("/books-by-rating/", status_code=status.HTTP_200_OK)
async def read_book_by_rating(book_rating: int = Query(ge=0, le=10)) -> list[Book]:
    books = []
    for book in BOOKS:
        if book.rating == book_rating:
            books.append(book)
    return books


@app.post("/books/add", status_code=status.HTTP_201_CREATED)
async def create_book(book_body: BookRequest) -> Book:
    new_book = Book(**book_body.model_dump())
    new_book.id = len(BOOKS)
    BOOKS.append(new_book)
    return new_book


@app.put("/books/update/{book_id}", status_code=status.HTTP_200_OK)
async def update_book(updated_book: BookRequest, book_id: int = Path(ge=0)) -> Book:
    for i, book in enumerate(BOOKS):
        if book.id == book_id:
            updated_book: Book = Book(**{**updated_book.model_dump(), "id": book.id})
            BOOKS[i] = updated_book
            return updated_book
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
