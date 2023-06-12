#!/usr/bin/env python3

"""
Helper script that reads data from trace log and automatically plots it in kst plot
It checks how many channels that are setup, if a maximum has not been selected.
It checks the name of each channel
It fixes so the timestamps are correct
"""

import argparse
import os
import shutil
import subprocess


def tail(file, lines=1, _buffer=4098):
    """Tail a file and get X lines from the end"""
    # Place holder for the lines found
    lines_found = []

    # Block counter will be multiplied by buffer
    # to get the block size from the end
    block_counter = -1

    # Loop until we find X lines
    while len(lines_found) < lines:
        try:
            file.seek(block_counter * _buffer, os.SEEK_END)
        except IOError:  # Either file is too small, or too many lines requested
            file.seek(0)
            lines_found = file.readlines()
            break

        lines_found = file.readlines()

        # Decrement the block counter to get the
        # next X bytes
        block_counter -= 1

    return lines_found[-lines:]

def save_raw(output_filename, tempfilename):
    # Make sure file does not already exist
    destination = output_filename
    if (os.path.isfile(destination)):
        number = 1
        if "." in destination:
            full_name = destination.split(".")[0] + "_" + str(number) + "." + destination.split(".")[1]
            while os.path.isfile(full_name):
                number += 1
                full_name = destination.split(".")[0] + "_" + str(number) + "." + destination.split(".")[1]
            destination = full_name
        else:
            full_name = destination + "_"  + str(number)
            while os.path.isfile(full_name):
                number += 1
                full_name = destination + "_" + str(number)
            destination = full_name

    os.path.isfile(os.getcwd() + "/" + destination)

    shutil.copyfile(tempfilename, destination)

def main():
    """ Start function to plot in kst """
    parser = argparse.ArgumentParser(description="Automatically plot file in kst")
    parser.add_argument("--samples", "-n")
    parser.add_argument("--channels", "-c")
    parser.add_argument("--file", "-f")
    parser.add_argument("--sampling_freq", "-s")
    parser.add_argument("--save_raw", "-R", action='store_true', help="Save raw values to filename. If no name set, save to the same as the input")
    parser.add_argument("--save_pdf", "-P", action='store_true', help="Save pdf image")
    args = parser.parse_args()

    if not args.samples:
        args.samples = 1024

    if not args.sampling_freq:
        args.sampling_freq = 4000

    if not args.channels:
        args.channels = -1

    if not args.file:
        print("Need to specify file")
        return

    with open(args.file, 'r', encoding="UTF-8") as file:
        data = tail(file, int(args.samples) + 30) # Add some extra lines for trace metadata and newlines after trace dump

    # Find index where trace dump occurs
    prescaler_start_index = -1
    for index, line in enumerate(data):
        if "trace prescaler" in line:
            prescaler_start_index = index

    if prescaler_start_index == -1:
        print("Failed to find trace dump start")
        exit()

    prescaler = int(data[prescaler_start_index].strip().replace("trace prescaler ", ""))
    trigger = data[prescaler_start_index + 1].strip()
    channels = data[prescaler_start_index + 2].strip()
    channel_names = channels.split(" ")
    if int(args.channels) < 0:
        args.channels = len(channel_names) - channel_names.count("unknown")

    samples = data[prescaler_start_index + 3: prescaler_start_index + 3 + int(args.samples)]

    print(f"Prescaler: {prescaler}\nTrigger: {trigger}\nChannels: {channels}\n")

    tempfilename = os.getcwd() + "/tmp.txt"

    with open(tempfilename, "w", encoding="UTF-8") as file:
        for index, line in enumerate(samples):
            file.write(str(index * prescaler / int(args.sampling_freq)) + " " + line)

    channels = ['-x', '1']
    for index in range(0, int(args.channels)):
        channels += ['--xlabel', channel_names[index].replace("_", "\\_")]
        channels += ['--ylabel', " "]
        channels += ['-y', str(index+2)]
        index += 1

    if (args.save_raw):
        if (args.save_raw == True):
            if ("." in args.file):
                save_raw(args.file.split(".")[0] + ".raw", tempfilename)
            else:
                save_raw(args.file + ".raw", tempfilename)
        else:
            save_raw(args.save_raw)

    command = ['kst2', tempfilename, '-n', str(args.samples), '-m', "3"] + channels

    if (args.save_pdf):
        path, file = os.path.split(args.file)
        if (args.save_pdf == True):
            if ("." in file):
                command += ["--print", path + "/" + file.split(".")[0] + ".pdf"]
            else:
                command += ["--print", path + "/" + file + ".pdf"]
        else:
            command += ["--print", args.save_pdf]

    print(command)
    with subprocess.Popen(command, stdout=subprocess.PIPE) as proc:
        if proc.returncode:
            print(proc)

if __name__ == "__main__":
    main()
