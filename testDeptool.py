#!/usr/bin/env python

import os
from nose.tools import raises, assert_raises
from mock import Mock, patch, call
from deptool import CmdConfig, Recipe, sanitizeStrList, run, installDeps, runRecipe, FailedCommandError, FailedRecipeError, getUrlFileName, parseDownload

@raises(ValueError)
def testRecipeInvalidDict():
    recipe = Recipe("something")
    
@raises(ValueError)
def testRecipeNoName():
    recipe = Recipe({})

@raises(ValueError)
def testRecipeEmptyName():
    recipe = Recipe({"name":""})

def testRecipeDefaultVersion0():
    recipe = Recipe({"name":"test"})
    assert(recipe.version == "0")

def testRecipeValid():
    recipe = Recipe({"name":"test", "version":"3.7"})
    assert(recipe.name == "test")
    assert(recipe.version == "3.7")

def testRecipeDefaultDependencies():
    recipe = Recipe({"name":"test"})
    assert(recipe.dependencies == [])

def testRecipeValidListDependencies():
    recipe = Recipe({"name":"test", "dependencies": ["dep1","dep2"]})
    assert(recipe.dependencies == ["dep1","dep2"])

def testRecipeValidStrDependencies():
    recipe = Recipe({"name":"test", "dependencies": "blah"})
    assert(recipe.dependencies == ["blah"] )

def testRecipeDefaultInstall():
    recipe = Recipe({"name":"test"})
    assert(recipe.install == [])

def testRecipeValidListInstall():
    recipe = Recipe({"name":"test", "install": ["command1","command2"]})
    assert(recipe.install == ["command1","command2"])

def testRecipeValidStrInstall():
    recipe = Recipe({"name":"test", "install":"command"})
    assert(recipe.install[0] == "command")

def testRecipeDefaultCheck():
    recipe = Recipe({"name":"test"})
    assert(recipe.check == [])

def testRecipeValidListCheck():
    recipe = Recipe({"name":"test", "check": ["command1","command2"]})
    assert(recipe.check == ["command1","command2"])

def testRecipeValidStrCheck():
    recipe = Recipe({"name":"test", "check":"command"})
    assert(recipe.check[0] == "command")

def testRecipeDefaultDownload():
    recipe = Recipe({"name":"test"})
    assert(recipe.download == [])

def testRecipeDownloadStr():
    recipe = Recipe({"name":"test", "download":"http://domain.tld/file.tgz"})
    assert(recipe.download == ["http://domain.tld/file.tgz"])

def testRecipeDownloadList():
    recipe = Recipe({"name":"test", "download":["http://domain.tld/file.tgz","http://domain.tld/anotherfile"]})
    assert(recipe.download == ["http://domain.tld/file.tgz","http://domain.tld/anotherfile"])

def testRecipeDownloadSingle():
    recipe = Recipe({"name":"test", "download":["http://domain.tld/file.tgz"]})
    assert(recipe.download == ["http://domain.tld/file.tgz"])

def testSanitizeStrList():
    assert( [] == sanitizeStrList([]) )
    assert( ["command1"] == sanitizeStrList(["command1"]) )
    assert( ["command1","command2"] == sanitizeStrList(["command1","command2"]) )
    assert( ["command1"] == sanitizeStrList("command1") )

def testRecipeLoadFile():
    recipe = Recipe.loadFile("zlib-1.2.11.yaml")
    assert( recipe.name == "zlib" )
    assert( recipe.version == "1.2.11" )
    assert( recipe.check == ["test -r ${LIBDIR}/libz.so","test -r ${INCDIR}/zlib.h"] )
    assert( len(recipe.install) == 5 )
    assert( recipe.dependencies == [] )

def testRunSingleCommandSuccess():
    run(":")

@raises(FailedCommandError)
def testRunSingleCommandFails():
    run("exit 1")

def testRunMultipleCommandSuccess():
    run([":",":",":"])

@raises(FailedCommandError)
def testRunMultipleCommandsFail():
    run([":","exit 1","exit 0"])

