from hashlib import sha256
import json


def digest(raw):
    return sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, separators=(',', ':'), sort_keys=True, allow_nan=False).encode()
