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

6. Add initial data into the database
```
python gestsis_alarm/manage.py loaddata sis
```

7. Finally, you can run the app !
```bash
python gestsis_alarm/manage.py runserver
```

## Usage

The project has two commands that you can execute without running the web server:

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

### extract_pdf

`extract_pdf` is the command that extract data from a mobilisation report (PDF file).

```bash
$ python manage.py extract_pdf -h
usage: manage.py extract_pdf [-h]
                             pdf_file

Extract data from the mobilisation report

positional arguments:
  pdf_file              Path to the pdf file, can be absolute or relative. If relative, the root folder is 'storage'

optional arguments:
  -h, --help            show this help message and exit
```

#### Example

```bash
# Extract data from the pdf file named 'report.pdf' placed in the `gestsis_alarm/storage` folder (Relative path)
python manage.py extract_pdf report.pdf

# Extract data from the pdf file named 'mobilisation.pdf' placed in the folder `/home/public/reports' (Absolute path)
python manage.py extract_pdf /home/public/reports/mobilisation.pdf 
```

### mail_and_extract

This command combine the actions of `retrieve_mail` and `extract_pdf` into one command. 
It is intended to be used in a cronjob.
**Contrary to `extract_pdf` the filename of the PDF will be added in the database.**
It uses the environment variables for the mail settings, and it can't be overwritten by command line parameters.

#### Example

```bash
python manage.py mail_and_extract
```

## Unit tests

This project comes with some unit tests to validate the code.
If you want to run them, go to the `gestsis_alarm` folder (it contains the `manage.py` file) and run the following command :
```bash
python manage.py test
```
Theses tests are located in the `tests` folder of `mail_parser`
