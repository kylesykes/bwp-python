"""First API, local access only"""
import hug
import os
import redis
import json
import base64
from xmlrpc.client import Binary



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

def cors_support(response, *args, **kwargs):
    response.set_header('Access-Control-Allow-Origin', '*')
    response.set_header('Access-Control-Allow-Method', 'POST, GET, OPTIONS')
    response.set_header('Access-Control-Allow-Headers', 'Content-Type')


@hug.options('/owner', requires=cors_support)
def options():
    return

@hug.options('/pet', requires=cors_support)
def options():
    return

"""
USER ROUTES
"""

@hug.post('/owner', requires=cors_support)
def create_owner(body):
    username = body.get('username', None)
    body['role'] = "owner"
    #post owner to owner redis database
    user.set(username, json.dumps(body))
    return body


@hug.get('/owner', requires=cors_support)
def get_owner(username: hug.types.text = None):
    # get owner from user redis database
    if username is None:
        # get all user record keys
        return user.keys()
    else:
        # return user record
        return json.loads(user.get(username))

"""
PET ROUTES
"""

@hug.post('/pet', requires=cors_support)
def create_pet(body):
    name = body.get('name', None)
    #post pet to pet redis database
    pet.set(name, json.dumps(body))
    return body


@hug.get('/pet', requires=cors_support)
def get_pet(name: hug.types.text = None):
    # get pet from user redis database
    if name is None:
        # get all pet records
        return pet.keys()
    else:
        return json.loads(pet.get(name))


"""
CREATE KENNEL USER
"""
@hug.post('/demo_setup', requires=cors_support)
def demo_setup():
    demo_user = {
        'username' : 'shelter',
        'password' : '1234',
        'firstName' : 'Jane',
        'lastName' : 'Goodall',
        'email' : 'jane@purina.com',
        'phoneNumber' : '314-123-4567',
        'role' : 'user'
    }


@hug.post('/document', requires=cors_support)
def get_document():
    test_document_path = 'docs/rabies_cert.pdf'

    with open(test_document_path, "rb") as f:
        encodedZip = base64.b64encode(f.read())
    return {
            'message' : "Successfully transmitted",
            'base64' : encodedZip.decode("utf-8") 
    }


"""
CLEAR REDIS DATABASE
"""

@hug.post('/clear_redis', requires=cors_support)
def clear_redis():
    try:
        # clear owner db
        user.flushdb()
        # clear pet db
        pet.flushdb()
        return True
    except:
        return False


if __name__ == '__main__':
    user.interface.local()