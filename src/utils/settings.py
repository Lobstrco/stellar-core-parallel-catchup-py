import os

# node secret key (generate with stellar core generator)
node_secret_key = os.environ.get('NODE_SECRET_KEY')
if not node_secret_key:
    raise RuntimeError("secret key not set. please add NODE_SECRET_KEY environment variable")

# database connection
db_host = os.environ.get('DB_HOST', default='localhost')
db_port = os.environ.get('DB_PORT', default=5432)
db_user = os.environ.get('DB_USER', default='user')
db_password = os.environ.get('DB_PASSWORD', default='password')
