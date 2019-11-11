#! /usr/bin/env python

"""
This script is written to check whether an object is able to contain sphere.
No physics about the cup is reasoned. This scrip only test the containability
This is written for cup imagination project.
@author: Hongtao Wu 
Nov 02, 2019
"""

import numpy as np
import pybullet as p
import pybullet_data
import time
import os
import math

sphere_urdf = "/home/hongtao/Dropbox/spirit-dictionary/dataset/general_object/sphere_mini.urdf"

class Containability(object):
    def __init__(self, obj_urdf, obj_zero_pos=[0, 0, 0], obj_zero_orn=[0, 0, 0], 
                 check_process=False, record_process=False):
        """
        Args:
        - obj_zero_orn: the start orientation of the object in Euler Angle
        - check_process: if set True, the process will be real time
        - record_process: if set True, the process will be recorded and saved as mp4 file
        """
        super(Containability, self).__init__()
        # Hyperparameter
        self.sphere_num = 225  # sphere number needs to be a 
        self.sphere_in_percentage_threshold = 0.2
        self.sphere_in_percentage = 0.0

        # Restitution
        self.sphere_restitution = 0.0
        self.object_restitution = 0.0
        self.plane_restitution = 0.0

        self.obj_urdf = obj_urdf
        self.containability = False

        # Simulation Parameter
        self.simulation_iteration = 1000
        self.save_mp4_dir = "/home/hongtao/Dropbox/spirit-dictionary/mp4"
        self.check_process = check_process
        self.record_process = record_process

        # Sphere Information
        self.sphere_id = []
        self.sphere_drop_orn = p.getQuaternionFromEuler([0, 0, 0])
        self.sphere_drop_pos = []
        self.sphere_in_drop_pos = []

        # Set the world
        physicsClient = p.connect(p.GUI)
        p.setGravity(0, 0, -10)

        p.setAdditionalSearchPath(pybullet_data.getDataPath())

        # Save mp4 video
        if self.record_process:
            today = time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime())
            mp4_file_name = today + "_retain_sphere_test.mp4"
            mp4_file_path = os.path.join(self.save_mp4_dir, mp4_file_name)
            p.startStateLogging(p.STATE_LOGGING_VIDEO_MP4, mp4_file_path)

        # Load plane
        self.plane_id = p.loadURDF("plane.urdf")
        p.changeDynamics(self.plane_id, -1, restitution=self.plane_restitution)

        # Load object
        obj_zero_pos = obj_zero_pos
        obj_zero_orn = p.getQuaternionFromEuler(obj_zero_orn)
        self.obj_id = p.loadURDF(self.obj_urdf, basePosition=obj_zero_pos, baseOrientation=obj_zero_orn, useFixedBase=True)
        p.changeDynamics(self.obj_id, -1, restitution=self.object_restitution)

        # Get the bounding box of the cup
        self.obj_curr_aabb = p.getAABB(self.obj_id)

        # Raise the object up
        if self.obj_curr_aabb[0][2] <= 0.1:
            p.resetBasePositionAndOrientation(self.obj_id, 
                    posObj=(0, 0, -self.obj_curr_aabb[0][2]+0.1),
                    ornObj=obj_zero_orn)
            self.obj_curr_aabb = p.getAABB(self.obj_id)

        # Reset debug camera postion
        p.resetDebugVisualizerCamera(2.0, 75, -50, [0, 0, 0.5])

        # Create constraint on the cup to fix its position
        constarin_Id = p.createConstraint(self.obj_id, -1, -1, -1, p.JOINT_FIXED, jointAxis=[0, 0, 0],
                parentFramePosition=[0, 0, 0], childFramePosition=obj_zero_pos,
                parentFrameOrientation=p.getQuaternionFromEuler([0, 0, 0]),
                childFrameOrientation=obj_zero_orn)


    def load_sphere(self):
        """ Load sphere before simulation. 
            Make sure that pybullet has already been connected before calling this function.             
        """

        # Set up sphere
        for i in range(self.sphere_num):
            sphere = p.loadURDF(sphere_urdf)
            p.changeDynamics(sphere, -1, restitution=self.sphere_restitution)

            self.sphere_id.append(sphere)

    
    def reset_sphere_drop(self, obj_curr_aabb):
        """ Get the sphere drop position around the obj_curr_aabb. This function is called after the set_sphere"""

        obj_aabb_xy_center = [(obj_curr_aabb[0][i] + obj_curr_aabb[1][i])/2 for i in range(2)]
        obj_aabb_xy_range = [abs(obj_curr_aabb[0][i] - obj_curr_aabb[1][i]) for i in range(2)]
        
        # Dropping from 1cm above the object
        sphere_drop_z = obj_curr_aabb[1][2] + 0.01

        sphere_per_length = math.sqrt(self.sphere_num/(obj_aabb_xy_range[0] * obj_aabb_xy_range[1]))

        x_sphere_num = math.floor(sphere_per_length * obj_aabb_xy_range[0])
        y_sphere_num = math.floor(sphere_per_length * obj_aabb_xy_range[1])

        sphere_drop_x = np.linspace(-obj_aabb_xy_range[0]/2, obj_aabb_xy_range[0]/2, x_sphere_num) + obj_aabb_xy_center[0]
        sphere_drop_y = np.linspace(-obj_aabb_xy_range[1]/2, obj_aabb_xy_range[1]/2, y_sphere_num) + obj_aabb_xy_center[1]

        # Reset the sphere_drop_pos
        self.sphere_drop_pos = []

        # Reset sphere position
        for i in range(self.sphere_num):
            y_idx = math.floor(i / x_sphere_num)
            x_idx = i % x_sphere_num

            try:
                sphere_start_pos = (sphere_drop_x[x_idx], sphere_drop_y[y_idx], sphere_drop_z)
            except:
                # For those out of range, position the sphere in a random xy in a higher layer
                sphere_start_pos = (obj_aabb_xy_center[0] + np.random.random() * obj_aabb_xy_range[0]/2, \
                                    obj_aabb_xy_center[1] + np.random.random() * obj_aabb_xy_range[1]/2, \
                                    sphere_drop_z + 0.05)
            
            self.sphere_drop_pos.append(sphere_start_pos)
            p.resetBasePositionAndOrientation(self.sphere_id[i], 
                    posObj=sphere_start_pos, 
                    ornObj=self.sphere_drop_orn)


    def checkincup(self, obj_curr_aabb):
        """ Get how many spheres are in the cup and the original position of the sphere
            Also, the drop pos of the in sphere will be updated to self.sphere_in_drop_pos
        """

        # Clear the sphere_in_drop_pos memory
        self.sphere_in_drop_pos = []

        # The center and range of the aabb. All scales are magnified by 100 times.
        obj_aabb_center = np.array([(obj_curr_aabb[0][i] + obj_curr_aabb[1][i])/2 for i in range(3)]) * 100
        obj_aabb_half_range = np.array([abs(obj_curr_aabb[0][i] - obj_curr_aabb[1][i]) for i in range(3)]) * 100 / 2

        for i in range(self.sphere_num):
            sphere_pos, _ = p.getBasePositionAndOrientation(self.sphere_id[i])
            sphere_pos = np.array(sphere_pos) * 100
            
            distance_to_center = np.absolute(sphere_pos - obj_aabb_center)
            in_box = distance_to_center < obj_aabb_half_range

            if np.all(in_box):
                # print("x: %.2f" % x, "y: %.2f" % y, "z: %.2f" % z)
                self.sphere_in_drop_pos.append(np.copy(self.sphere_drop_pos[i]))

        return len(self.sphere_in_drop_pos)


    def get_containability(self):
        """ Test the pouring of sphere and check how many sphere remains after pouring. """
        # Load sphere
        self.load_sphere()
        # Reset sphere position
        self.reset_sphere_drop(self.obj_curr_aabb)

        ########################### Drop Sphere Into ############################

        for i in range(self.simulation_iteration):
            p.stepSimulation()

            if self.check_process:
                time.sleep(1. / 240.)

            if i == int(1 * self.simulation_iteration / 5):
                # Check the number of sphere in the bbox before moving the sphere away
                sphere_in_num = self.checkincup(self.obj_curr_aabb)

            if i > int(1 * self.simulation_iteration / 5) and i < int(1 * self.simulation_iteration / 2):
                horizontal_field_strength = 5 + 5 * math.sin(math.pi / 2 * (i - int(self.simulation_iteration / 5)) / int(3 * self.simulation_iteration / 10))
                p.setGravity(horizontal_field_strength, horizontal_field_strength, -10)

            elif i >= int(1 * self.simulation_iteration / 2) and i < int(3 * self.simulation_iteration / 5):
                p.setGravity(10, 10, -10)

            elif i >= int(3 * self.simulation_iteration / 5) and i < int(9 * self.simulation_iteration / 10):
                horizontal_field_strength = -5 - 5 * math.sin(math.pi / 2 * (i - int(3 * self.simulation_iteration / 5)) / int(3 * self.simulation_iteration / 10))
                p.setGravity(horizontal_field_strength, horizontal_field_strength, -10)

            elif i >= int(9 * self.simulation_iteration / 10):
                p.setGravity(-10, -10, -10)


        ########## 2.0 Version of checking sphere ##########
        # Check the x, y, z coordinate of the sphere w.r.t to the x, y, z coordinate of the cup
        sphere_in_box_num = self.checkincup(self.obj_curr_aabb)
        print("Number of sphere in box: ", sphere_in_box_num)

        # Calculate how many percentage of the spheres are in the cup
        sphere_num_percentage = sphere_in_box_num / self.sphere_num

        # Disconnect the 
        p.disconnect()

        if sphere_num_percentage > self.sphere_in_percentage_threshold:
            print("#####################################")
            print("THIS IS A CONTAINER! The sphere in percentage is: {}".format(sphere_num_percentage))
            print("#####################################")
            self.containability = True

        else:
            print("/////////////////////////////////////")
            print("THIS IS NOT A CONTAINER!The sphere in percentage is: {}".format(sphere_num_percentage))
            print("/////////////////////////////////////")
            self.containability = False
        
        return self.containability


# Test
if __name__ == "__main__":

    # Object information
    obj_name = "cup_0003"
    obj_urdf = "/home/hongtao/Dropbox/spirit-dictionary/dataset/cup_imagine/cup_physical_properties/" + \
    str(obj_name) + "/" + str(obj_name) + ".urdf"

    C = Containability(obj_urdf, obj_zero_pos=[0, 0, 1], obj_zero_orn=[math.pi/2, 0, 0])

    containable_affordance = C.get_containability()