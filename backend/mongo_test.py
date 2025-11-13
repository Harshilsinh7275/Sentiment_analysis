


from pymongo import MongoClient

try:
    client = MongoClient("mongodb+srv://cse190840131065_db_user:Admin123@cluster0.jkltzas.mongodb.net/?appName=Cluster0")
    print(client.server_info())
except Exception as e:
    print("Error:", e)