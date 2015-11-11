import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as pyplot
import json
import argparse
from collections import OrderedDict
import os

def main(args):
    parser = argparse.ArgumentParser(description='Analyzer tool')
    parser.add_argument(
        '--path',
        )
    parser.add_argument(
        '--output',
        )
    parser.add_argument(
        '--return_type',
        )

    args = parser.parse_args(args)

    output_name = "latency_line"
    if (args.output):
        output_name = args.output
    path = "result.json"
    if (args.path):
        path = args.path
    return_type = "events"
    if (args.return_type):
        return_type = args.return_type
    with open( path ) as data_file:
        data = json.load(data_file, object_pairs_hook=OrderedDict)

    if not os.path.exists("%s" % output_name):
        os.mkdir("%s" % output_name)
    output_name = "%s/%s" % (output_name, output_name)

    if return_type == "service_latency":
        latency_dict = get_res(data, "service_latency")
        for msg_type, trace in latency_dict.items():
            pyplot.figure(figsize=(9,4))
            for lat_level, lat_data in trace.items():
                if lat_level == "Messenger":
                    continue
                pyplot.plot(lat_data.keys(), lat_data.values(), "o", label=lat_level)
            pyplot.xlabel("start_time(msec)")
            pyplot.ylabel("latency(msec)")
            pyplot.legend(loc = 'center left', bbox_to_anchor = (1, 0.5), prop={'size':6})
            pyplot.grid(True)
            x1,x2,y1,y2 = pyplot.axis()
            pyplot.axis((x1,x2,0,y2))
            pyplot.suptitle("%s" % "blkin_trace")
            pic_name = '%s_%s.png' % (output_name, msg_type)
            pyplot.savefig(pic_name)
            pyplot.close()

    elif return_type == "events":
        events_dict = get_res(data, "events")
        for msg_type, trace in events_dict.items():
            output = []
            first_line = True
            for start_time, events in trace.items():
                if first_line:
                    output.append( 'start_time,%s' % ','.join(events.keys()) )
                    first_line = False
                output.append( "%s,%s" % (start_time, ",".join(events.values())) )
            with open( "%s_%s.csv" % (output_name, msg_type), 'w' ) as f:
                f.write( "\n".join(output) )
#    print latency_dict.keys()


def get_res( data, return_type ):
    res = OrderedDict()
    first_start_time = None
    for trace_id, trace_data in data.items():
        trace_start = trace_data["start_timestamp"]
        if not first_start_time:
            first_start_time = trace_start

        if return_type == "events":
            trace_res = OrderedDict()
            msg_type = get_sublevel( trace_start, trace_data, trace_res, first_start_time, return_type )
            if msg_type not in res:
                res[msg_type] = OrderedDict()
            res[msg_type][(trace_start-first_start_time)/1000000] = trace_res

        elif return_type == "service_latency":
            get_sublevel( trace_start, trace_data, res, first_start_time, return_type )
    return res

def get_sublevel( trace_start, trace_data, res, first_start_time, return_type, msg_type=None ):
    for span_id, span_data in trace_data.items():
        if not span_id.isdigit():
            continue

        # only handle span_id:span_data dict
        if return_type == "service_latency":
            msg_type = get_service_lat( trace_start, span_data, res, first_start_time, msg_type )

        if return_type == "events":
            msg_type_tmp = get_events_list( trace_start, span_data, res, first_start_time )
            if msg_type_tmp != None:
                msg_type = msg_type_tmp

        if contains_sublevel( span_data ):
            msg_type_tmp = get_sublevel( trace_start, span_data, res, first_start_time, return_type, msg_type )

            if msg_type_tmp != None:
                msg_type = msg_type_tmp

    return msg_type

def contains_sublevel( span_data ):
    for key in span_data:
        if key.isdigit():
            return True
    return False

def get_service_lat(trace_start, span_data, res, first_start_time, msg_type):
    level_name = "trace_name"
    if "Messenger_type" in span_data:
        msg_type = span_data["Messenger_type"]
    if msg_type not in res:
        res[msg_type] = OrderedDict()
    if level_name in span_data:
        service_name = span_data[level_name]
        first_event = span_data["events"].keys()[0]
        last_event = span_data["events"].keys()[-1]
        lat = span_data["events"][last_event] - span_data["events"][first_event]
        key = (trace_start - first_start_time)/1000000
        value = "%.3f" % float(lat/1000000.0)
        if service_name not in res[msg_type]:
            res[msg_type][service_name] = OrderedDict()
        res[msg_type][service_name][key] = value
    return msg_type

def get_events_list(trace_start, span_data, res, first_start_time):
    level_name = "trace_name"
    if "events" in span_data:
        for event, timestamp in span_data["events"].items():
            value =  "%.3f" % float(timestamp/1000000.0)
            event = "%s_%s" % (span_data[level_name], event)
            res[event] = value
    if "Messenger_type" in span_data:
        return span_data["Messenger_type"]

if __name__ == '__main__':
    import sys
    main(sys.argv[1:])
