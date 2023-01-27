import os, datetime

def folder_creation(name=None):
    if name is None:
        mydir = os.path.join(
            os.getcwd(), 
            "outputs",
            datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))
    else:
        mydir = os.path.join(
            os.getcwd(), 
            "outputs",
            name)

    os.makedirs(mydir)
    return mydir
