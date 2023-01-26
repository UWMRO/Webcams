""" webcam_handler.py [camera definition file]

Requests and archives webcam images, then and forwards the latest to a remote server. 
Uses Pycurl to retrieve images via http, Paramiko to push them to the server via ssh.

Camera definition file format is:

      name URL username password

The URL is the specific call that returns a single image. Note that the
naming convention assumes images come in slower than once per second.

Original by Matt Armstrong (~'17-'18)
modified for direct access to webcams by OJF '19
modified for simplifying code by Midori Rollins '22

Note: Will fail if:
- the archive directory doesn't exist
- if the camera definition file has blank lines

ToDo: Exceptions don't print or pass their exceptions up
"""

import os, shutil, subprocess, glob, time, sys
import pycurl # retrieve
from paramiko import SSHClient
from datetime import datetime

class WebCam:
    """ Object to represent one of the webcams at MRO """

    def __init__(self, name, URL, userName, password=None):
        self.name = name
        self.URL = URL
        self.userName = userName
        self.password = password
        self.lastImage = None

    def retrieve_and_archive_image(self, savePath):
        """ Request (via http) and save current image. Returns full path to new image. """

        imagePath = savePath + "/" + self.name + "_" + datetime.now().strftime("%m%d_%H%M%S") + '.jpg'
        with open(imagePath, 'wb') as f:
            c = pycurl.Curl()
            c.setopt( c.URL, self.URL)
            if self.password:
                c.setopt( c.USERPWD, self.userName + ":" + self.password )
            else:
                c.setopt( c.USERPWD, self.userName )
            c.setopt( c.WRITEDATA, f )
            try:
                c.perform()
            except:
                print( "Error retrieving image from", self.name )
            else:
                self.lastImage = imagePath
            c.close()


    
if __name__ == "__main__":

    try:
        camera_definition_file = sys.argv[1]
    except IndexError as e:
        print( "Usage:", sys.argv[0], "[camera definition file]")
        exit()

    #archivePath = "/home/ojf/Pictures/MRO_Webcams/"
    archivePath = "/Users/ramid/Downloads/"
    remotePath = 'public_html/webcams/'
    remoteHost = 'ovid.u.washington.edu'
    user = 'mrouser'
    cameras = []  # list of all WebCam objects

    
    FILE = open(camera_definition_file)
    for line in FILE:
        if line[0] == '#':
            continue
        cameras.append( WebCam(*line.split()) ) # *args "unwraps" the list from split()
    for camera in cameras:
            print( "Read in camera", camera.name )
            print( camera.URL, " ", camera.userName, " ", camera.password )


    while True:

        """ Check for correct daily folder in archive, then save an image from each camera. """
        path = archivePath + datetime.now().strftime("%Y%m%d")

        if os.path.exists( path + "/" ) == False:
            try:
                os.mkdir( path )
            except Exception as e:
                sys.exit( "Error creating ", path, ": ", e )


        for camera in cameras:
            #camera.retrieve_and_archive_image(path)
            print( datetime.now().strftime("%m/%d %H:%M"), ": image archived from", camera.name )


        """ Push images to remote server. """
        ssh = SSHClient()
        ssh.load_system_host_keys()
        # ssh.connect(remoteHost, username=user)
        # sftp = ssh.open_sftp()
            
        for camera in cameras:
            if camera.lastImage:
                #sftp.put(camera.lastImage, remotePath + camera.name + ".jpg")
                print( datetime.now().strftime("%m/%d %H:%M"), ": Posted image from", camera.name )
        # sftp.close()
        ssh.close()


        for i in range(300,-1,-1):
            sys.stdout.write('\r')
            sys.stdout.write('Sleeping: %02d seconds remaining' %i)
            sys.stdout.flush()
            time.sleep(1)
        print( '\r\n' )