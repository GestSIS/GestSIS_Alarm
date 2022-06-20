from django.core.management.utils import get_random_secret_key
import os.path
import shutil
import fileinput

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
with fileinput.input(files=ENV_FILENAME, inplace=True) as f:
    for line in f:
        if line.strip().startswith("GESTSIS_ALARM_SECRET_KEY="):
            print("GESTSIS_ALARM_SECRET_KEY=\"{}\"".format(get_random_secret_key()))
        else:
            print(line, end="")

print("The SECRET_KEY has been set !")
