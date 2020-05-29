import argparse
import datetime
import json
import re
import subprocess

def mfs_dumpobj(fsids=[]):

    for id in fsids:
        if args.debug:
            print("Finding info on " + str(id))

        s = subprocess.check_output(
            "/home/ben/mfs-utils/bin.Linux-x86_64/mfs_dumpobj -rj {}".format(id),
            shell=True,
            universal_newlines=True)

        if "RecordingPart" in s:  # This fsid has data related to a recording, so let's proceed
            # Fixing up the JSON output from mfs_dumpobj for our purposes here
            s = s.replace('\n"],', '"]')  # Fixing Multi-line empty array
            s = s.replace(',\n}', '\n}')  # Removing , from last item within an object
            s = re.sub('},(?!\n")', '}', s)  # Removing trailing comma from the last object
            s = re.sub(' \d+/\d{2}', '', s)  # Removing fsid/part from titles
            # s = re.sub('[^a-zA-z0-9 ,]', '', s)  # Removing most non-alphanumeric chars
            # s = re.sub('(\[")|("\])', '\\1""" \\2"""', s)
            # s = re.sub('(\w\s+)\"(\w)|\"\s+(\w)', '\\1 \\2', s)  # TODO: Need to fix this regex
            s = re.sub('\"+', '\"', s)
            

            if args.debug:
                print(type(s))
                print('{' + s + '}')

            # Make a call to print stream detail
            fsid_json = json.loads('"""{' + s + '}"""')
            fsid_json['fsid'] = id

            stream_detail(fsid_json)


def stream_detail(input={}):
    if args.debug:
        print(input)

    result = {}
    result['fsid'] = input['fsid']
    result['title'] = input['Program']['Title'][0]
    try:
        result['desc'] = input['Program']['Description'][0]
    except:
        result['desc'] = "No Description Provided"
    try:
        result['network'] = input['Station']['Name'][0]
    except:
        result['network'] = "No Network Provided"
    try:
        result['stream_size'] = int(input['Recording']['StreamFileSize'][0].strip(',')) / 1000  # MB
    except:
        result['stream_size'] = 0.000
    try:
        result['start_date'] = int(input['Recording']['StartDate'][0].strip(','))
        # Calculating human readable date from TiVo epoch time
        result['start_date'] = datetime.datetime.fromtimestamp(
        int(input['Recording']['StartDate'][0].strip(',')) * 86400).strftime('%Y-%m-%d')
    except:
        result['start_date'] = "No Start Date Provided"
    try:
        #  Calculating human readable time from TiVo epoch time
        result['start_time'] = datetime.datetime.fromtimestamp(
            int(input['Recording']['StartTime'][0].strip(','))).strftime('%H:%M:%S')
    except:
        result['start_time'] = "No Start Date Provided"
    try:
        result['duration'] = int(input['Showing']['Duration'][0].strip(',')) / 60
    except:
        result['duration'] = 0.000
    try:
        stream_path = set([i.split(':')[0].split('/')[1] for i in input['Recording']['IndexPath'][0].split(',')])
    except:
        stream_path = "No stream path"

    if 'Theme' in input:
        result['theme'] = input['Theme']['KeywordPhrase'][0]

    print("{:<12} {:<17.15} {:<43.40} {:<20.18} {:<10} {:<10} {:<2.0f} min   {:<4.2f} MB  /{}".format(
        result['fsid'],
        result['title'],
        result['desc'],
        result['network'],
        result['start_date'],
        result['start_time'],
        int(result['duration']),
        int(result['stream_size']),
        stream_path,
    ))


def get_all_fsids():
    s = subprocess.check_output(
            "mfs_ls -R / |grep tyDb |awk '{print $1}'",
            shell=True,
            universal_newlines=True)

    fsids = [int(i) for i in s.split('\n') if i]

    # Remove duplicate fsids
    fsids = list(set(fsids))

    return fsids


def parse_args():
    parser = argparse.ArgumentParser(
        description='Provides information on all TiVo video found within a TiVo MFS')

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-f', '--fsid',
    nargs='+',
    help="Provide one or more FSIDs to query as a space-separated list")

    group.add_argument('-a', '--all',
        action='store_true',
        help="Provide information for all video found on the TiVo MFS. \
            Depending on the size of your TiVo MFS, this may take several \
            minutes to complete.")

    parser.add_argument('--debug',
        action='store_true',
        help='Output JSON data')

    return parser.parse_args()
    


if __name__ == "__main__":
    args = parse_args()

    if args.fsid:
        mfs_dumpobj(args.fsid)

    if args.all:
        fsid_list = get_all_fsids()

        print("""
        Processing {} FSIDs...
        This will likely take several minutes to complete, and
        only FSIDs which may have video will be reported on.\n""".format(
            len(fsid_list)))
        
        mfs_dumpobj(fsid_list)
