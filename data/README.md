# How to add your own model:

You can use your own model to perform a containability and pouring simulation. There are a few steps you need to follow to make sure your model works with the simulation.

* Scale your object model down so that the length is on the order of 0.1 - 0.3mm. Save it as an .obj file.

* Create a folder for your object inside `container-visualize/data/`, and name it `object_name_0`.

* Inside the folder, put the object file and its V-HACD decomposition. If your model is not overly complicated, it is possible to use a copy of the object in place of V-HACD. Name them `object_name_0.obj` and `object_name_0_vhacd.obj` respectively.

* Copy the [URDF template](template.urdf) into your object folder, name the file `object_name_0.urdf`. Open the file using a text editor and change the default object names.

Your object directory now should look like this:
```bash
├── data
│   ├── object_name_0
│   │   ├── object_name_0.obj
│   │   ├── object_name_0_vhacd.obj
│   │   ├── object_name_0.urdf
...
```

Now you can carry out the simulations with the instructions [here](../README.md)