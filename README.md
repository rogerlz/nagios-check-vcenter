    An Nagios plugin made in Python using pyVmomi that
    get informations for virtual machines, esx hosts and datastores

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
