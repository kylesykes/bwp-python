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


@hug.options('/link', requires=cors_support)
def options_link():
    return

@hug.options('/document', requires=cors_support)
def options_document():
    return

@hug.options('/pet', requires=cors_support)
def options_pet():
    return

@hug.options('/owner', requires=cors_support)
def options_owner():
    return

@hug.options('/breeds', requires=cors_support)
def options_breeds():
    return

@hug.options('/reminder', requires=cors_support)
def options_reminder():
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
    first_name = body.get('firstName', '')
    last_name = body.get('lastName', '')
    body['adopted_pets'] = []
    body['owner_id'] = 'owner:{}:{}:{}'.format(first_name, last_name, username)
    #post owner to owner redis database
    user.set(body['owner_id'], json.dumps(body))
    
    return body

def get_owner_keys():
    owners = [Id.decode("utf-8") for Id in user.keys() if 'doc:' not in Id.decode("utf-8")]
    return owners


@hug.get('/owner', requires=cors_support)
def get_owner(owner_id: hug.types.text = None):
    # get owner from user redis database
    if owner_id is None:
        # get all user record keys
        return get_owner_keys()
    else:
        # return user record
        return json.loads(user.get(owner_id))


@hug.get('/owner_by_username', requires=cors_support)
def get_owner_by_username(username: hug.types.text = None):
    owner_keys = get_owner_keys()
    username_keys = [key for key in owner_keys if username in key]
    if len(username_keys) == 1:
        username_key = username_keys[0]
        return json.loads(user.get(username_key))
        # return username_key
    elif len(username_keys) == 0:
        return {
            "message": "No key with username exists or multiple people with same username."
        }


"""
PET ROUTES
"""

@hug.post('/pet', requires=cors_support)
def create_pet(body):
    pet_uuid = get_uuid()
    pet_name = body.get('name', None)
    temp_key = '{}:{}'.format(pet_name, pet_uuid)
    
    body['adopted'] = False

    #put doc_ids on pet
    body['documents'] = get_document_ids()
    body['pet_id'] = pet_uuid

    #post pet to pet redis database
    pet.set(temp_key, json.dumps(body))

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
    owner_id = body['owner_id']

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
REMINDER ROUTES
"""
def get_keys(key_type):
    keys = [Id.decode("utf-8") for Id in user.keys() if '{}:'.format(key_type) in Id.decode("utf-8")]
    return keys


def get_reminder_keys():
    reminders = [Id.decode("utf-8") for Id in user.keys() if 'reminder:' in Id.decode("utf-8")]
    return reminders


@hug.post('/reminder', requires=cors_support)
def add_reminder(body):
    reminder_id = get_uuid()
    body['reminder_id'] = 'reminder:{}'.format(reminder_id)
    user.set(body['reminder_id'], json.dumps(body))
    return body

@hug.get('/reminder', requires=cors_support)
def get_reminder(reminder_id: hug.types.text = None):
    if reminder_id is None:
        # get all reminder_ids
        reminder_ids = get_keys(key_type='reminder')
        return reminder_ids
    else:
        # get specific reminder_id object
        reminder_object = user.get(reminder_id)
        return json.loads(reminder_object)

"""
QUERIES
"""

@hug.get('/breeds', requires=cors_support)
def get_breed_list():
    with open('data/breed_list.txt', 'r') as r:
        breed_list = json.loads(r.read())
    return breed_list


@hug.get('/adopted_pet_numbers', requires=cors_support)
def adopted_pet_numbers():
    pets_adopted = []
    pet_ids = pet.keys()
    
    for pet_id in pet_ids:
        pet_object = json.loads(pet.get(pet_id))
        if pet_object['adopted'] == True:
            pets_adopted.append(pet_id)
    
    payload = {
        'total' : len(pet_ids),
        'adopted' : len(pets_adopted)
    }
    return payload


"""
DOCUMENTS
"""

def get_document_ids():
    user_keys = user.keys()
    document_ids = [Id.decode("utf-8") for Id in user_keys if 'doc:' in Id.decode("utf-8")]
    return document_ids

@hug.get('/document', requires=cors_support)
def get_document(document_id: hug.types.text = None):
    if document_id is None:
        return get_document_ids()
    else:
        encoded_document = user.get(document_id)
        return encoded_document


"""
IMAGES
"""

# @hug.get('/image.png', output=hug.output_format.png_image)
# def get_image_for_breed():
#     return '../artwork/logo.png'

"""
CREATE DEMO STUFF
"""
@hug.get('/demo_setup', requires=cors_support)
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

    # clear owner db
    user.flushdb()
    # clear pet db
    pet.flushdb()

    #add encoded_documents to redis
    with open('docs/encoded_documents.txt', 'r') as r:
        encoded_doc_list = json.loads(r.read())
    for i, encoded_doc in enumerate(encoded_doc_list):
        user.set('doc:{}'.format(i), encoded_doc)

    return {'message' : "Success"}




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