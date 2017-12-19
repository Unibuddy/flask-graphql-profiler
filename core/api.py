import logging
from datetime import datetime

import os
from flask import Blueprint, current_app
from flask_graphql import GraphQLView
from flask_jwt import jwt_required, JWTError, current_identity
from graphql import execute
from raygun4py import raygunprovider

from pikachu.analyser.recorder import get_endpoint, record_request
from pikachu.core.schema import schema

logger = logging.getLogger(__package__)

graphql_api = Blueprint('api', __name__, url_prefix='')

environment = os.getenv('DATABASE', default='DEV')
graphiql = environment == 'DEV'


class PikachuGraphQLView(GraphQLView):
    def execute(self, *args, **kwargs):
        endpoints = get_endpoint(self.schema, *args, **kwargs)
        self.endpoints = endpoints if endpoints else []
        return execute(self.schema, *args, **kwargs)

    def execute_graphql_request(self, *args, **kwargs):
        """Time the request and send any exceptions to Raygun"""
        start = datetime.now
        self.endpoints = []
        result = super().execute_graphql_request(*args, **kwargs)
        end = datetime.now
        record_request(start_time=start, end_time=end, endpoints=self.endpoints)
        if result is not None and result.errors and not current_app.config.get('TESTING'):
            raygun_sender = raygunprovider.RaygunSender(
                current_app.config.get('RAYGUN_ACCESS_TOKEN')
            )

            @jwt_required()
            def set_user():
                raygun_sender.set_user({
                    'firstName': current_identity.first_name,
                    'fullName': '{0} {1}'.format(
                        current_identity.first_name,
                        current_identity.last_name
                    ),
                    'email': current_identity.email,
                    'isAnonymous': False,
                    'identifier': current_identity.email
                })

            try:
                set_user()
            except JWTError:
                pass

            for error in result.errors:
                try:
                    raise error.original_error
                except:
                    raygun_sender.send_exception()
        return result


graphql_api.add_url_rule(
    '/graphql',
    view_func=PikachuGraphQLView.as_view(
        'graphql',
        schema=schema,
        graphiql=graphiql,
    )
)