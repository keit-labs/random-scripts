# Control Tower Setup
Scripts used in AWS Control Tower Work

## Common dependancies 

Using [pipenv](https://pipenv.pypa.io/en/latest/), install the required python modules.
~~~bash
pipenv install
Creating a virtualenv for this project…
Pipfile: /Users/richardkeit/git/richardkeit/random-scripts/Pipfile
Using /usr/local/opt/python@3.7/bin/python3 (3.7.12) to create virtualenv…
⠼ Creating virtual environment...created virtual environment CPython3.7.12.final.0-64 in 212ms
  creator CPython3Posix(dest=/Users/richardkeit/git/richardkeit/random-scripts/.venv, clear=False, no_vcs_ignore=False, global=False)
  seeder FromAppData(download=False, pip=bundle, setuptools=bundle, wheel=bundle, via=copy, app_data_dir=/Users/richardkeit/Library/Application Support/virtualenv)
    added seed packages: pip==22.3.1, setuptools==65.6.3, wheel==0.38.4
  activators BashActivator,CShellActivator,FishActivator,NushellActivator,PowerShellActivator,PythonActivator

✔ Successfully created virtual environment! 
Virtualenv location: /Users/richardkeit/git/richardkeit/random-scripts/.venv
Installing dependencies from Pipfile.lock (4b0547)…
  🐍   ▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉ 7/7 — 00:00:02
To activate this project's virtualenv, run pipenv shell.
Alternatively, run a command inside the virtualenv with pipenv run.
~~~

## Enroll old AWS Accounts


Using [enroll_account.py](enroll_account.py), create the required role for enrolling an existing account in AWS Control Tower

#### Assumptions:
This script assumes that you are either:
1. Logged into the Management Account in your AWS Organizations
1. Logged into the destinaton account with the relevant permissions


##### Logged into Management Account
~~~bash
pipenv run python enroll_account.py --aws-account-id XXXXX

[2022-12-28 16:21:25,098] {credentials.py:1120} INFO - Found credentials in environment variables.
[2022-12-28 16:21:26,114] {enroll_account.py:28} WARNING - Not in correct account, will use OrganizationAccountAccessRole to assume access into XXXXXX
[2022-12-28 16:21:27,147] {enroll_account.py:97} INFO - Creating Role
~~~

#####
