from graphene import AbstractType, resolve_only_args, Field

from pikachu.analyser.fields import AnalyserField, AverageField
from pikachu.analyser.models import Request


class AnalyserQuery(AbstractType):
    all_requests = Field(AnalyserField)

    @resolve_only_args
    def resolve_all_requests(self):
        average_requests = list(Request.objects.aggregate(*[
            {
                "$project": {
                    "id": 1,
                    "endpoint": 1,
                    "start_time": 1,
                    "end_time": 1,
                    "delta": {"$subtract": ["$end_time", "$start_time"]}
                }
            },
            {
                "$group": {
                    "_id": "$endpoint",
                    "average_delta": {"$avg": "$delta"}
                }
            },
            {
                "$sort": {
                    "average_delta": -1
                }
            },
        ]))
        return AnalyserField(
            requests=Request.objects.all(),
            endpoints=[AverageField(
                average_request["_id"],
                average_request["average_delta"]
            ) for average_request in average_requests]
        )