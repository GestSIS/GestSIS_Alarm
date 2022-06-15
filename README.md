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

#### Populate the environment

You need to specify some variables before running the application. Luckily, the project have a template file :)

You can use the helper script `init_key.py` to do the step 4 and 5 for you if you want.

4. Copy the `.env.example` file to `.env` (It's in the `gestsis_alarm` folder)
```bash
cp gestsis_alarm/.env.example gestsis_alarm/.env
```
5. Generate a secret key and put it into the `.env` file (`GESTSIS_ALARM_SECRET_KEY`).
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

#### Start !

6. Finally, you can run the app !
```bash
python gestsis_alarm/manage.py runserver
```