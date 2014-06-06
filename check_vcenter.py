#!/usr/bin/env python
# coding: utf-8

"""

    An Nagios plugin made in Python using pyVmomi that
    get informations for virtual machines, esx hosts and datastores

"""

__author__ = "Rogerio Goncalves <rogerlz@gmail.com>"
__version__ = "0.1"

try:
    import warnings
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=DeprecationWarning)
        from pyVim import connect
        from pyVmomi import vmodl
        from pyVmomi import vim
except ImportError as e:
    raise(e)

import atexit
from optparse import OptionParser


def get_obj(content, vmname, obj):
    obj = None
    container = content.viewManager.CreateContainerView(content.rootFolder,
                                                        obj, True)
    for c in container.view:
        if c.name == vmname:
            obj = c
            break
    return obj


def nagios_return(param, wrn, crit, comment):
    if param >= crit:
        print "CRITICAL - " + comment
        return 2
    elif param >= wrn:
        print "WARNING - " + comment
        return 1
    else:
        print "OK - " + comment
        return 0
    print "CRITICAL - Unknown value : %d" % param
    return 2


"""
Process ESX Hosts Informations:
    host.summary.quickStats.overallCpuUsage
    host.summary.hardware.cpuMhz
    host.summary.hardware.numCpuCores
    host.summary.quickStats.overallMemoryUsage
    host.summary.hardware.memorySize
"""


def process_host_info(content):
    host = get_obj(content, opt.name, [vim.HostSystem])
    if opt.action in "CpuUsage":
        CpuUsage = float(host.summary.quickStats.overallCpuUsage)
        CpuTotal = float(((host.summary.hardware.cpuMhz *
                           host.summary.hardware.numCpuCores)))
        PercentUsage = ((CpuUsage/CpuTotal)*100)
        comment = "%s.overallCpuUsage: %.1f Mhz, cpu: %.1f Mhz, %.2f %%" % (opt.name.split(".")[0], CpuUsage, CpuTotal, PercentUsage)
        return nagios_return(PercentUsage, opt.warning, opt.critical, comment)
    elif opt.action in "MemoryUsage":
        MemoryUsage = ((float(host.summary.quickStats.overallMemoryUsage)/1024))
        MemorySize = ((float(host.summary.hardware.memorySize)/1024/1024/1024))
        PercentUsage = ((MemoryUsage/MemorySize)*100)
        comment = "%s.overallMemoryUsage: %.2f GB, memorySize: %.2f GB, %.2f %%" % (opt.name.split(".")[0], MemoryUsage, MemorySize, PercentUsage)
        return nagios_return(PercentUsage, opt.warning, opt.critical, comment)
    else:
        return parser.print_help()


"""
Process Datastore Informations:
    datastore.summary.freeSpace
    datastore.summary.capacity
    datastore.summary.accessible
    datastore.summary.maintenanceMode
"""


def process_datastore_info(content):
    datastore = get_obj(content, opt.name, [vim.HostSystem])
    if opt.action in "FreeSpace":
        freeSpace = ((float(datastore.summary.freeSpace)/1024/1024/1024))
        Capacity = ((float(datstore.summary.capacity)/1024/1024/1024))
        PercentFree = ((freeSpace/Capacity)*100)
        PercentUsage = ((100-PercentFree))
        comment = "%s.FreeSpace: %.1f GB, Capacity: %.1f GB, %.2f %% Used" % (opt.name, freeSpace, Capacity, PercentUsage)
        return commands.nagios_return(PercentUsage, opt.warning,
                                      opt.critical, comment)
    elif opt.action in "HealthStatus":
        accessible = datastore.summary.accessible
        maintenance = datastore.summary.maintenanceMode
        comment = "%s.acessible: %s, %s.maintenanceMode: %s" % (opt.name, accessible, opt.name, maintenance)
        if accessible is True and maintenance in "normal":
            print "OK - " + comment
            return 0
        else:
            print "CRITICAL - " + comment
            return 2
    else:
        return parser.print_help()

"""
Process Virtual Machines Informations:
    vm.summary.quickStats.hostMemoryUsage
    vm.summary.quickStats.guestMemoryUsage
    vm.summary.quickStats.overallCpuUsage
    vm.summary.quickStats.swappedMemory
    vm.summary.config.memorySizeMB
"""


