from sanic import Sanic
from sanic.response import json
from pymongo import MongoClient
app = Sanic(__name__)


client = MongoClient('mongodb://localhost:27017/')
db = client['library']
async def insert_book(book_data):
    try:
        collection = db['books']
        result = collection.insert_one(book_data)
        return result.inserted_id
    except Exception as e:
        return str(e)
@app.route('/books', methods=['GET'])
async def get_all_books(request):
    try:
        collection = db['books']
        books = collection.find({})
        return json([{
            'id': str(book['_id']),
            'title': book['title'],
            'description': book['description']
        } for book in books])
    except Exception as e:
        return json({'error': str(e)})
@app.route('/book/<id>', methods=['GET'])
async def get_book_by_id(request, id):
    try:
        collection = db['books']
        book = collection.find_one({'_id': ObjectId(id)})
        if book:
            return json({
                'id': str(book['_id']),
                'title': book['title'],
                'description': book['description']
            })
        else:
            return json({'error': 'Book not found'})
    except Exception as e:
        return json({'error': str(e)})
@app.route('/book/create', methods=['POST'])
async def create_book(request):
    try:
        book_data = request.json
        book_id = await insert_book(book_data)
        return json({'id': str(book_id)})
    except Exception as e:
        return json({'error': str(e)})
@app.route('/book/update', methods=['PUT'])
async def update_book(request):
    try:
        book_data = request.json
        book_id = book_data.get('id')
        if book_id:
            collection = db['books']
            result = collection.update_one({'_id': ObjectId(book_id)}, {'$set': book_data})
            if result.modified_count > 0:
                return json({'message': 'Book updated successfully'})
            else:
                return json({'error': 'Book not found'})
        else:
            return json({'error': 'Missing book id'})
    except Exception as e:
        return json({'error': str(e)})
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)