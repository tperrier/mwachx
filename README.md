# Installation

You need to install [nodejs] first. [nvm], the node analog to [rvm] can be useful for getting node installed. 

You need Gulp installed globally:
```
$ npm i -g gulp
```

## Clone the repo:

```
$ git clone https://github.com/tperrier/mwachx.git
$ cd mwachx
```

## Install Javascript dependencies:

```
$ npm install
```

Behind the scenes this will also call `bower install`.  You should find that you have two new
folders in your project.

* `node_modules` - contains the npm packages for the tools we need
* `contacts/static/app/bower_components` - contains the libraries (e.g., Angular) that we are relying on

> **Note:** the `bower_components` folder would normally be installed in the root folder but
we change this location through the `.bowerrc` file.  Putting it in the `static/app` folder makes
it easier to serve the files by a webserver.


## Setup Python virtualenv and install dependencies

```
$ mkvirtualenv --no-site-packages mwachx
$ pip install -r requirements.txt
```

## Setup your settings files

```
$ echo "from .settings_base import *" > mwach/local_settings_2.py
```

## Setup database

```
$ ./manage.py migrate
```

## Start the backend and build the frontend with Gulp:
```
$ ./manage.py runserver
$ gulp
```

The default gulp command will start a [livereload] server on `localhost:8000`. The [chrome extension] is very useful.

# Project Todos

Support/upgrade to latest django


[nvm]:https://github.com/creationix/nvm
[rvm]:https://rvm.io/
[livereload]:http://livereload.com/
[chrome extension]:https://chrome.google.com/webstore/detail/livereload/jnihajbhpnppcggbcgedagnkighmdlei?hl=en
