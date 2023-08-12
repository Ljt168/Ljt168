import pymongo
from sanic import Sanic
from sanic.response import json
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
import json as json_module

app = Sanic(__name__)

mongodb_uri = "mongodb://localhost:27017"
database_name = '20211103046'


# 创建Database类，用于处理与MongoDB的连接和操作
class Database:
    def __init__(self, uri, database_name):
        self.client = AsyncIOMotorClient(uri)
        self.db = self.client[database_name]


    async def insert(self, collection_name, document):
        try:
            collection = self.db[collection_name]
            await collection.insert_one(document)
        except Exception as e:
            # 处理异常，例如记录日志或返回错误信息
            print(f"Failed to insert document: {str(e)}")

    def find(self, collection_name, query=None):
        try:
            collection = self.db[collection_name]
            return collection.find(query)
        except Exception as e:
            # 处理异常，例如记录日志或返回错误信息
            print(f"Failed to find documents: {str(e)}")

    async def update(self, collection_name, query, update):
        try:
            collection = self.db[collection_name]
            await collection.update_many(query, update)
        except Exception as e:
            # 处理异常，例如记录日志或返回错误信息
            print(f"Failed to update documents: {str(e)}")

    async def delete(self, collection_name, query):
        try:
            collection = self.db[collection_name]
            await collection.delete_many(query)
        except Exception as e:
            # 处理异常，例如记录日志或返回错误信息
            print(f"Failed to delete documents: {str(e)}")

    # 跨表
    # 获取具有特定权限的用户
    async def get_users_with_permission(self, permission):
        try:
            users = self.db['users']
            permissions = self.db['permissions']
            result = await users.aggregate([
                {
                    '$lookup': {
                        'from': 'permissions',
                        'localField': 'permission_name',  # 修改为正确的权限字段
                        'foreignField': 'name',
                        'as': 'user_permissions'
                    }
                },
                {
                    '$match': {
                        'user_permissions.name': permission
                    }
                }
            ]).to_list(length=None)
            return result
        except Exception as e:
            print(f"Failed to get users with permission: {str(e)}")


# 创建UserService类，用于定义与用户相关的操作
class UserService:
    def __init__(self, database):
        self.db = database

    async def get_all_users(self):
        users = self.db.find('users')
        return [user async for user in users]

    async def get_user(self, id):
        user = await self.db.find('users', {'_id': ObjectId(id)}).to_list(length=None)
        if user:
            return user[0]
        else:
            return None

    async def create_user(self, data):
        await self.db.insert('users', data)
        return {'message': 'User created successfully'}

    async def update_user(self, id, data):
        query = {'_id': ObjectId(id)}
        update = {'$set': data}
        await self.db.update('users', query, update)
        return {'message': 'User updated successfully'}

    async def delete_user(self, id):
        query = {'_id': ObjectId(id)}
        await self.db.delete('users', query)
        return {'message': 'User deleted successfully'}
#权限管理
class PermissionService:
    def __init__(self, database):
        self.db = database
    async def get_all_permissions(self):
        permissions = self.db.get_all_permissions()
        return [permission async for permission in permissions]

    async def create_permission(self, data):
        await self.db.insert_permission(data)
        return {'message': 'Permission created successfully'}

    async def update_permission(self, name, data):
        query = {'name': name}
        update = {'$set': data}
        await self.db.update_permission(query, update)
        return {'message': 'Permission updated successfully'}

    async def delete_permission(self, name):
        query = {'name': name}
        await self.db.delete_permission(query)
        return {'message': 'Permission deleted successfully'}
#部门
class DepartmentService:
    def __init__(self, database):
        self.db = database
    async def get_all_departments(self):
        departments = self.db.get_all_departments()
        return [department async for department in departments]

    async def create_department(self, data):
        await self.db.insert_department(data)
        return {'message': 'Department created successfully'}

    async def update_department(self, name, data):
        query = {'name': name}
        update = {'$set': data}
        await self.db.update_department(query, update)
        return {'message': 'Department updated successfully'}

    async def delete_department(self, name):
        query = {'name': name}
        await self.db.delete_department(query)
        return {'message': 'Department deleted successfully'}
#跨表
    async def get_users_with_permission(self, permission):
        users = await self.db.get_users_with_permission(permission)
        return users

    # 自动化脚本建表
    async def create_tables(self):
        # 创建users集合，并定义字段
        await db.client[database_name].create_collection('users')
        users_collection = db.db['users']
        await users_collection.create_index("username", unique=True)
        users_collection.create_index("department")
        users_collection.create_index("position")

        # 创建permissions集合，并定义字段
        await db.client[database_name].create_collection('permissions')
        permissions_collection = db.db['permissions']
        await permissions_collection.create_index("name", unique=True)
        permissions_collection.create_index("permission")

        # 创建departments集合，并定义字段
        await db.client[database_name].create_collection('departments')
        departments_collection = db.db['departments']
        await departments_collection.create_index("name", unique=True)
        departments_collection.create_index("parent")

    # 添加用于创建表的API端点
    @app.route("/tables/create", methods=["POST"])
    async def create_tables_handler(request):
        await request.create_tables()
        return custom_json({'message': 'Tables created successfully'})


