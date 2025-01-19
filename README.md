# PRIORITY
**PRIORITY** is the acronim of Platform for the tRansition to sustanInable zerO-caRbon mobilITY. 
This work presents the design and the implementation of a digital platform for **rban mobility**  addressed to decision makers. The platform allows aggregating mobilit mobility data  within   **traffic zones**  for analysis of travel demand, polluting emissions, energy consumption and externalities  **in the metropolitan city of Rome (Italy)**
Detailed architecture and functionalities are explained together with the final outputs to summarize the status of mobility over a study area based on its urbanization and traffic indicators.

The platform has been designed to retrieve mobility insights from Floating Car Data, General **(FCD)** Transit Feed Specification data  **(GTFS)** and public transport data. 
PRIOIRTY has been Built with the  **Python Flask** framework to allow the users to easily explore data through a dashboard together with interactive maps. This platform integrates real-world mobility data with modelled data to enhance the reconstruction of individual travel. In addition, it offers the option to perform  **online statistics** over traffic zones upon a mouse click with the possibility to visualize  **hourly profiles** of several traffic variables as well as polluting emissions, energy consumption and externalities. 

The platform allows exploitation of mobility data to perform  **spatial and temporal aggregations**, to compute  <strong> desire lines  </strong> between origins and destinations and, to highlight traffic zones crossed by trips originating from a specific zone. Additionally, the PRIORITY platform offers the possibility to  **retrieve Points of Interests (POI)** from the OpenStreetMap database and to load an updated charging network for electric vehicles through the direct connection with Open Charge Map.

for any question contact federico.karagulian@enea.it or karafede@hotmail.com

# Installation
The platform PRIORITY has been developed considering both Windows and Linux operating systems. 
To make the platform working on your own system follow these steps

1. Consider installing a recent Python verison. I suggest the verison **Pythyon 3.10** or later versions
2. In the terminal window install the requred packages as lieted in the **requirements.txt**. Be aware, you might be required to install additional packages or dependencies upon installation on Windows or Linux environment.
3. Create your own working directory where you are going to copy the file **main.py** and directories **templates** and **static**
4. Once you have download the files in this repositoriy and installed the necessary libraries, while in the terminal window, go to your working directory and execute **python main.py***

## Database
A database should be setup using **Postgresql** to store input data to be processed in the Platform. The structure of the table is explained into details in the publication linked to this project.


![image](https://github.com/user-attachments/assets/7716d40d-8efa-41cd-a42e-a71f3c99d08b)

<br>

![image](https://github.com/user-attachments/assets/26cc8762-bb6e-42e1-bec0-c174c547aa04)


