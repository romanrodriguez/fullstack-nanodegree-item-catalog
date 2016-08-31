# Item Catalog

## Project Overview
Application that provides a list of items within a variety of categories as well as provide a user registration and authentication system. Registered users will have the ability to post, edit and delete their own items.

## Prerequisites
All the project's files are in the `catalog folder`. Outside of it is this `README`, and a `Vagrantfile` and `pg_config.sh` for you to easily run this project. You need to have [Vagrant](https://www.vagrantup.com/) and [VirtualBox](https://www.virtualbox.org/wiki/Downloads) installed in your system.

You could also run the project localy by installing the following in your system:
pip install werkzeug==0.8.3
pip install flask==0.9
pip install Flask-Login==0.1.3
You should also have Python and SQLAlquemy installed.

To ensure an faster and more streamlined setup, we are going to use the first method here.

## Instructions
1. Download this project to your computer. 
You can clone the repo with the following command: git clone https://github.com/romanrodriguez/fullstack-nanodegree-item-catalog.git
2. Unzip it, and `cd` into it on the command line.
3. Enter `vagrant up`, followed by `vagrant ssh`
4. `cd` into `/vagrant/catalog`
5. Now we create the database. Run `python database_setup.py` to do so.
6. We populate the database with some items so that we don't start with an empty environment. Run `python populate_catalog_database.py`.
7. At last we can run the application. Run `python catalog.py`.
8. To see the application up locally, head over to `http://localhost:5000`.
9. To see the JSON, head over to `localhost:5000/catalog/json/`.

