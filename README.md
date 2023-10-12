# UserProfile

* Python (3.8, 3.9)
* Django (3.0, 3.1)

We **highly recommend** and only officially support the latest patch release of
each Python and Django series.


## Installation
The first thing to do is to clone the repository:

```sh
$ https://github.com/VAIBHAV-BODHANE/UserProfile.git
$ cd UserProfile/profile_manger
```

Create a virtual environment to install dependencies in and activate it:

```sh
$ virtualenv -p python3.8 venv
$ source env/bin/activate
```
Then install the dependencies:

```sh
(venv)$ pip install -r requirements.txt
```
Note the `(venv)` in front of the prompt. This indicates that this terminal
session operates in a virtual environment set up by `virtualenv`.

Once `pip` has finished downloading the dependencies:
```sh
(env)$ python manage.py makemigrations
(env)$ python manage.py migrate
(env)$ python manage.py runserver
```
