Encrypted Python (xpyce)
========================

XPPython3 plugin loads both regular python files (\*.py) and specially encrypted python files (\*.xpyce).

 I am indebted to Soroco Americas Private Limited (https://blog.soroco.com) and https://github.com/soroco/pyce
 for the initial code and idea. I've modified it slightly to support more python versions and work better
 within X-Plane. You can read their code and blog for background.

Normally, python files are distributed as readable text source files. This is a wonderful feature,
allowing users to actually see what the code is going to do, and allows them to make small modifications
to the plugin to better suit their needs.

But, sometimes there is a need for encryption.

* You have a proprietary algorithm, the details of which you don't want to divulge.
* You have complex code you don't want the user to muck-around with as it makes your
  support efforts difficult.
* You need to "lock" the code, making it unusable in some cases.

How xpyce works
---------------

Instead of distributing \*.py files, you can distribute encrypted \*.xpyce files. For each
original \*.py file, you'll create a compiled \.pyc file and then encrypt it, resulting in a
private decryption key + a \*.xpyce file.

Distribute the \*.xpyce file(s) and get the decryption key to the user somehow, and with that information, XPPython3 will
load the module.

Your (non-encrypted) python will update XPPython3 with the decryption keys at runtime, and when XPPython3 attempts to load
a module it will do the normal search for the appropriate \*.py file & failing that, will look for a relevant \*.xpyce
file. If the \*.xpyce file is found, XPPython3 will see if it knowns a decryption key for that file and then attempts to
decrypt and load the compiled byte-code.

If everying is done correctly, there is a very small performance impact on load and zero impact on run time.

Decryption Keys and Loading Complexity
--------------------------------------

Internally, you're updating a loading dictionary which looks similar to::

  {'module.foo.abc': '<key for module.foo.abc>',
   'module.foo.xyz': '<key for module.foo.xyz>',
   ...
   }

The key to the dict is an absolute module name (not a file!). When you encrypt a file you get a decryption key.
When you update the loading dictionary, you need to provide **the module name** as it will be imported.

See :doc:`import`.

Because we automatically add ``Resourcs/plugins`` to ``sys.path``, your file::

  PythonPlugins/myplugin/main.py

can be loaded as::

  PythonPlugins.myplugin.main

Though in your PI\_\*.py file, you'll probably simply load it as::

  from .myplugin import main

Doesn't matter how you actually import the (potentially) encrypted module, the key to the loader dictionary
is the absolute module name or (in this case) ``PythonPlugins.myplugin.main``.

And, if you're loading for an Aircraft plugin, you might still import the encrypted module from PythonPlugins, or
if it is stored local to the Aircraft it might be::

  Laminar Research.Baron B58.plugins.PythonPlugins.myplugin.main

**However**

It's a bit more complicated: Because each version of python needs a different key, you actually
will use the module + ``.cypython-3?.xpyce`` including the python version number.

*Now, for a trick:*

Most commonly, your encrypted module will be located in a subdirectory next to your XPPython3 plugin. This allows you
to import your module using relative imports, i.e., ::

  from .myplugin import main

That means when you register your decryption key you can always register it as::

  {__package__ + 'myplugin.main.cpython-36.xpyce': '<my python 36 decryption key>',
   __package__ + 'myplugin.main.cpython-37.xpyce': '<my python 37 decryption key>',
   __package__ + 'myplugin.main.cpython-38.xpyce': '<my python 38 decryption key>',
   __package__ + 'myplugin.main.cpython-39.xpyce': '<my python 39 decryption key>',
  }

Sounds complicated, but it's not: set it up once and it just works! Review the examples below.


Working Example
---------------

For example, assume I have a Plugin, ``PI_MyPlugin.py``, which will import a local file ``.myplugin.main``.
Your file structure might look like:

::

  <X-Plane>/
  └─── Resources/
       └─── plugins/
            ├─── XPPython3/
            │    ├─── xpyce_compile.py
            │    └─── ....
            └─── PythonPlugins/
                 ├─── PI_MyPlugin.py
                 └─── myplugin/
                      └─── main.py

For whatever reason, you want to protect ``main.py``, so encrypt it:

Step 1. Generate the keys
*************************

* You *must* do this for each version of python.

  * \*.pyc files potentially differ for each version of python.
  * \*.pyc files are the same across platforms, so you only need to generate keys on a single computer (Mac, Windows, or Linux).
  * \*.pyc files are the same between minor releases, so 3.7.1 versus 3.7.3 doesn't matter.

* Use ``xpyce_compile.py`` to both compile and encrypt your \*.py file. It is located in XPPython3 folder
  
* The result is one file for each version of python, and a key

.. code-block:: console

   $ cd Resources/plugins/PythonPlugins
   $ cd myplugin
   $ python3.6 ../../XPPython3/xpyce_compile.py main.py 
   main.cpython-36.xpyce: 9aa5bf3430695af2943af746c3ffdf106a26d618974e0bdf5965b8ebe3f5f08b
   $ python3.7 ../../XPPython3/xpyce_compile.py main.py 
   main.cpython-37.xpyce: 5716da8a938ad287c789e40379e3ae08cf08d29c543004339dd32f22426f948e
   $ python3.8 ../../XPPython3/xpyce_compile.py main.py 
   main.cpython-38.xpyce: 6fadbd1be106c9868c5fe1381f0d7f8d742f5fa22495f10b6107005166248516
   $ python3.9 ../../XPPython3/xpyce_compile.py main.py 
   main.cpython-39.xpyce: 6fa0a80137281869ccbafa58c01354c74d3004de114309ade691d239e122cd68

::

  <X-Plane>/
  └─── Resources/
       └─── plugins/
            ├─── XPPython3/
            │    ├─── xpyce_compile.py
            │    └─── ....
            └─── PythonPlugins/
                 ├─── PI_MyPlugin.py
                 └─── myplugin/
                      ├─── main.py
                      ├─── main.cpython-36.xpyce
                      ├─── main.cpython-37.xpyce
                      ├─── main.cpython-38.xpyce
                      └─── main.cpython-39.xpyce

Step 2. Add Keys to your PI\_\*.py file
***************************************

XPPython3 can't read the \*.xpyce file without a key, so you'll need to provide that in
a PI\_\*.py file. It can be simple as::

   from XPPython3.xpyce import update_keys

   keys = {
        __package__ + '.myplugin.main.cpython-36.xpyce': '9aa5bf3430695af2943af746c3ffdf106a26d618974e0bdf5965b8ebe3f5f08b',
        __package__ + '.myplugin.main.cpython-37.xpyce': '5716da8a938ad287c789e40379e3ae08cf08d29c543004339dd32f22426f948e',
        __package__ + '.myplugin.main.cpython-38.xpyce': '6fadbd1be106c9868c5fe1381f0d7f8d742f5fa22495f10b6107005166248516',
        __package__ + '.myplugin.main.cpython-39.xpyce': '6fa0a80137281869ccbafa58c01354c74d3004de114309ade691d239e122cd68'
   }
   update_keys(keys)

   class PythonInteface:
      ...

In the above example, we provide the keys in readable python. With the keys, the user could decrypt the
\*.xpyce file but, that merely gets them a compiled \*.pyc file. This is a great way to protect your secrets
without and digital rights management.

.. note:: There are tools which will allow an enterprising individual to read and manipulate python byte-code, but
          the same can be said for manipulating compiled binary shared objects. **Nothing** is absolutely secure.
          
An alternative to directly adding keys to your PI\_\*.py file, you might require a user to login to your server and download
keys, or read them from a configuration file. In any case, you have to call ``update_keys`` *prior* to importing
the encrypted module(s).

Example: Convert an Existing Plugin
-----------------------------------

Assume you have an existing (python3) plugin: ``PI_MySecret.py``, and you want to convert it.

1. Create subdirectory and place your original code there:

  .. code-block:: console

     $ pwd
     <XP>/Resources/plugins/PythonPlugins
     $ mkdir mysecret
     $ mv PI_MySecret.py mysecret

2. Create a new "shell" plugin PI_MySecret.py under PythonPlugins, which looks similar to::

    from .mysecret import PI_MySecret

    class PythonInterface(PI_MySecret.PythonInterface):
        pass

3. Test and convince yourself this new plugin is identical to your old plugin. (We've not done any encryption yet).

4. Generate keys
   Remember to generate keys for ``mysecret/PI_MySecret.py``, not for your new shell ``PI_MySecret.py``

  .. code-block:: console

   $ cd mysecret
   $ python3.6 ../../XPPython3/xpyce_compile.py PI_MySecret.py 
   PI_MySecret.cpython-36.xpyce: 9aa5bf3430695af2943af746c3ffdf106a26d618974e0bdf5965b8ebe3f5f08b
   $ python3.7 ../../XPPython3/xpyce_compile.py PI_MySecret.py 
   PI_MySecret.cpython-37.xpyce: 5716da8a938ad287c789e40379e3ae08cf08d29c543004339dd32f22426f948e
   $ python3.8 ../../XPPython3/xpyce_compile.py PI_MySecret.py 
   PI_MySecret.cpython-38.xpyce: 6fadbd1be106c9868c5fe1381f0d7f8d742f5fa22495f10b6107005166248516
   $ python3.9 ../../XPPython3/xpyce_compile.py PI_MySecret.py 
   PI_MySecret.cpython-39.xpyce: 6fa0a80137281869ccbafa58c01354c74d3004de114309ade691d239e122cd68
 
5. Add the keys to your shell PI_MySecret.py file::

     from XPPython3.xpyce import update_keys
     
     keys = {
         __package__ + '.mysecret.PI_MySecret.cpython-36.xpyce': '9aa5bf3430695af2943af746c3ffdf106a26d618974e0bdf5965b8ebe3f5f08b',
         __package__ + '.mysecret.PI_MySecret.cpython-37.xpyce': '5716da8a938ad287c789e40379e3ae08cf08d29c543004339dd32f22426f948e',
         __package__ + '.mysecret.PI_MySecret.cpython-38.xpyce': '6fadbd1be106c9868c5fe1381f0d7f8d742f5fa22495f10b6107005166248516',
         __package__ + '.mysecret.PI_MySecret.cpython-39.xpyce': '6fa0a80137281869ccbafa58c01354c74d3004de114309ade691d239e122cd68'
     }
     update_keys(keys)
     
     from .mysecret import PI_MySecret
     
     
     class PythonInterface(PI_MySecret.PythonInterface):
         pass

6. Test again.

   Note that *we still load the* ``mysecret/PI_MySecret.py`` file. This will always be true: if the \*.py file
   exists, we use it. If the \*.py file does not exist, we look for the \*.xpyce.

7. Move / Remove the \*.py and test again.

   .. code-block:: console

     $ mv mysecret/PI_MySecret.py mysecret/PI_MySecret.py-disabled

8. Done. Ship the code as::

                 ├─── PI_MyScecret.py
                 └─── myscecret/
                      ├─── PI_MySecret.cpython-36.xpyce
                      ├─── PI_MySecret.cpython-37.xpyce
                      ├─── PI_MySecret.cpython-38.xpyce
                      └─── PI_MySecret.cpython-39.xpyce

Alternatives
------------

The above examples provide keys directly in the python source -- remember XPPython3 still needs a PI\_\*.py file
to with a defined PythonInterface class in order to start the plugin.

If you don't want to store the code in the python file, you could add code to your ``PythonInterface().XPluginStart()``
function: It could read a local file with username / password information, and exchange that information with your server
to retrieve the decryption keys (Note: the decryption keys will be the same for all users!). On success, you update
the loader dictionary using ``XPPython3.xpyce.update_keys()``.

Then, your XPluginStart or XPluginEnable can import the encrypted module, something like::

  class PythonInterface:
     def XPPluginStart(self):
         try:
             user_credentials = readCredentialsFromFile()
             keys = getKeysFromServer(user_credenials)
             XPPython3.xpyce.update_keys(keys)
             mod = importlib.import_module('.myplugin.main')
         except:
             mod = None
         return 'Name', 'Signature', 'Description'

     def XPluginEnable(self):
         if not mod:
            promptUserForCredentials():
         else:
            mod.doStuff()

Fortunately, you can test all this *without encryption* by simply not deleting your \*.py module (``myplugin/main.py`` in this
example). Once you have the credentials part working, delete the python file and the ``importlib.import_module()`` code
will look for the encrypted version.
