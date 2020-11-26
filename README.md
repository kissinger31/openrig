# openrig 
## General rig python libraries and NXT rig build graphs

# Building a biped rig
1. Add the openrig package to your python sys.path so it is available to Maya. (See env example below)
2. Get the NXT maya plugin from the NXT github release page.
3. Open the biped_base_rig.nxt graph in NXT in Maya
openrig/openrig/archetypes/biped/rig/data/base/biped_base_rig.nxt
4. Run a build by clicking the play/build button in nxt.
git pu
# NXT file roots
For building assets layering biped from another location, please use the NXT_FILE_ROOTS environment variable.

# Python env setup example
```python
import os, sys

repo_path = 'C:/Users/{user}/Desktop/sunrise'
openrig_path = '{}/openrig'.format(repo_path)
nxt_roots = '{anotherPathToAssets}/character;{}/openrig/openrig/archetypes'.format(repo_path)

sys.path.append(openrig_path)
sys.path.append(repo_path)

os.environ['NXT_FILE_ROOTS'] = nxt_roots
```

