# PRIORITY
**PRIORITY** is the acronim of Platform for the tRansition to sustanInable zerO-caRbon mobilITY. 
This work presents the design and the implementation of a digital platform for **rban mobility**  addressed to decision makers. The platform allows aggregating mobilit mobility data  within   **traffic zones**  for analysis of travel demand, polluting emissions, energy consumption and externalities  **in the metropolitan city of Rome (Italy)**
Detailed architecture and functionalities are explained together with the final outputs to summarize the status of mobility over a study area based on its urbanization and traffic indicators.

The platform has been designed to retrieve mobility insights from Floating Car Data, General **(FCD)** Transit Feed Specification data  **(GTFS)** and public transport data. 
PRIOIRTY has been Built with the  **Python Flask** framework to allow the users to easily explore data through a dashboard together with interactive maps. This platform integrates real-world mobility data with modelled data to enhance the reconstruction of individual travel. In addition, it offers the option to perform  **online statistics** over traffic zones upon a mouse click with the possibility to visualize  **hourly profiles** of several traffic variables as well as polluting emissions, energy consumption and externalities. 

The platform allows exploitation of mobility data to perform  **spatial and temporal aggregations**, to compute  <strong> desire lines  </strong> between origins and destinations and, to highlight traffic zones crossed by trips originating from a specific zone. Additionally, the PRIORITY platform offers the possibility to  **retrieve Points of Interests (POI)** from the OpenStreetMap database and to load an updated charging network for electric vehicles through the direct connection with Open Charge Map.


# Installation
The platform PRIORITY has been developed considering both Windows and Linux operating systems. 
To make the platform working on your own system follow these steps

1. Consider installing a recent Python verison. I suggest the verison **Pythyon 3.10** or later versions
2. In the terminal window install the requred packages as lieted in the **requirements.txt**. Be aware, you might be required to install additional packages or dependencies upon installation on Windows or Linux environment.
3. Create your own working directory where you are going to copy the file **main.py** and directories **templates** and **static**
4. Once you have download the files in this repositoriy and installed the necessary libraries, while in the terminal window, go to your working directory and execute **python main.py**
5. To deploy the this application on a web-server (Linux machine using Apache+WSGI), follow the indication suggested in this link: https://tecadmin.net/deploying-flask-application-on-ubuntu-apache-wsgi/
6. Most of parameters and datasets stored in the format of .csv files, .geojson files, .txt files have been linekd to a session user id (i.e. **data_sessionID.geojson**). The sessionID is an unique alphanumeric code generated automatically 

## Database
A database should be setup using **PostgreSQL** to store input data to be processed in the Platform. The main structure of the tables is explained into details in the publication linked to this project.
Connection to a PostgreSQL database has been done in the following way:
```
from sqlalchemy import create_engine
from sqlalchemy import exc
import sqlalchemy as sal
from sqlalchemy.pool import NullPool
from sqlalchemy.sql import text

engine = create_engine("postgresql://username:password@123.456.555.567:5432/DB_NAME")
query = text('''SELECT.....FROM..... WHERE...''')
```
if the query contains **parameters**, you must consider using the following line:
```
stmt = query.bindparams(x=str(param_1), y=str(param_2), z=str(param_3))

with engine.connect() as conn:
  res = conn.execute(stmt).all()
df = pd.DataFrame(res)
```

## Possible Setup Issues

When clicking on a selected geographical zone on the map, the **index** of that zone is saved in a .txt file and read by the Python Flask code.
The index file is read differently when considering working in a Windows or Linux environment. 

Therefore, when working within **Windows environment** proceed as follow:

```
    ## read back zmu index
    with open(path_app + "static/params/index_zmu_" + session.sid + ".txt") as f:
        lines = f.readlines()
    ## string split and get value
    selected_index_zmu = ((lines[1]).split())[1]
```
Instead, if you are going to work within a **Linux environment**, proceed as follow:
```
    ## read back zmu index
    with open(path_app + "static/params/index_zmu_" + session.sid + ".txt") as f:
        lines = f.readlines()
   
    line = ((lines[0]).split(':'))[1]
    import re
    ## string split and get value
    line = re.sub('}\n', '', line)
    selected_index_zmu = line  
```
<br>
<br>

![image](https://github.com/user-attachments/assets/7716d40d-8efa-41cd-a42e-a71f3c99d08b)

*Home page of the platform PRIORITY*

<br>

![image](https://github.com/user-attachments/assets/d6ab6899-bc60-4e68-9966-8d24cd7c2542)

*The module Private Mobility within the platform PRIORITY*

## Problems or questions?
for any question contact federico.karagulian@enea.it or karafede@hotmail.com
... and much other work is going on....

## Citation
If you used Genesis in your research, we would appreciate it if you could cite it. We are still working on a technical report, and before it's public, you could consider citing:
```
@software{PRIORITY,
  author = {PRIORITY Authors},
  title = {PRIORITY: PRIORITY, a web-server Mobility Platform: design and implementation},
  month = {January},
  year = {2024},
  url = {https://github.com/karafede/PRIORITY}
}
```
