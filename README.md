# PRIORITY
**PRIORITY** is the acronim of Platform for the tRansition to sustanInable zerO-caRbon mobilITY. 
This work presents the design and the implementation of a digital platform for **rban mobility**  addressed to decision makers. The platform allows aggregating mobilit mobility data  within   **traffic zones**  for analysis of travel demand, polluting emissions, energy consumption and externalities  **in the metropolitan city of Rome (Italy)**
Detailed architecture and functionalities are explained together with the final outputs to summarize the status of mobility over a study area based on its urbanization and traffic indicators.

The platform has been designed to retrieve mobility insights from Floating Car Data, General **(FCD)** Transit Feed Specification data  **(GTFS)** and public transport data. 
PRIOIRTY has been Built with the  **Python Flask** framework to allow the users to easily explore data through a dashboard together with interactive maps. This platform integrates real-world mobility data with modelled data to enhance the reconstruction of individual travel. In addition, it offers the option to perform  **online statistics** over traffic zones upon a mouse click with the possibility to visualize  **hourly profiles** of several traffic variables as well as polluting emissions, energy consumption and externalities. 

The platform allows exploitation of mobility data to perform  **spatial and temporal aggregations**, to compute  <strong> desire lines  </strong> between origins and destinations and, to highlight traffic zones crossed by trips originating from a specific zone. Additionally, the PRIORITY platform offers the possibility to  **retrieve Points of Interests (POI)** from the OpenStreetMap database.

# Installation
The platform PRIORITY has been developed considering both Windows and Linux operating systems. 
To make the platform working on your own system follow these steps

1. Consider installing a recent Python verison. I suggest the verison **Pythyon 3.10** or later versions
2. In the terminal window install the requred packages as lieted in the **requirements.txt**. Be aware, you might be required to install additional packages or dependencies upon installation on Windows or Linux environment.
3. Create your own working directory where you are going to copy the file **main.py** and directories **templates** and **static**
4. Once you have download the files in this repositoriy and installed the necessary libraries, while in the terminal window, go to your working directory and execute  **> python main.py**
5. To deploy the this application on a web-server (Linux machine using Apache+WSGI), follow the indication suggested in this link: https://tecadmin.net/deploying-flask-application-on-ubuntu-apache-wsgi/


## Database
A database should be setup using **PostgreSQL** to store input data to be processed in the Platform. The main structure of the tables is explained into details in the publication linked to this project.
Connection to a PostgreSQL database has been done in the following way:
```
from sqlalchemy import create_engine
from sqlalchemy import exc
import sqlalchemy as sal
from sqlalchemy.pool import NullPool
from sqlalchemy.sql import text

engine = create_engine("postgresql://username:password@123.456.555.567:5432/database_name")
query = text('''SELECT.....FROM..... WHERE...''')
```
if the query contains **parameters**, you must consider using the following line:
```
stmt = query.bindparams(x=str(param_1), y=str(param_2), z=str(param_3))

with engine.connect() as conn:
  res = conn.execute(stmt).all()
df = pd.DataFrame(res)
```

## Initialization
Most of parameters and datasets stored in the format of .csv files, .geojson files, .txt files have been linekd to a session user id (i.e. **data_0b4c7f3d-c6ae-46ca-8705-ac159ebc8aa7,geojson** ). The sessionID is an unique alphanumeric code generated automatically each time an user access to the link of the Platform. In this way, multiple users can operate on the same webpage and visualize their own results. 

At the first installation, the datasets supporting the visualization are generated upon execution of tyhe engine behind the page after setting the initial paramenters. For instance, in the Provate Module, upon setting of the *range of days, trip indicator, type of data*, and *type of staypoints*, the execution of the page only starts after selecting the **Hour range**. Default parameters and datasets (in the format of .csv, .txt and .geojson file) are loaded from the **/static** folder that you can download from this repository. If you have any problem finding or generating a dataset, or something missing, please feel free to contact me. 
The datasets and parameters present in the **/static** folder are mainly as default data to be used when the user opens a selected page. For most of the module the datasets generated upon exection of a page are stored in session and sent from Python Flask to the html/javascript. This data are not saved into the **/static** folder but into the **cache** that is located in the **/flask_session** folder. This cache should be empty quite frequently depending on the workload of the platform. 

In the **Python FLask** code, the commnad line that transforms a given dataset into a session variable is:
```
session["result_variable"] = dataset_result.to_json()
```

In the **html-css-javascript** code, the commnad line creating a variable of data from the session variable is:
```
var data = JSON.parse(JSON.stringify({{session["result_variable"] | tojson | safe}}));
   data = "[" + data + "]";
   var data = eval(data);
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

![image](https://github.com/user-attachments/assets/cd9dc925-9910-4b3c-b9ad-e05e253f4e88)


*Home page of the platform PRIORITY*

<br>

![image](https://github.com/user-attachments/assets/d6ab6899-bc60-4e68-9966-8d24cd7c2542)

*The module Private Mobility within the platform PRIORITY*

## Caveats
The PRIORTY platform has been realized with the puprose to follow the best practice for delivering an acceptable web-interface. While the back-end has been completly created using **Python** with the implementation of several algorithms to process mobility data upon user request, the front-end has been implemented using **css, javascript, html** and namy **java libraries**. 

However there are few things that should be considered for future improvement:
1. The front-end (web-interface) should be optimized to have a dashboard better adjustable to different screen sizes.
2. Html file used in each module very often contains the same pieces of css and javascripts codes but with sligth differences. This choice was taken to customize each web-page. However, once the functionalites are well defined, it is possible to directly load css and javascripts files into the html files.
3. In the select option it is only possible selecting the same parameter once

## Problems or questions?
for any question contact federico.karagulian@enea.it or karafede@hotmail.com

... work is in progress to populate this GitHub page........

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
