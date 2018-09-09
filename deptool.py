#!/usr/bin/env python

import os
import re
import yaml
import shutil
import argparse
import subprocess
import requests

def sanitizeStrList(strlist):
    if (not isinstance(strlist, list)): return [ str(strlist) ]
    mylist = []
    for element in strlist: mylist.append(str(element))
    return mylist

def expandPath(path):
	expanded = os.path.expandvars(path)
	expanded = os.path.expanduser(expanded)
	return expanded

def getUrlFileName(url):
    path = re.sub("^https?\:\/\/","",url,1, re.IGNORECASE)
    path = re.sub("^[^\/]*","",path,1)
    splitted = path.split("/")
    filename = splitted[-1]
    if filename: return filename
    return "noname"

class Recipe(object):
    def __init__(self, recipeDict):
        if not isinstance(recipeDict, dict):  raise ValueError("Invalid recipe")
        self.name = recipeDict.get("name","")
        if (self.name == ""):  raise ValueError("Invalid name")
        self.version = recipeDict.get("version","0")
        self.dependencies = recipeDict.get("dependencies", [])
        if (not isinstance(self.dependencies, list)):  raise ValueError("Invalid dependencies")
        self.install = sanitizeStrList( recipeDict.get("install", []) )
        self.check = sanitizeStrList( recipeDict.get("check", []) )
        self.download = sanitizeStrList( recipeDict.get("download", []) )
    
    @staticmethod
    def loadFile(filePath):
        with open(filePath) as recipeFile:
            yamlRecipe = yaml.load(recipeFile)
        return Recipe(yamlRecipe)

class FailedCommandError(RuntimeError):
    pass

class FailedRecipeError(RuntimeError):
    pass

def setEnv(cmdconfig, recipe):
    os.environ["NAME"] = recipe.name
    os.environ["PKGNAME"] = recipe.name
    os.environ["VERSION"] = recipe.version
    os.environ["PROJECTDIR"] = cmdconfig.projectdir
    os.environ["PREFIX"] = cmdconfig.prefix
    os.environ["SRCDIR"] = cmdconfig.srcDir
    os.environ["BINDIR"] = cmdconfig.binDir
    os.environ["LIBDIR"] = cmdconfig.libDir
    os.environ["INCDIR"] = cmdconfig.incDir
    os.environ["PKGDIR"] = cmdconfig.pkgDir
    os.environ["TMPDIR"] = cmdconfig.tmpDir
    pathVar = os.getenv("PATH","")
    if cmdconfig.binDir not in pathVar.split(":"): os.environ["PATH"] = "{}:{}".format(cmdconfig.binDir,pathVar)

def createDir(directory):
    if not os.path.exists(directory): os.makedirs(directory)

def ensureDirs(cmdconfig):
    createDir(cmdconfig.prefix)
    createDir(cmdconfig.srcDir)
    createDir(cmdconfig.binDir)
    createDir(cmdconfig.libDir)
    createDir(cmdconfig.incDir)
    createDir(cmdconfig.tmpDir)
    createDir(cmdconfig.pkgDir)

def retrieveUrl(url, filename):
    response = requests.get(url, stream=True)
    if response.status_code != 200: raise RuntimeError("Server returned code '{}'".format(response.status_code))
    with open(filename,"wb") as f:  shutil.copyfileobj(response.raw,f)

def loadRemoteRecipe(url, cacheDir):
    destdir = "{}/{}".format(cacheDir, re.sub("^(https?\:\/\/)","",url,1))
    recipeFile = "{}/recipe.yaml".format(destdir)
    createDir(destdir)
    retrieveUrl(url, recipeFile)
    return Recipe.loadFile(recipeFile)

def run(commands):
    for command in sanitizeStrList(commands):
        print command
        result = subprocess.call(command, shell=True)
        if (result != 0): raise FailedCommandError("Command '{}' returned with code '{}'".format(command, result))

def installDeps(dependencies, config):
    for dependency in dependencies:
        print "Installing dependency '{}'"
        result = subprocess.call([config.exe, "--projectdir", config.projectdir, dependency])
        if result != 0: raise FailedRecipeError("Failed to run dependency recype '{}'".format(dependency))
        print "Dependency '{}' installed successfully"

