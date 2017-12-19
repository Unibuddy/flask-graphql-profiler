from mongoengine import *


class Request(Document):
    endpoint = StringField(required=True)
    start_time = DateTimeField(required=True)
    end_time = DateTimeField(required=True)