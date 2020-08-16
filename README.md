Deptool
============
Copyright (c) 2018 Jose Manuel Sanchez Madrid. This file is licensed under MIT license. See file LICENSE for details.

## Overview
Deptool (Dependency Tool) is a pseudo package manager and dependency tool. It is mainly intended to install necessary dependecies of a software project that may be available only as source code and not as a binary package in most operating system's software repositories. Given a recipe, Deptool can download the source code of a program or library, compile it and install it in a subdirectory of the project, so it can be built without relying on the system to satisfy those dependencies. Deptool does download and install recursively necessary depencies to build the recipes.

The idea behind deptool is to fulfill the following requirements:
 - Easy install of dependent libraries and its dependencies recursively
 - Be able to install software and libraries without available package in the operating systems's software repository or other package/dependency manager repositories that rely on binary distribution
 - Be able to install software with no binary distribution and only source code available
 - Not depend on the software maintainer to support an speciffic packaging system
 - Not depend on a central package repository that require speciffic dedicated infrastructure
 - Be able to easely write new recipes that may or may not rely on other existing recipes
 - Be able to install all dependencies contained in a project's subfolder, to avoid messing arround with the system's itslef, so different projects can build independently regardless of conflicting versions. 
 - Be able to build software from source code, even in a different way than the software maintainer supports, if necessary

## Usage example
```
$ ./deptool.py  curl-7.54.1.yaml
```
This will download the source code of [curl](https://curl.haxx.se/) and its dependencies [OpenSSL](https://www.openssl.org/) and  [zlib](https://zlib.net/), it will compile then and install them a "build" subdirectory of the current working directory. Executable binaries will be installed in build/bin, libraries in build/lib, include files in build/include, source files in build/src/curl/7.54.1 for curl and the similar paths with their name and version for zlib and OpenSSL, and temporary files are created in /tmp/deptool.
A project written in c language that makes use of libcurl may be compiled then using the -I and -L optionsand can run by properly setting the LD\_LIBRARY\_PATH environment variable to use dynamic libraries not in /usr/lib or /usr/local/lib:
```
$ gcc -o myproject  myproject.c  -Ibuild/include -Lbuild/lib -lcurl
$ export LD_LIBRARY_PATH="${CWD}/build/lib:${LD_LIBRARY_PATH}"
$ ./myproject
```

Deptool can also run recipes given an url:
```
./depptool.py https://gitlab.com/chemasan/deptool-recipes/raw/master/curl-7.54.1.yaml
```

## Recipes
Recipes are yaml files describing how the software must be installed.

Example:
```yaml
name: curl
version: 7.61.0
check:
  - test -r ${LIBDIR}/libcurl.so
  - test -r ${INCDIR}/curl/curl.h
dependencies:
  - zlib-1.2.11.yaml
  - openssl-1.1.0i.yaml
download: https://github.com/curl/curl/releases/download/curl-7_61_0/curl-7.61.0.tar.gz  ${TMPDIR}/curl.tgz
install:
  - rm -rf ./*
  - tar xzf "${TMPDIR}/curl.tgz" && mv ${PKGDIR}/curl-${VERSION}/* ${PKGDIR}/
  - ./buildconf
  - ./configure --with-ssl=${PREFIX} --with-zlib=${PREFIX} --prefix=${PREFIX}
  - make
  - make install
```

A recipe has the following properties:
 - **name** (required): The name of the software package.
 - **version** (required): The version of the software package.
 - **check**: A list of commands to run in order to check the software package is installed. If all the commands return with an exit status 0, it is considered that the software package is already installed and the recipe is satisfied. If any command returns with an exit status non 0, it is considered that the software package is not installed.
 - **download**: A list of url's to download. Optionally the destination filename can be set. If the destination filename is not set, the url will be downloaded into ${TMPDIR} with the filename deduced from the URL. If the filename can't be deduced, it will be saved as _noname_. If destination filename is a directory, it saves de file into it. If destination path is in a non-existing directory, it creates the directory tree.
 - **dependencies**: A list of recipe files that is required to be installed before installing the recipe. URL's to the recipes can be used as well. Dependency recipes are ran if the _check_ determines the package is not installed, and they are ran before the _intall_.
 - **install**: A list of commands to run in order to install the software package. It is only ran if the _check_ determined that the package is not installed. It is ran after installing its dependencies. If all the commands return with an exit status 0, it is considered the package has been installed correctly. Otherwise if any command returns with exit status non 0, the execution is aborted and it is considered that the installation failed.

All properties that accept a list (check, download, dependencies, install) may accept an string instead if a single element is going to be set.
All elements in _check_ and _install_ lists are executed in different shell processes, with PKGDIR as working directory.
BINDIR is added to the path so the recipes can use binaries installed by their dependencies.
The following environment variables are exported and can be used in by the _check_ and _install_ commands, and in the destination filename in _download_:
 - NAME : The package name as set in the recipe's _name_ property.
 - VERSION : The package version as set in the recipe's _version_ property.
 - PROJECTDIR : The project's directory as set by the _--projectdir_ or _-p_ options, or the current working directory as default
 - PREFIX : The prefix path where all the files are installed. ${PROJECTDIR}/build by default.
 - SRCDIR : The directory path where the sources for all packages are stored. ${PREFIX}/src by default.
 - BINDIR : The directory path where the binaries are installed. ${PREFIX}/bin by default.
 - LIBDIR : The directory path where the libraries are installed. ${PREFIX}/lib by default.
 - INCDIR : The directory path where the library headers are installed. ${PREFIX}/include by default.
 - PKGDIR : The directory path where the source code for the current package is stored. ${SRCDIR}/${NAME}/${VERSION} by default.
 - TMPDIR : The directory path to be use as storage for temporary files. If no destination filename is set for the _download_, downloaded files are stored there. /tmp/deptool by default.

## TODO
 - [ ] Custom environment variables in recipes
 - [ ] Improve testing
 - [ ] Refactor of the main and get rid of non-used functions
 - [ ] Command options to set different paths independently
 - [ ] Scripts to publish releases
 - [ ] Dependencies file references are relative to the current recipe path
 - [ ] Option to reduce the output
