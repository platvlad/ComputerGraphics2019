import glm
import math


class CameraController:
    def __init__(self, camera_pos):
        self.dragging = False
        self.last_screen_coords = [0, 0]
        self.camera_pos = camera_pos
        self.up_direction = glm.vec3(0.0, 1.0, 0.0)
        self.view = glm.lookAt(self.camera_pos, glm.vec3(0.0, 0.0, 0.0), self.up_direction)
        self.yaw = 0
        self.pitch = 0
        self.distance = glm.length(camera_pos)
        self.sensitivity = 0.4

    def __update_view(self):
        self.__update_camera_pos()
        self.view = glm.lookAt(self.camera_pos, glm.vec3(0.0, 0.0, 0.0), self.up_direction)

    def __update_camera_pos(self):
        x = self.distance * math.cos(glm.radians(self.pitch)) * math.sin(glm.radians(self.yaw))
        y = self.distance * math.sin(glm.radians(self.pitch))
        z = self.distance * math.cos(glm.radians(self.pitch)) * math.cos(glm.radians(self.yaw))
        self.camera_pos = glm.vec3(x, y, z)

    def update_position(self, screen_coords):
        offset = [screen_coords[0] - self.last_screen_coords[0], self.last_screen_coords[1] - screen_coords[1]]
        new_yaw = self.yaw - offset[0] * self.sensitivity
        new_pitch = self.pitch - offset[1] * self.sensitivity

        pitch_min = min(self.pitch, new_pitch)
        pitch_max = max(self.pitch, new_pitch)
        if (pitch_min <= 90) and (pitch_max > 90) or (pitch_min <= 270) and (pitch_max > 270):
            self.up_direction *= -1
        self.yaw = new_yaw % 360
        self.pitch = new_pitch % 360
        self.last_screen_coords = screen_coords
        self.__update_view()

    def change_dist(self, factor):
        self.distance *= factor
        self.__update_view()