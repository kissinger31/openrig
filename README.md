# Overview 
OpenRig is collection python libraries and NXT graphs that allow you to author and deliver rigs. Openrig has archetype examples to show how one might use [NXT ](https://nxt-dev.github.io/) to create templates and inherit layers to generate rigged assets. It also contains tons of useful libraries to help with exporting, importing, mutating all kinds of data. Most of the libaraies are written to work with Autodesk Maya.

# Links
- [Dependencies](#dependencies)
- [Building](#building-a-biped-rig)
- [NXT File Roots](#nxt-file-roots)
- [Contributing](CONTRIBUTING.md)
- [Licensing](LICENSE)

# Dependencies 
* Numpy for Maya (or any Python 2.7)
`pip install -i https://pypi.anaconda.org/carlkl/simple numpy`
* NXT Maya plugin - [NXT Release](https://github.com/nxt-dev/nxt_editor/releases/latest)
* Maya 2018 and on

# Building a biped rig
1. Add the openrig package to your python sys.path so it is available to Maya. (See env example below)
2. Get the NXT maya plugin from the NXT github release page. 
    - [NXT Core](https://github.com/nxt-dev/nxt/releases/latest)
    - [NXT Editor](https://github.com/nxt-dev/nxt_editor/releases/latest)
3. Open the `biped_base_rig.nxt` graph in NXT in Maya
`openrig/openrig/archetypes/biped/rig/data/base/biped_base_rig.nxt`
4. Run a build by clicking the play/build button in nxt.

# NXT file roots
For building assets layering biped from another location, please use the **_NXT_FILE_ROOTS_** environment variable.

The environement variable **_NXT_FILE_ROOTS_** will allow *_NXT_* to fall through when doing resolution for referenced files and attribute file/path resolution. This way you don't have to have hard coded paths to files in your graphs. Please read the [NXT Reference](https://nxt-dev.github.io/reference/#tokens) for more information about this.

# Python env setup example
```python
import os, sys

# repo path is the directory your repo is located. you cloned you're repo. 
repo_path = 'C:/Users/{user}/Desktop/sunrise'
openrig_path = '{}/openrig'.format(repo_path)
nxt_roots = '{anotherPathToAssets}/character;{}/openrig/archetypes'.format(openrig_path)

sys.path.append(openrig_path)
sys.path.append(repo_path)

os.environ['NXT_FILE_ROOTS'] = nxt_roots
```

