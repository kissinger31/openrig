from maya import cmds
import os
d = os.path.abspath(os.path.join(os.path.dirname(__file__), 'mod'))
mod_path = cmds.fileDialog2(fileFilter='*.mod', dialogStyle=2, dir=d, fm=1)
if mod_path:
    mod_path = mod_path[0]

pipeline_root = os.path.abspath(os.path.join(mod_path, '../../../../../'))
mod_file = '''+ sunrise any {module_root}
PYTHONPATH +:= /pipeline
PYTHONPATH +:= /pipeline/nxt/src
'''.format(module_root=pipeline_root)

maya_app_dir = os.environ['MAYA_APP_DIR']
maya_mod_dir = os.path.abspath(os.path.join(maya_app_dir, 'modules'))
mod_file_path = os.path.abspath(os.path.join(maya_mod_dir, 'sunrise.mod'))
old_mod = os.path.abspath(os.path.join(maya_mod_dir, 'openrig.mod'))
go = True
if not os.path.isdir(maya_mod_dir):
    os.mkdir(maya_mod_dir)
if os.path.isfile(mod_file_path):
    try:
        os.remove(mod_file_path)
    except Exception as e:
        go = False
        cmds.error(e)
if os.path.isfile(old_mod):
    try:
        os.remove(old_mod)
    except Exception as e:
        go = False
        cmds.error(e)

if go:
    with open(mod_file_path, 'w') as f:
        f.write(mod_file)
    print(mod_file_path)
    cmds.quit()
else:
    cmds.confirmDialog(title='Install Error!',
                       message=('Please delete these files (if they exist) and '
                                'try the install again!'
                                '\n{}\n{}'.format(mod_file_path, old_mod)))
