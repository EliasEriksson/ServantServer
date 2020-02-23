from typing import *
import pickle
from io import BytesIO
from math import ceil


def cls_to_bytes(cls: Type[object]) -> bytes:
    attrs = {attr: value for attr, value in cls.__dict__.items()
             if not attr.startswith("__") or not attr.startswith("_")}

    bites = b"".join([str(attr).encode() + str(value).encode() for attr, value in attrs.items()])
    return bites


class Colors:
    green = 0
    blue = 1


with BytesIO() as file:
    pickle.dump(cls_to_bytes(Colors), file)
    file.seek(0)
    first_color = file.read()


class Colors:
    green = 0
    blue = 1
    red = 2


with BytesIO() as file:
    pickle.dump(cls_to_bytes(Colors), file)
    file.seek(0)
    second_color = file.read()

print(first_color == second_color)

with BytesIO(first_color) as file:
    file.seek(0)
    obj1 = pickle.load(file)
    print(obj1)
    # print(obj1.__dict__)


with BytesIO(second_color) as file:
    file.seek(0)
    obj2 = pickle.load(file)
    print(obj2)
    # print(obj2.__dict__)

print(obj1 == obj2)

