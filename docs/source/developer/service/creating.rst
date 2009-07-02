
Creating a new service
======================

As will be seen, there is a large amount of boiler plate involved in creating
a service, and so we have provided the creator.py script in the tools/
directory of the source distribution. You should run this with the single
argument _service_ and you will be asked a few questions to complete the
process:

.Using tools/creator.py::

    ali@book:~/working/pida$ python tools/creator.py service
    Please enter the path for the service [/home/ali/working/pida/pida/services]: /tmp
    Please enter the Service name: MyService
    Creating service my service in /tmp
