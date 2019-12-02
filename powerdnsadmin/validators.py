import os
from bravado_core.spec import Spec
from bravado_core.validate import validate_object
from yaml import load, Loader


def validate_zone(zone):
    validate_object(spec, zone_spec, zone)


def validate_apikey(apikey):
    validate_object(spec, apikey_spec, apikey)


def get_swagger_spec(spec_path):
    with open(spec_path, 'r') as spec:
        return load(spec.read(), Loader)


bravado_config = {
    'validate_swagger_spec': False,
    'validate_requests': False,
    'validate_responses': False,
    'use_models': True,
}

dir_path = os.path.dirname(os.path.abspath(__file__))
spec_path = os.path.join(dir_path, "swagger-spec.yaml")
spec_dict = get_swagger_spec(spec_path)
spec = Spec.from_dict(spec_dict, config=bravado_config)
zone_spec = spec_dict['definitions']['Zone']
apikey_spec = spec_dict['definitions']['ApiKey']
