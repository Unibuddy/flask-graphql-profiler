import asyncio
from threading import Thread

from graphql.execution.base import ExecutionContext, get_operation_root_type, collect_fields
from graphql.pyutils.default_ordered_dict import DefaultOrderedDict

from pikachu.analyser.models import Request


async def call_ext_service(start, end, endpoints, loop):
    requests = [Request(
        endpoint=endpoint,
        start_time=start,
        end_time=end,
    ) for endpoint in endpoints]
    Request.objects.insert(requests)
    if loop.is_running():
        loop.stop()


def start_analyser_worker(loop):
    asyncio.set_event_loop(loop)
    loop.run_forever()


def get_endpoint(the_schema, document_ast, root_value=None, context_value=None, variable_values=None,
                 operation_name=None, executor=None, middleware=None):
    context = ExecutionContext(
        the_schema,
        document_ast,
        root_value,
        context_value,
        variable_values,
        operation_name,
        executor,
        middleware
    )

    the_type = get_operation_root_type(context.schema, context.operation)
    fields = collect_fields(
        context.schema,
        the_type,
        context.operation.selection_set,
        DefaultOrderedDict(list),
        set()
    )
    return [str(field) for field in fields]


def record_request(start_time, end_time, endpoints):
    new_loop = asyncio.new_event_loop()
    t = Thread(target=start_analyser_worker, args=(new_loop,))
    t.start()
    # Call the graphql analyser in a new thread so the response to client is not delayed
    asyncio.run_coroutine_threadsafe(call_ext_service(start_time, end_time, endpoints, new_loop), loop=new_loop)