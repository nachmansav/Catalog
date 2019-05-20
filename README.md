# Project overview:
This is a project for the Udacity Full Stack Web Developer nanodegree program. The project is to build a RESTful web application using Python and the Flask framework along with implementing third-party OAuth authentication and a database for persistent storage.
## Details:
This project is a dynamic, RESTful web application where users can share recipes online. It demonstrates the basics of CRUD (create, read, update, delete) operations. It runs on Pyhton with the Flask framework. It utilizes SQLAlchemy to manage the database. Bootstrap is used to style the front end.
It features Google's OAuth 2.0 authentication so that users can login and out. 
Only users that are logged in can create a new recipe. Logged-in users are only able to edit or delete the recipes that they created. There are also public versions of the main pages so that a user that is not logged-in can still view all of the recipes present. The application stores and displays each recipe according to the category that it was created with.
## Instructions for running the code:
Update: the code is running here: http://www.52.59.212.112.xip.io/
The following are the original running instructions:
1. Download and install [Vagrant](https://www.vagrantup.com/) and [VirtualBox](https://www.virtualbox.org/).
2. Download the following Udacity [folder](https://d17h27t6h515a5.cloudfront.net/topher/2017/August/59822701_fsnd-virtual-machine/fsnd-virtual-machine.zip) which contains preconfigured vagrant settings.
3. Clone this repository.
5. Navigate to the Udacity folder using the command line interface and inside that, cd into the vagrant directory.
6. Launch the virtual machine with the command 'vagrant up'.
7. Once Vagrant installs the necessary files use 'vagrant ssh' to connect to the virtual machine.
8. Cd into the '/vagrant' folder.
9. Copy the contents of this repository to this directory.
10. Cd into the new directory.
10. Use the command 'python project.py' to run the python program.
11. Connect to the application by opening a browser and going to 'http://localhost:5000/'



