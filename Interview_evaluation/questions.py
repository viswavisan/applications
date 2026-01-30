questions = [
    {
        "id": 1,
        "question": "Basic : write code to split odd and even in the range of 1 to 10.",
        "expected_output": "([2, 4, 6, 8, 10], [1, 3, 5, 7, 9])",
        "answer": ""
    },
    {
        "id": 2,
        "question": "Basic : flatten_dict({'a':1, 'b':{'b1':2}, 'c':[1,2,3], 'd':{'d1':{'d2':3}} })",
        "expected_output": "{'a': 1, 'b.b1': 2, 'c': [1, 2, 3], 'd.d1.d2': 3}",
        "answer": ""
    },
    {
        "id": 3,
        "question": "Basic : group_anagrams(words=['eat','tea','tan','ate','nat','bat'])",
        "expected_output": "[['eat', 'tea', 'ate'], ['tan', 'nat'], ['bat']]",
        "answer": ""
    },
    {
        "id": 4,
        "question": "Basic : verify_brackets ( '{[()]}' , '{[(])}' )",
        "expected_output": "True, False",
        "answer": ""
    },
    {
        "id": 5,
        "question": "OOPS : debug following class",
        "expected_output": """{'total': 3}
{'Laptop': 2}
{'Phone': 1}
{'product': 'Laptop'}""",
        "answer": """
class order:
    def __init__(self, product,count):
        self.total_orders += count
    def get_order_count(self):
        return {product:count}
    def get_dict(self):
        return laptop.__dict__
        
laptop = Order("Laptop",2)
phone = Order("Phone")

print(Order.total_orders)
print(laptop.get_order_count())
print(phone.get_order_count())
print(laptop.get_dict())
        
        """

    },
    {
        "id": 6,
        "question": "SQL Raw query: Get the names of employees who earn more than the average salary.",
        "expected_output": "['Alice', 'David']",
        "answer": """
import sqlite3

def run_query(query):
    conn = sqlite3.connect(':memory:')
    cursor = conn.cursor()
    cursor.execute(''' CREATE TABLE employees (id INTEGER PRIMARY KEY, name TEXT, salary REAL)''')
    cursor.executemany('INSERT INTO employees VALUES (?, ?, ?)', [(1, 'Alice', 70000),(2, 'Bob', 50000),(3, 'Charlie', 60000),(4, 'David', 80000),(5, 'Eve', 55000)])
    cursor.execute(query)
    results = [i[0] for i in cursor.fetchall()]
    conn.close()
    return results

print(run_query('''------------------------------'''))"""
    },
    {
        "id": 7,
        "question": "ORM : Get the names of students who got 5th highest marks by SQLAlchemy ORM",
        "expected_output": "['Grace']",
        "answer": """
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.sql import func

Base = declarative_base()

#table setup
class Student(Base):
    __tablename__ = 'students'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    marks = Column(Integer)

#db setup
engine = create_engine('sqlite:///:memory:')
Base.metadata.create_all(engine)
session = sessionmaker(bind=engine)()

# Sample data
students_data = [
    Student(name='Alice', marks=100),
    Student(name='Bob', marks=100),
    Student(name='Charlie', marks=99),
    Student(name='David', marks=99),
    Student(name='Eve', marks=98),
    Student(name='Frank', marks=96),
    Student(name='Grace', marks=95),
    Student(name='Tony', marks=95),
    Student(name='steve', marks=90),
]
session.add_all(students_data)
session.commit()

#answer
------------------------------------------
        """
    },
    {
        "id": 8,
        "question": "flask: Create a route /add that accepts a POST request with JSON \
        data containing two numbers a and b, and returns their sum in JSON.",
        "expected_output": "",
        "answer": """
                  
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/add')
def greet():
    _____________________
    ____________________
    if a is None or b is None:
        return jsonify({"error": "Missing numbers"}), 400
    return jsonify({"sum": a + b})

if __name__ == "__main__":
    _______________________


        """
    },
    {
        "id": 9,
        "question": "Test : Write a Pytest test for a function that adds two numbers.",
        "expected_output": "",
        "answer": ""
    },
    {
        "id": 10,
        "question": "pandas : merge dataframe",
        "expected_output": """
           id     name   salary
0   1    Alice  50000.0
1   2      Bob  60000.0
2   3  Charlie      NaN
3   4      NaN  70000.0

        """,
        "answer": """
import ________

df1 = ({
    "id": [1, 2, 3],
    "name": ["Alice", "Bob", "Charlie"]
})

df2 = pd.DataFrame({
    "id": [1, 2, 4],
    "salary": [50000, 60000, 70000]
})

# Outer join keeps all rows from both DataFrames
merged = ____________________
print(merged)
                  """
    }
    ]