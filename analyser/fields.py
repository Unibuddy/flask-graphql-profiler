from graphene import ObjectType, String, List


class RequestField(ObjectType):
    id = String()
    endpoint = String()
    start_time = String()
    end_time = String()
    delta = String()


class AverageField(ObjectType):
    endpoint = String()
    average_delta = String()


class AnalyserField(ObjectType):
    requests = List(RequestField)
    endpoints = List(AverageField)