def process_vm_info(content):
    vm = get_obj(content, opt.name, [vim.VirtualMachine])
    if opt.action in "CpuUsage":
        cpuUsage = ((float(vm.summary.quickStats.overallCpuUsage))/100)
        comment = "%s.quickStats.overallCpuUsage: %.2f %%" % (opt.name, cpuUsage)
        return commands.nagios_return(cpuUsage, opt.warning,
                                      opt.critical, comment)
    elif opt.action in "HostMemoryUsage":
        MemoryUsage = ((float(vm.summary.quickStats.hostMemoryUsage)/1024))
    elif opt.action in "GuestMemoryUsage":
        MemoryUsage = ((float(vm.summary.quickStats.guestMemoryUsage)/1024))
        MemorySize = ((float(vm.summary.config.memorySizeMB)/1024))
        PercentUsage = ((MemoryUsage/MemorySize)*100)
        comment = "%s.guestMemoryUsage: %.2f GB, memorySizeMB: %.2f GB, %.2f %%" % (opt.name, MemoryUsage, MemorySize, PercentUsage)
        return nagios_return(PercentUsage, opt.warning, opt.critical, comment)
    elif opt.action in "SwappedMemory":
        MemoryUsage = ((float(vm.summary.quickStats.swappedMemory)/1024))
        MemorySize = ((float(vm.summary.config.memorySizeMB)/1024))
        PercentUsage = ((MemoryUsage/MemorySize)*100)
        comment = "%s.swappedMemory: %.2f GB, memorySizeMB: %.2f GB, %.2f %%" % (opt.name, MemoryUsage, MemorySize, PercentUsage)
        return nagios_return(PercentUsage, opt.warning, opt.critical, comment)
    else:
        return parser.print_help()


def main():
    global opt
    global parser

    help_text = """
    This is a bigger help with actions separated by mode

    if mode = vm
        name = virtual machine name
        actions =
            CpuUsage
            HostMemoryUsage
            GuestMemoryUsage
            SwappedMemory
            Health

    if mode = datastore
        name = datastore name
            actions =
                FreeSpace
                Health

    if mode = host
        name = esx hostname in vcenter
            actions =
                CpuUsage
                MemoryUsage
                Health
    """
    parser = OptionParser(usage=help_text, version="%prog 1.0 beta")
    parser.add_option("-H", action="store", help="vCenter Hostname/IP",
                      dest="hostname")
    parser.add_option("-P", action="store",
                      help="vCenter Port (default: %default)",
                      dest="port", default=443, type=int)
    parser.add_option("-u", action="store", help="vCenter Username",
                      dest="username")
    parser.add_option("-p", action="store", help="vCenter Password",
                      dest="password")
    parser.add_option("-m", action="store", help="vm, host or datastore",
                      dest="mode")
    parser.add_option("-n", action="store", help="see usage text",
                      dest="name")
    parser.add_option("-a", action="store", help="see usage text",
                      dest="action")
    parser.add_option("-W", action="store", help="The Warning threshold (default: %default)",
                      dest="warning", default=80, type=int)
    parser.add_option("-C", action="store", help="The Critical threshold (default: %default)",
                      dest="critical", default=90, type=int)

    (opt, args) = parser.parse_args()

    """
    Required Arguments
    """
    if (opt.hostname is None or opt.username is None or
        opt.password is None or opt.name is None or
        opt.mode is None or opt.action is None):
        return parser.print_help()

    try:
        si = connect.SmartConnect(host=opt.hostname,
                                  user=opt.username,
                                  pwd=opt.password,
                                  port=int(opt.port))

        if not si:
            print("Could not connect to %s using "
                  "specified username and password" % opt.username)
            return -1

        atexit.register(connect.Disconnect, si)

        content = si.RetrieveContent()
        if opt.mode in "host":
            process_host_info(content)
        elif opt.mode in "vm":
            process_vm_info(content)
        elif opt.mode in "datastore":
            process_datastore_info(content)
        else:
            return parser.print_help()

    except vmodl.MethodFault, e:
        print "Caught vmodl fault : " + e.msg
        return -1
    except IOError, e:
        print "Could not connect to %s. Connection Error" % opt.hostname
        return -1
    return 0


if __name__ == "__main__":
    main()
