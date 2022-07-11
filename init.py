import sys

from django.core.management.utils import get_random_secret_key
import os.path
import shutil
import fileinput

# Force replace of the SECRET_KEY if -f argument is given
force_replace = (len(sys.argv) > 1 and sys.argv[1] == "-f")

# Get the absolute path of the directory containing this file
file_dir = os.path.dirname(os.path.realpath(__file__))

ENV_FILENAME = os.path.join(file_dir, "gestsis_alarm", ".env")
ENV_EXAMPLE_FILENAME = os.path.join(file_dir, "gestsis_alarm", ".env.example")

# Create .env file from the example if the file isn't found
if not os.path.exists(ENV_FILENAME):
    print("Didn't find the .env file in the directory, copying from the template...")
    shutil.copyfile(ENV_EXAMPLE_FILENAME, ENV_FILENAME)
    print("Copy done !")

# With fileinput, the standard output is redirected to the file so print effectively write into the file

has_token_been_replaced = False

with fileinput.input(files=ENV_FILENAME, inplace=True) as f:
    for line in f:
        if line.strip().startswith("GESTSIS_ALARM_SECRET_KEY=") and \
                (line.strip() == "GESTSIS_ALARM_SECRET_KEY=" or force_replace):
            print("GESTSIS_ALARM_SECRET_KEY=\"{}\"".format(get_random_secret_key()))
            has_token_been_replaced = True
        else:
            print(line, end="")

if has_token_been_replaced:
    print("The SECRET_KEY has been set !")
else:
    print("The SECRET_KEY hasn't been changed (Already have one)")
