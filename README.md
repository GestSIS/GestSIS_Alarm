# GestSIS_Alarm

Django app managing the alarm for GestSIS

## Structure

- The project name is `gestsis_alarm`, in it, there is two applications:
  - `admin_panel` containing all the code for the admin view
  - `mail_parser` containing all the code for retrieving mails and parsing the PDF in it

## Installation

### Using Docker

To use this project with Docker, you need to do the following steps:

1. `git clone` the project
2. Copy the`.env.example` file to `.env`
3. Specify the missing values in it (except for `GESTSIS_ALARM_SECRET_KEY`, it will be generated automatically)
4. Run Docker compose
```bash
docker-compose up -d
```
4. If you go to `http://127.0.0.1:8000`, you should see the django webpage

#### Access django terminal

If you want to access the terminal inside the docker container to run `manage.py` commands, you need to run the following command :
```bash
docker exec -it alarm bash
```
Or with docker-compose :
```bash
docker-compose exec alarm bash
```

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
    - By default, if a key is already set, it won't be overridden, add the argument `-f` to the script to force the generation of a new key

The script has done some jobs for you, but you need to do the last step :

5. Open the configuration file (`.env`) and specify the missing values.

Theses are important because without them, the application won't function properly.

6. Migrate the database
```
python manage.py migrate
```

7. Add initial data in the database
```
python manage.py loaddata sis
```

7. Finally, you can run the app !
```bash
python manage.py runserver
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
# Extract data from the pdf file named 'report.pdf' placed in the `storage` folder (Relative path)
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

## Databases

This project supports SQLite out of the box but you can change the engine for one supported by Django:
- MySQL/MariaDB
- PostgreSQL
- Oracle

To do that, you will need to change the `GESTSIS_DATABASE_URL` variable in the`.env` file and follow the url schema below :
```ini
# For SQLite
# (you can also add a dot (.) to make it relative to the gestsis_alarm folder)
GESTSIS_DATABASE_URL=sqlite:////absolute/path/to/db/file

# PostgreSQL
GESTSIS_DATABASE_URL=postgres://user:password@host:port/dbname

# For MySQL/MariaDB
GESTSIS_DATABASE_URL=mysql://user:password@host:port/dbname

# For Oracle
GESTSIS_DATABASE_URL=oracle://user:password@host:port/dbname
```

If you don't choose SQLite, **you will need to install additional dependencies** :
- MySQL/MariaDB : `mysqlclient` (`pip install mysqlclient`)
- PostgreSQL : `psycopg2` (`pip install psycopg2`)
- Oracle : [cx_Oracle driver](https://oracle.github.io/python-cx_Oracle/)

More infos available in the [Django documentation](https://docs.djangoproject.com/en/4.0/ref/databases/)

## Unit tests

This project comes with some unit tests to validate the code.
If you want to run them, run the following command :
```bash
python manage.py test
```
Theses tests are located in the `tests` folder of `mail_parser`
