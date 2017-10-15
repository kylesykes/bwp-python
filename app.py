"""First API, local access only"""
import hug
import os
import redis
import json
import base64
from xmlrpc.client import Binary
import uuid



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

"""
HELPER FUNCTIONS
"""
def get_uuid():
    return str(uuid.uuid4())

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

@hug.options('/document', requires=cors_support)
def options():
    return

"""
USER ROUTES
"""

@hug.post('/owner', requires=cors_support)
def create_owner(body):
    if body.get('username', None) is None:
        return {"message" : "Bad person, you need a username"}
    username = body.get('username', None)
    body['role'] = "owner"
    body['adopted_pets'] = []
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
    pet_uuid = get_uuid()
    pet_name = body.get('name', None)
    temp_key = '{}:{}'.format(pet_name, 'test')
    
    body['adopted'] = False
    
    #post pet to pet redis database
    pet.set(temp_key, json.dumps(body))
    # add id to response
    body['pet_id'] = pet_uuid
    return body


@hug.get('/pet', requires=cors_support)
def get_pet(pet_id: hug.types.text = None):
    # get pet from user redis database
    if pet_id is None:
        # get all pet records
        return pet.keys()
    else:
        return json.loads(pet.get(pet_id))


"""
LINKING ROUTES
"""

@hug.post('/link', requires=cors_support)
def link_owner_pet(body):
    pet_id = body['pet_id']
    owner_id = body['owner_username']

    #get and alter owner dict
    owner_object = json.loads(user.get(owner_id))
    adopted_pet_list = owner_object.get('adopted_pets', [])
    if pet_id not in adopted_pet_list:
        adopted_pet_list.append(pet_id)
    owner_object['adopted_pets'] = adopted_pet_list

    # get and update pet object to show adopted
    pet_object = json.loads(pet.get(pet_id))
    pet_object['adopted'] = True
    pet_object['adopted_by'] = owner_id

    # send updates to redis
    pet.set(pet_id, json.dumps(pet_object))
    user.set(owner_id, json.dumps(owner_object))
    return {
            'owner': owner_object,
            'pet' : pet_object
    }


"""
DOCUMENTS
"""


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
CREATE DEMO STUFF
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