import os
import sys

def setup_env():
    """
    Called on maya startup
    """
    print(' rigging env - executing')
    # Commenting this out until we figure out how we want to handle this.
    #root_path_list = [os.path.join(sys.path[-1],'rig')]
    #os.environ['NXT_FILE_ROOTS'] = ';'.join(root_path_list)
    # Override pose panel mel procs