def testRunRecipeCheckTrue():
    recipe = Recipe({"name": "libtest", "version": "1.3", "check": ["test -f /usr/local/lib/libtest.so","test -f /usr/local/include/test.h"], "install":["wget http://test/test.tgz", "tar xzf test.tgz", "cd test && make install"] })
    expected = [ call("test -f /usr/local/lib/libtest.so",shell=True) , call("test -f /usr/local/include/test.h",shell=True) ]
    with patch("subprocess.call", return_value = 0) as mock:
        runRecipe(recipe)
        assert( mock.mock_calls == expected )

def testRunRecipeCheckFalse():
    recipe = Recipe({"name": "libtest", "version": "1.3", "check": ["test -f /usr/local/lib/libtest.so","test -f /usr/local/include/test.h"], "install":["wget http://test/test.tgz", "tar xzf test.tgz", "cd test && make install"] })
    expected = [ call("test -f /usr/local/lib/libtest.so",shell=True), call("wget http://test/test.tgz",shell=True), call("tar xzf test.tgz",shell=True), call("cd test && make install",shell=True) ]
    with patch("subprocess.call", side_effect = [1,0,0,0] ) as mock:
        runRecipe(recipe)
        assert( mock.mock_calls == expected )

def testRunRecipeFailedInstall():
    recipe = Recipe({"name": "libtest", "version": "1.3", "check": ["test -f /usr/local/lib/libtest.so","test -f /usr/local/include/test.h"], "install":["wget http://test/test.tgz", "tar xzf test.tgz", "cd test && make install"] })
    expected = [ call("test -f /usr/local/lib/libtest.so",shell=True), call("wget http://test/test.tgz",shell=True) ]
    with patch("subprocess.call", side_effect = [1,1] ) as mock:
        assert_raises( FailedRecipeError, runRecipe, recipe)
        assert( mock.mock_calls == expected )

def testInstallDeps():
    dependencies = ["dependency1.yaml","dependency2.yaml"]
    config = CmdConfig("myrecipe.yaml", "/myproject/build")
    expected = [ call([config.exe,"--prefix",config.prefix,"dependency1.yaml"]), call([config.exe,"--prefix",config.prefix,"dependency2.yaml"]) ]
    with patch("subprocess.call", return_value = 0) as mock:
        installDeps(dependencies, config)
        assert( mock.mock_calls == expected )

def testInstallDepsFail():
    dependencies = ["dependency1.yaml","dependency2.yaml","dependency2.yaml"]
    config = CmdConfig("myrecipe.yaml", "/myproject/build")
    expected = [ call([config.exe,"--prefix",config.prefix,"dependency1.yaml"]), call([config.exe,"--prefix",config.prefix,"dependency2.yaml"]) ]
    with patch("subprocess.call", side_effect = [0,1]) as mock:
        assert_raises( FailedRecipeError, installDeps, dependencies, config)
        assert( mock.mock_calls == expected )

def testGetUrlFileName():
    assert ( "myfile.tgz" == getUrlFileName("http://something/dir/subdir/myfile.tgz") )
    assert ( "myfile.tgz" == getUrlFileName("something/dir/subdir/myfile.tgz") )
    assert ( "subdir" == getUrlFileName("http://something/subdir") )
    assert ( "noname" == getUrlFileName("http://something/subdir/") )
    assert ( "noname" == getUrlFileName("http://something/") )
    assert ( "noname" == getUrlFileName("http://something") )
    assert ( "noname" == getUrlFileName("") )

def testParseDownload():
    os.environ["MYDIR"] = "/tmp/mydir"
    assert ( parseDownload("https://example.tld/d/file.tgz") == ("https://example.tld/d/file.tgz","file.tgz") )
    assert ( parseDownload("https://example.tld/d/") == ("https://example.tld/d/","noname") )
    assert ( parseDownload("https://example.tld/d/file.tgz myfile.tgz") == ("https://example.tld/d/file.tgz","myfile.tgz") )
    assert ( parseDownload("https://example.tld/d/file.tgz ${MYDIR}/myfile.tgz") == ("https://example.tld/d/file.tgz","/tmp/mydir/myfile.tgz") )
    assert ( parseDownload("https://example.tld/d/file.tgz mydir/") == ("https://example.tld/d/file.tgz","mydir/file.tgz") )
