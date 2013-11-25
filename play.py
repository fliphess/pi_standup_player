#!/usr/bin/env python
import argparse
import os
import random
import re
import signal
import subprocess
import sys

#
# Settings
# 

# at work (raspberry pi)
#play_command = '/usr/bin/omxplayer -o hdmi %s & /bin/sleep 20 ; /usr/bin/killall omxplayer.bin'
# at home (vlc)
play_command = '/usr/bin/vlc %s & /bin/sleep 20 ; /usr/bin/killall vlc'

# the command used to download youtube clips
download_command = "cd %s ; youtube-dl --max-quality 35 '%s'"

# the url where to get the clips (supported by youtube-dl)
url = 'http://www.youtube.com/watch?v=%s'

# 
# Functions
#

def log(output):
    if not parse_options()['quiet']:
        sys.stdout.write("%s" % output)

def parse_options():
    """ Get options and return arguments
    """
    parser = argparse.ArgumentParser(description="""
    Downloads the tunes from the settings file daily if not present
    And plays a song on our raspberry pi as long as the given duration.
    """)
    parser.add_argument('-c', '--cron', help='Download the listed tunes', action="store_true")
    parser.add_argument('-p', '--play', help='Play a random song from the tunesdir', action="store_true")
    parser.add_argument('-d', '--dir', help='The dir where the songs are stored', required=True, type=str)
    parser.add_argument('-l', '--list', help='List with ids to download from youtube', default='./all_tunes_listing')
    parser.add_argument('-q', '--quiet', help='Be silent', action="store_true")
    arguments = vars(parser.parse_args())

    if not arguments['cron'] and not arguments['play']:
        print "See --help for usage"
        raise Exception("Not enough arguments: Use -d and -c or -p")
    return arguments

def signal_handler(signal, frame):
    """ Handle ctrl+C
    """
    print "\nHa! You pressed Ctrl+C! Quitting as requested"
    sys.exit(0)

def run_local_command(command):
    output = ''
    try:
        output = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT,)
    except Exception as e:
        raise Exception("Error: %s: %s" % (command, e)) 
    if output == '': 
        output = 'No output for run_local_command: %s' % (command)
    return output

def get_tunes_from_youtube(tunesfile, args):
    """ Download al ID's from youtube using youtube-dl 
    """
    with open(tunesfile) as fh:
        content = fh.readlines()

    for item in content:
        try:
            command = download_command % (args['dir'], url % item)
            output = run_local_command(command)
        except Exception as e:
            raise Exception('Command %s Failed: %s' % (command, e))
        log(output)

def play_random_tune_from_dir(args):
    listing = [ f for f in os.listdir(args['dir']) if os.path.isfile(os.path.join(args['dir'], f)) ]
    random_tune = os.path.join(args['dir'], random.choice(listing))
    random_tune = re.escape(random_tune)
    command = play_command % random_tune
    try:
        output = run_local_command(command)
    except Exception as e: 
        raise Exception('Failed to run command %s: %s' % (command, e))
    log(output)
 

# 
# The main routine
# 
def main():
    """ The main routine 
    """
    try:
        args = parse_options()
    except Exception as e:
        raise Exception('Error: I did not understand your input! %s' % e)

    if not os.path.isdir(args['dir']):
        raise Exception('Error: Tunes dir %s not found!' % args['dir'])
    if not os.path.isfile(args['list']):
        raise Exception('Error: Tunes file %s not found!' % args['list'])
        
    for i in ('/usr/bin/vlc', '/usr/bin/youtube-dl'):
        if not os.path.isfile(i) and not os.access(i, os.X_OK):
            raise Exception('Error: command %s is not executable!' % i)

    if args['cron']:
        try:
            get_tunes_from_youtube(args['list'], args)
        except Exception as e:
            raise Exception('Error: Failed to download tunes from file %s to dir %s. Output was %s' % (args['list'], args['dir'], e))
    else:
        try:
            play_random_tune_from_dir(args)
        except Exception as e:
            raise Exception('Error: Failed to play random tune from dir %s. Output was %s' % (args['dir'], e))


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)    # catch ctrl+c 
    try:
        main()
    except Exception as e:
        print "Error in %s! Output was %s" % (sys.argv[0], e)
        sys.exit(1)
    sys.exit(0)

