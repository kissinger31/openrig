import maya.cmds as mc

def remove_all_namespaces():
    '''
    Forcibly removes all namesspaces from the current scene recursively
    :return:
    '''
    namespaces_exist = True
    protected = [u'UI', u'shared']
    while namespaces_exist:
        all = mc.namespaceInfo(listOnlyNamespaces=True)
        ns_to_remove = list(set(all) - set(protected))
        if not ns_to_remove:
            namespaces_exist = False

        for ns in ns_to_remove:
            mc.namespace(moveNamespace=(ns, ':'), force=True)
            mc.namespace(removeNamespace=ns, force=True)