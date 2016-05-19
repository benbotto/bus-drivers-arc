# bus-drivers-arc
The Crash Analysis Toolbox is a collection of python based ArcMap scripts, and tools for use in [ArcGIS for Desktop](http://www.esri.com/software/arcgis/arcgis-for-desktop) versions 10.2.x and above. These tools offer a more streamlined approach to analyzing traffic crash data, compared to ArcGIS’ model builder.  The tools are also modular, meaning that python tools can be removed or added to each project without much effort. 

The primary user of the Hotspot Analysis Tool Suite is Dr. Ghazan Khan, an assistant professor of civil engineering, specializing in transportation engineering, at California State University, Sacramento.  Dr. Khan has expert-level knowledge of the ArcGIS platform, and he is a subject matter expert in the crash analysis field. Dr. Khan lectures about ArcGIS and road safety, and his civil engineering students may utilize the developed tools in their research (particularly graduate students).  All users of the Hotspot Analysis Tool Suite are expected to be proficient in ArcGIS.

The Crash Analysis toolbox has 4 major tools: Crash Radius Density, Crash Network Density, Network K Analysis, and Cross K Function. Each one of these tools acts takes an existing crash data (see "scratch/collision data/Collisions.csv" for test data) and takes in various inputs (defined by each tool) and outputs analysis by each type of tool. 

Each of the tools are located within their own python script (as well as helper python scripts) in the "toolbox" folder.
Also, Each of the tools support have documentation built into the xml metadata which show in the ArcMap User Interface "Item Descriptions".  To see them, go to the ArcCatalog, then right click on a python tool and select “Item Description”. A new window will open, describing the tool. These "self-documenting" item descriptions are maintained in the corresponding tools .xml file in the "toolbox" folder. These files can be edited in two ways, through the xml file or through the ArcCatalog UI (See Section 4 - Tools in the "As Built Design - Crash Analysis Toolbox"). 

## Features
* The Crash Analysis toolbox has 7 major tools in the "toolbox" folder (refer to the User Manual or consult with Dr. Khan for details on each tool as they have background information of each tool as well as expected output):
  * **Crash Radius Density**
  * **Crash Network Density**
  * **Create Random Points on a Network Dataset**
  * **Global K Functoin**
  * **Cross K Function**
  * **Netowrk Dataset Length**
  * **Random ODCM Permutations**

## Required Environment
* ArcGIS Desktop 10.2+ 
* Python 2.7
* Some tools require additional packages   
    * The ArcGIS Editor for OSM (OpenStreetMap) - ArcGIS extension required for the Crash Network Density and Network K Analysis Tools, specifically to be able use open-source network data of streets within the toolbox. For installation, follow the link below (urls subject to change):  <br />
      * 10.2.x - http://www.arcgis.com/home/item.html?id=16970017f81349548d0a9eead0ebba39 
      * 10.3.x - http://www.arcgis.com/home/item.html?id=75716d933f1c40a784243198e0dc11a1 

## Additional Documentation
* **Crash Analysis Toolbox - User Manual:** User Manual

## Developer Roadmap
* First Understand Dr. Khan's problem from a theoretical standpoint (take ArcGIS out of the equation)
* Learn Basics of ArcGIS (Check out Youtube Videos on)
      - What is the ArcGIS System, how is it used
      - What are the various data types in ArcGIS (geodatabases, feature classes, network layers)
      - How to add geographical data from a csv/excel file onto a map in ArcGIS
      - What are tools and toolboxes in ArcGIS
      - Understand what OpenStreetMap API is  
       - Program a simple tool in ArcMap
* Become a user for the existing tools: 
       - Learn how to use the tools, Read the User Manual for the tools, CONSULT WITH DR. KHAN on why he uses the tools if anything becomes unclear.
       - Learn Git and how to setup a repository with the existing code. 
* Study the existing code base and incrementally add features needed!


## Code Structure
* Each tool is contained into the Crash Analysis Toolbox
     - Crash Analysis Toolbox.pyt - the python code that defines the tool box
     - Crash Analysis Toolbox.Tool.pyt.xml - the xml file that contains the metadata + item descriptions of the toolbox.
* Each tool is defined in their own <<toolname>>.pyt for the classes of the each tool, the <<toolname>>.xml for their metadata + item descriptions. Some of the tools have helper classes. 

## Credits
* **Project Sponsor**:  <br />
 Ghazan Khan, Ph.D <br />
 Assistant Professor, Transportation Engineering <br />
 Department of Civil Engineering <br />
 CALIFORNIA STATE UNIVERSITY, SACRAMENTO <br />
 6000 J Street, Sacramento, CA 95819-6029 <br />

* **Development Team**: <br />
"Bus Drivers" - CSUS Computer Science Senior Project Team <br />
 CSC 190/191 - Fall 2015/Spring 2016  <br />
  Ben Botto <br />
  Kian Faroughi <br />
  Kenneth Spence <br />
  Victor Zepeda <br />
  Austin Purcell <br />
  Kevin Choe <br />

