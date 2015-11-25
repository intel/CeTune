import babeltrace
import sys
import argparse
import json
from collections import OrderedDict

def main(args):
    parser = argparse.ArgumentParser(description='Analyzer tool')
    parser.add_argument(
        '--path',
        )
    parser.add_argument(
        '--output',
        )
    args = parser.parse_args(args)

    traces = babeltrace.TraceCollection()
    lttng_input = args.path
    if args.output:
        output_path = args.output
    else:
        output_path = "result.json"
    ret = traces.add_trace( lttng_input, "ctf" )

    result = OrderedDict()
    for event in traces.events:
        if 'trace_id' not in event:
            continue
        trace_id = event['trace_id']
        span_id = event['span_id']
        parent_span_id = event['parent_span_id']
#       init new op
        if trace_id not in result:
            result[trace_id] = OrderedDict()
            if parent_span_id not in result[trace_id]:
                result[trace_id][parent_span_id] = OrderedDict()
            result[trace_id][parent_span_id][span_id] = init_zipkin_data( event )
            zipkin_data = result[trace_id][parent_span_id][span_id]
            result[trace_id]["start_timestamp"] = event.timestamp
            if 'event' in event:
                zipkin_data["events"][event['event']] = event.timestamp - result[trace_id]["start_timestamp"]
            elif 'key' in event and 'val' in event:
                zipkin_data[event['key']] = event['val']
#       add this tracepoint into a leveled op
        else:
            zipkin_data = init_zipkin_data_by_parent_span_id( parent_span_id, result[trace_id], event, result[trace_id]["start_timestamp"] )

    with open(output_path, 'w') as f:
        json.dump(result, f, indent=4)

def init_zipkin_data_by_parent_span_id( parent_span_id, root, event, start_time ):
    span_id = event["span_id"]
    if parent_span_id in root:
        root = root[parent_span_id]
        if span_id not in root:
            root[span_id] = init_zipkin_data( event )
        zipkin_data = root[span_id]
        if 'event' in event:
            zipkin_data["events"][event['event']] = event.timestamp - start_time
        elif 'key' in event and 'val' in event:
            tmp_key = event['key']
            tmp_index = 1
            while tmp_key in zipkin_data:
                tmp_key = "%s_%d" % (tmp_key, tmp_index)
                tmp_index += 1
            zipkin_data[tmp_key] = event['val']
        return
    else:
        for span_id in root.keys():
            if not isinstance(span_id, int):
                continue
            init_zipkin_data_by_parent_span_id( parent_span_id, root[span_id], event, start_time )
        return

def init_zipkin_data( event ):
    zipkin_data = OrderedDict()
    zipkin_data["service_name"] = event['service_name']
    zipkin_data["trace_name"] = event['trace_name']
    zipkin_data["events"] = OrderedDict()
    return zipkin_data


if __name__ == '__main__':
    import sys
    main(sys.argv[1:])
