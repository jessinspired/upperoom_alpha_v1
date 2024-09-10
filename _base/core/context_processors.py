from uuid import uuid4


def generate_uuid(request):
    return {'uuid': str(uuid4())}
