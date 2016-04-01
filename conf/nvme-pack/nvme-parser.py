import os
import sys
import argparse
import json
from collections import OrderedDict

class NVMeParser(object):
    def __init__(self, path="/usr/local/bin"):
        self.nvmetool_path = path

    def find_attr_start_line(self, lines, min_line=4, max_line=9):
        """
        Return line number of the first real attribute and value.
        The first line is 0.  If the 'ATTRIBUTE_NAME' header is not
        found, return the index after max_line.
        """
        for idx, line in enumerate(lines[min_line:max_line]):
            col = line.split()
            if len(col) > 1 and col[1] == 'ATTRIBUTE_NAME':
                return idx + min_line + 1

        print('ATTRIBUTE_NAME not found in second column of'
                      ' smartctl output between lines %d and %d.'
                      % (min_line, max_line))

        return max_line + 1

    def parse_output(self, attributes, start_offset=0, end_offset=-1):
        import string

        att_list = attributes.split('\n')
        att_list = att_list[start_offset:end_offset]
        dev_info=OrderedDict()
        for att in att_list:
            att_kv = att.split(':')
            if not att_kv[0]: continue
            if len(att_kv) > 1:
                dev_info[string.strip(att_kv[0])] = string.strip(att_kv[1])
            else:
                dev_info[string.strip(att_kv[0])] = ''

        return dev_info

    def get_smart_info(self, device, output):
        smart_info_dict = OrderedDict()
        smart_info_dict['nvme_basic'] = OrderedDict()
        smart_info_dict['nvme_smart'] = OrderedDict()
        smart_info_dict['nvme_smart_additional_info'] = OrderedDict()

        if "/dev/nvme" in device:
            #print("This is a nvme device : " + device)
            dev_info = OrderedDict()
            dev_smart_log = OrderedDict()
            dev_smart_add_log = OrderedDict()

            import commands

            # get nvme device meta data
            err, attributes =  commands.getstatusoutput('sudo %snvme id-ctrl ' % self.nvmetool_path + device)
            if not err:
                basic_info_dict = self.parse_output(attributes)
                #print("basic_info_dict=" + str(basic_info_dict))
                smart_info_dict['nvme_basic']['Drive Family'] = basic_info_dict.get('mn') or ''
                smart_info_dict['nvme_basic']['Serial Number'] = basic_info_dict.get('sn') or ''
                smart_info_dict['nvme_basic']['Firmware Version'] = basic_info_dict.get('fr') or ''
                smart_info_dict['nvme_basic']['Drive Status'] = 'PASSED'
            else:
                smart_info_dict['nvme_basic']['Drive Status'] = 'WARN'
                print("Fail to get device identification with error: " + str(err))

            # get nvme devic smart data
            err, attributes = commands.getstatusoutput('sudo %snvme smart-log ' % self.nvmetool_path + device)
            if not err:
                dev_smart_log_dict = self.parse_output(attributes, 1)
                #print("device smart log=" + str(dev_smart_log_dict))
                smart_info_dict['nvme_smart'].update(dev_smart_log_dict)
            else:
                smart_info_dict['nvme_basic']['Drive Status'] = 'WARN'
                print("Fail to get device smart log with error: " + str(err))

            # get nvme device smart additional data
            err, attributes = commands.getstatusoutput('sudo %snvme smart-log-add ' % self.nvmetool_path + device)
            if not err:
                dev_smart_log_add_dict = self.parse_output(attributes, 2)
                #print("device additional smart log=" + str(dev_smart_log_add_dict))
                #smart_info_dict['smart']['<<< additional smart log'] = ' >>>'
                smart_info_dict['nvme_smart_additional_info'].update(dev_smart_log_add_dict)
            else:
                smart_info_dict['nvme_basic']['Drive Status'] = 'WARN'
                print("Fail to get device additional (vendor specific) smart log with error: "  + str(err))

        with open(output, 'w') as f:
           json.dump(smart_info_dict, f, indent=4)
        return smart_info_dict


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='NVME INFO Parser')
    parser.add_argument(
        '--output',
        )
    parser.add_argument(
        'device',
        help = 'only support redeploy now',
        )
    parser.add_argument(
        '--tool_path',
    )
    args = parser.parse_args(sys.argv[1:])
    device=args.device
    parser = NVMeParser(args.tool_path)
    parser.get_smart_info(device, args.output)