# 创建数据库实例
db = Database(mongodb_uri, database_name)
# 创建用户服务实例
user_service = UserService(db)
permission_service = PermissionService(db)
department_service = DepartmentService(db)


# 自定义JSONEncoder类，用于处理将MongoDB的ObjectId转换为字符串格式
class CustomJSONEncoder(json_module.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        return super().default(obj)

# 自定义json函数，用于将数据编码为JSON格式并返回相应
def custom_json(response_data, status=200):
    encoded_data = json_module.dumps(response_data, cls=CustomJSONEncoder)
    return json(encoded_data, status=status, content_type="application/json")

# 异常处理函数，用于处理请求过程中发生的异常
@app.exception(Exception)
async def handle_exception(request, exception):
    error_message = str(exception)
    return custom_json({'message': error_message}, status=500)

# 添加用于用户管理的API端点
@app.route("/users", methods=["GET"])
async def get_all_users(request):
    users = await user_service.get_all_users()
    return custom_json(users)

@app.route("/user/create", methods=["POST"])
async def create_user(request):
    data = request.json
    if data is None:
        return custom_json({'message': 'Invalid request data'}, status=400)
    result = await user_service.create_user(data)
    if result is None:
        return custom_json({'message': 'Failed to create user'}, status=500)
    return custom_json(result)

@app.route("/user/update/<username>", methods=["PUT"])
async def update_user(request, username):
    data = request.json
    if data is None:
        return custom_json({'message': 'Invalid request data'}, status=400)
    result = await user_service.update_user(username, data)
    if result is None:
        return custom_json({'message': 'Failed to update user'}, status=500)
    return custom_json(result)

@app.route("/user/delete/<username>", methods=["DELETE"])
async def delete_user(request, username):
    result = await user_service.delete_user(username)
    if result is None:
        return custom_json({'message': 'Failed to delete user'}, status=500)
    return custom_json(result)

#权限管理
@app.route("/permissions", methods=["GET"])
async def get_all_permissions(request):
    permissions = await permission_service.get_all_permissions()
    return custom_json(permissions)

@app.route("/permission/create", methods=["POST"])
async def create_permission(request):
    data = request.json
    if data is None:
        return custom_json({'message': 'Invalid request data'}, status=400)
    result = await permission_service.create_permission(data)
    if result is None:
        return custom_json({'message': 'Failed to create permission'}, status=500)
    return custom_json(result)

@app.route("/permission/update/<name>", methods=["PUT"])
async def update_permission(request, name):
    data = request.json
    if data is None:
        return custom_json({'message': 'Invalid request data'}, status=400)
    result = await permission_service.update_permission(name, data)
    if result is None:
        return custom_json({'message': 'Failed to update permission'}, status=500)
    return custom_json(result)

@app.route("/permission/delete/<name>", methods=["DELETE"])
async def delete_permission(request, name):
    result = await permission_service.delete_permission(name)
    if result is None:
        return custom_json({'message': 'Failed to delete permission'}, status=500)
    return custom_json(result)
#部门
@app.route("/departments", methods=["GET"])
async def get_all_departments(request):
    departments = await department_service.get_all_departments()
    return custom_json(departments)

@app.route("/department/create", methods=["POST"])
async def create_department(request):
    data = request.json
    if data is None:
        return custom_json({'message': 'Invalid request data'}, status=400)
    result = await department_service.create_department(data)
    if result is None:
        return custom_json({'message': 'Failed to create department'}, status=500)
    return custom_json(result)

@app.route("/department/update/<name>", methods=["PUT"])
async def update_department(request, name):
    data = request.json
    if data is None:
        return custom_json({'message': 'Invalid request data'}, status=400)
    result = await department_service.update_department(name, data)
    if result is None:
        return custom_json({'message': 'Failed to update department'}, status=500)
    return custom_json(result)

@app.route("/department/delete/<name>", methods=["DELETE"])
async def delete_department(request, name):
    result = await department_service.delete_department(name)
    if result is None:
        return custom_json({'message': 'Failed to delete department'}, status=500)
    return custom_json(result)

#跨表
@app.route("/users/permission/<permission>", methods=["GET"])
async def get_users_with_permission(request, permission):
    users = await user_service.get_users_with_permission(permission)
    return custom_json(users)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
