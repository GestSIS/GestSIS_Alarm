# GestSIS_Alarm (Tentative name)

Django app managing the alarm for GestSIS

## Structure

- The project name is `gestsis_alarm`, in it, there is two projects :
  - `admin_panel` containing all the code for the admin view
  - `mail_parser` containing all the code for retrieving mails and parsing the PDF in it

## Installation

### Using Docker

[TODO]

### Manually

#### Requirements

This project use Django Framework 4, so the project need at least **Python 3.8**

The requirements can be installed using the `requirements.txt` file.

For example, using a virtual environment :

1. Create a virtual environment
```bash
python -m venv .venv
```
2. Activate the environment
```
# Windows
.venv/Scripts/activate.bat
# Linux
source .venv/bin/activate
```
3. Install the dependencies
```
pip install -r requirements.txt
```
4. Run the initialisation script
```bash
python init.py
```
It will do two things :
  - Copy the`.env.example` file to `.env`
  - Populate the `.env` file with a secret key that will be used by Django

The script has done some jobs for you, but you need to do the last step :

5. Open the configuration file (`gestsis_alarm/.env`) and specify the missing values.

Theses are important because without them, the application won't function properly.

6. Finally, you can run the app !
```bash
python gestsis_alarm/manage.py runserver
```

## Usage

The project has one command that you can execute without running the web server:

### retrieve_mail

`retrieve_mail` is the command that allows you to check your mail server and see if there is mobilisation report that can be downloaded.

The usage is has follows:

```
$ python manage.py retrieve_mail -h
usage: manage.py retrieve_mail [-h] [--server SERVER] [--port PORT] [--username USERNAME] [--password PASSWORD]
                               [--whitelisted-mails WHITELISTED_MAILS [WHITELISTED_MAILS ...]] [--use-starttls]

Retrieve PDF from mail server and store it into the pdf folder

optional arguments:
  -h, --help            show this help message and exit
  --server SERVER       Url of the mail server
  --port PORT           Port of the mail server
  --username USERNAME   Can be a username or your email address depending on your email provider
  --password PASSWORD   Password to connect to your mail server
  --whitelisted-mails   The script will only download PDF from the mail addresses
  --use-starttls        If given, the connection to the mail server will use STARTTLS instead of IMAPs
```

For each parameter you don't provide, the script will check if the corresponding environment variable is available. If not, the command return an error.
The environment variables can be set manually using the method your OS gives you or you can populate the variable inside the `.env`. (They start with `GESTSIS_ALARM_MAIL_*`)

**NOTE:** The parameter on the command line takes precedence over the environment variable.

#### Example

```bash
# Retrieve all the variable from the environment 
python manage.py retrieve_mail

# Get username from the command line and the others variable from the environment
python manage.py retrieve_mail --username nobody@example.com

# Get the whitelisted mail and the server url from the command line and the others from the environment
python manage.py retrieve_mail --server mail.example.com --whitelisted-mails noreply@example.com report@example.com mobile@example.com
```
