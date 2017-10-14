"""First API, local access only"""
import hug
import os
import redis
import json

# try:
#     REDIS_URL = redis.from_url(os.environ.get("REDIS_URL"))
# except:
REDIS_URL = "redis://h:p5fb02a20cc28b27ca3b002543e7266b49df0ab1273719499c89a26d52f959d60@ec2-34-206-56-227.compute-1.amazonaws.com:52639"

demo_logins = {
    'username' : 'shelter',
    'password' : '1234'
}

user_db_id = 0
pet_db_id = 1

user = redis.from_url(REDIS_URL, db=user_db_id)
pet = redis.from_url(REDIS_URL, db=pet_db_id)

super_secret_key = 'abcd1234'

#login authentication
authentication = hug.http(requires=hug.authentication.basic(hug.authentication.verify('shelter', '1234')))

@authentication.get('/login')
@authentication.post('/login')
def login(user: hug.directives.user, key=super_secret_key):
    return {"message": "Successfully authenticated with user: {0}".format(user),
            "key" : key}

@hug.post('/owner')
def create_owner(body):
    username = body.get('username', None)
    body['role'] = "owner"
    #post owner to owner redis database
    user.set(username, body)
    return body

@hug.get('/owner')
def get_owner(body, username: hug.types.text = None):
    # get owner from user redis database
    if username is None:
        # get all owner records
        return user.keys()
    else:
        return user.get(username)


if __name__ == '__main__':
    user.interface.local()