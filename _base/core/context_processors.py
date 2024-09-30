from uuid import uuid4


def generate_uuid(request):
    return {'uuid': str(uuid4())}


def assets_base_url(request):
    return {'assets_base_url': 'https://upperoom.s3.amazonaws.com/assets'}