def runRecipe(recipe):
    try:
        print "Checking for '{}' '{}'".format(recipe.name, recipe.version)
        run(recipe.check)
        print "'{}' '{}' is already installed".format(recipe.name, recipe.version)
        return
    except (FailedCommandError) as e:
        print "'{}' '{}' is not installed".format(recipe.name, recipe.version)
    print "Installing '{}' '{}'".format(recipe.name, recipe.version)
    try:
        run(recipe.install)
        print "'{}' '{}' installed successfully".format(recipe.name, recipe.version)
        return
    except (FailedCommandError) as e:
        print "Failed to install '{}' '{}'".format(recipe.name, recipe.version)
        print e
    raise FailedRecipeError("Recipe for '{}' '{}' failed".format(recipe.name, recipe.version))

class CmdConfig(object):

    DEFAULT_PROJECTDIR = os.getcwd()

    def __init__(self, recipeFile, projectdir=DEFAULT_PROJECTDIR):
        self.projectdir = projectdir
        self.recipeFile = recipeFile
        self.prefix = "{}/build".format(projectdir)
        self.srcDir = "{}/src".format(self.prefix)
        self.binDir = "{}/bin".format(self.prefix)
        self.libDir = "{}/lib".format(self.prefix)
        self.incDir = "{}/include".format(self.prefix)
        self.tmpDir = "/tmp/deptool"
        self.cacheDir = "{}/var/lib/cache/deptool".format(self.prefix)
        self.pkgDir = None
        self.cwd = os.getcwd()
        self.exe = os.path.realpath(__file__)

def parseCmdConfig():
    parser = argparse.ArgumentParser(description="Dependency resolving tool")
    parser.add_argument("--projectdir","-p",dest="projectdir",default=CmdConfig.DEFAULT_PROJECTDIR,help="Project Directory")
    parser.add_argument("recipe",help="Recipe file's path")
    args = parser.parse_args()
    return CmdConfig(args.recipe, args.projectdir)

if __name__ == "__main__":
    cmdconfig = parseCmdConfig()
    if re.match("^https?\:\/\/.*",cmdconfig.recipeFile):  recipe = loadRemoteRecipe(cmdconfig.recipeFile, cmdconfig.cacheDir)
    else:  recipe = Recipe.loadFile(cmdconfig.recipeFile)
    if not cmdconfig.pkgDir: cmdconfig.pkgDir = "{}/{}/{}".format(cmdconfig.srcDir, recipe.name, recipe.version)
    setEnv(cmdconfig, recipe)
    ensureDirs(cmdconfig)
    os.chdir(cmdconfig.pkgDir)
    try:
        print "Checking for '{}' '{}'".format(recipe.name, recipe.version)
        run(recipe.check)
        print "'{}' '{}' is already installed".format(recipe.name, recipe.version)
        exit(0)
    except (FailedCommandError) as e:
        print "'{}' '{}' is not installed".format(recipe.name, recipe.version)
    os.chdir(cmdconfig.cwd)
    print "Installing dependencies for '{}' '{}'".format(recipe.name, recipe.version)
    try:
        installDeps(recipe.dependencies, cmdconfig)
    except (FailedRecipeError) as e:
        print e
        print "Recipe for '{}' '{}' failed cause can't satisfy some dependencies".format(recipe.name, recipe.version)
        exit(1)
    os.chdir(cmdconfig.tmpDir)
    for download in recipe.download:
        splittedDownload = download.strip().split(" ",1)
        url = splittedDownload[0]
        if len(splittedDownload) > 1:  destfile =  expandPath(splittedDownload[1].strip())
        else: destfile = getUrlFileName(url)
        if os.path.exists(destfile): print "File '{}' already downloaded into '{}'. Skipping.".format(url, destfile)
        else: print "Downloading '{}' into '{}'".format(url, destfile)
        retrieveUrl(url, destfile)
    os.chdir(cmdconfig.pkgDir)
    print "Installing '{}' '{}'".format(recipe.name, recipe.version)
    try:
        run(recipe.install)
        print "'{}' '{}' installed successfully".format(recipe.name, recipe.version)
        exit(0)
    except (FailedCommandError) as e:
        print "Failed to install '{}' '{}'".format(recipe.name, recipe.version)
        print e
        print "Recipe for '{}' '{}' failed".format(recipe.name, recipe.version)
        exit(1)