import csv
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session,sessionmaker

engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

def main():
    f = open("books.csv")
    reader = csv.reader(f)
    next(reader, None)
    for number, title, author, publication in reader: 
        db.execute("INSERT INTO books (isbn_no, title, author, pub_year) VALUES (:isbn_no, :title, :author, :publication)",
            {"isbn_no": number, "title": title, "author": author, "publication": publication })
        print(f"added {title}book by {author} which is published in {publication},its isbn number is{number}.")
    db.commit()

if __name__== "__main__":
    main()