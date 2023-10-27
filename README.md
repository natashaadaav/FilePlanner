# FilePlanner
Time planning app based on your files.
## Run app
Install requirements:

```
python -m pip install -r requirements.txt
```

Run app:

```
python interface.py
```

## Create a package for Windows

Install PyInstaller:

```
pip install --upgrade pyinstaller
```

**Create** a folder into which the packaged app will be created (for example ..\MyApp). **Move** the file spec\FilePlanner.spec to the created folder.
The spec folder should be **removed** from FilePlanner project folder.

```
cd ..\MyApp
```

In file FileCalendar.spec<br>
replace the line <br>
```Tree('..\FileCalendar')``` <br>
with<br>
```Tree('\path\to\project\FileCalendar')```


```
coll = COLLECT(
    exe, 
    Tree('..\FileCalendar'),  # replace path

    a.binaries,
    a.zipfiles,
    a.datas,
    *[Tree(p) for p in (sdl2.dep_bins + glew.dep_bins)],

    strip=False,
    upx=True,
    upx_exclude=[],
    name='demo',
)
```

Run PyInstaller:
```
python -m PyInstaller FilePlanner.spec
```


