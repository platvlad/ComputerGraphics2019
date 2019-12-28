from OpenGL.GL import *
from OpenGL.GLUT import *
import pywavefront as pwf
import numpy as np
import glm
from Camera import CameraController


def normalize(vertices):
    max_elem = np.max(np.abs(vertices))
    if max_elem > 0:
        vertices /= (1.1 * max_elem)


def get_normals(vertices, faces):
    normals = np.zeros(shape=np.shape(vertices), dtype=np.float32)
    for face in faces:
        i0 = face[0]
        i1 = face[1]
        i2 = face[2]
        v0 = vertices[i0]
        v1 = vertices[i1]
        v2 = vertices[i2]
        v01 = v1 - v0
        v12 = v2 - v1
        normal = np.cross(v01, v12)
        normals[i0] += normal
        normals[i1] += normal
        normals[i2] += normal
    for i in range(len(normals)):
        norm_length = np.linalg.norm(normals[i])
        if norm_length > 0:
            normals[i] /= norm_length
    return normals


def get_vert_faces(path):
    mesh = pwf.Wavefront(path, create_materials=True, collect_faces=True)
    vertices = np.asarray(mesh.vertices, dtype=np.float32)
    normalize(vertices)
    faces = np.asarray(mesh.mesh_list[0].faces)
    normals = get_normals(vertices, faces)
    vertices = np.concatenate((vertices, normals), axis=1)
    face_array = faces.flatten()
    vertex_array = vertices.flatten()
    return vertex_array, face_array

class Viewer:
    def __init__(self, path):
        vertex_array, self.face_array = get_vert_faces(path)
        glutInit()
        glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
        self.width = 640
        self.height = 480
        glutInitWindowSize(self.width, self.height)
        glutCreateWindow(b"Viewer")
        self.VAO = glGenVertexArrays(1)
        glBindVertexArray(self.VAO)

        VBO = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, VBO)
        glBufferData(GL_ARRAY_BUFFER, vertex_array.nbytes, vertex_array, GL_STATIC_DRAW)

        EBO = glGenBuffers(1)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, EBO)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, self.face_array.nbytes, self.face_array, GL_STATIC_DRAW)

        vertex_shader = Viewer.create_shader(GL_VERTEX_SHADER, 'vertex.vs')
        fragment_shader = Viewer.create_shader(GL_FRAGMENT_SHADER, 'fragment.fs')
        self.program = glCreateProgram()
        glAttachShader(self.program, vertex_shader)
        glAttachShader(self.program, fragment_shader)
        glLinkProgram(self.program)
        glUseProgram(self.program)
        glDeleteShader(vertex_shader)
        glDeleteShader(fragment_shader)
        glEnable(GL_DEPTH_TEST)

        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 24, None)
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 24, ctypes.c_void_p(12))
        glEnableVertexAttribArray(1)
        glBindVertexArray(0)
        glutDisplayFunc(self.draw)
        glutIdleFunc(self.draw)
        glutMotionFunc(self.motion)
        glutMouseFunc(self.mouse)
        camera_pos = glm.vec3(0, 0, 2)
        self.projection = glm.perspective(45, self.width / self.height, 0.1, 100)
        self.cam_controller = CameraController(camera_pos)
        self.setup_light()
        self.min_threshold = 1.0
        self.growing = False

    def setup_light(self):
        light_pos_location = glGetUniformLocation(self.program, 'lightPos')
        light_pos = glm.vec3(-2, 0, 0)
        initial_color = glm.vec3(1.0, 0.5, 0.2)
        glUniform3fv(light_pos_location, 1, glm.value_ptr(light_pos))
        initial_color_location = glGetUniformLocation(self.program, 'initialColor')
        glUniform3fv(initial_color_location, 1, glm.value_ptr(initial_color))
        ambient_strength_location = glGetUniformLocation(self.program, 'ambientStrength')
        glUniform1f(ambient_strength_location, 0.1)

    def show(self):
        glutMainLoop()

    def draw(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glBindVertexArray(self.VAO)
        view_location = glGetUniformLocation(self.program, 'view')
        projection_location = glGetUniformLocation(self.program, 'projection')

        glUniformMatrix4fv(view_location, 1, GL_FALSE, glm.value_ptr(self.cam_controller.view))
        glUniformMatrix4fv(projection_location, 1, GL_FALSE, glm.value_ptr(self.projection))

        glDrawElements(GL_TRIANGLES, len(self.face_array), GL_UNSIGNED_INT, None)

        glBindVertexArray(0)
        glutSwapBuffers()

    @staticmethod
    def create_shader(shader_type, shader_file_name):
        with open(shader_file_name, 'r') as shader_file:
            vert_shader_text = shader_file.read()
            shader = glCreateShader(shader_type)
            glShaderSource(shader, vert_shader_text)
            glCompileShader(shader)
            return shader

    def mouse(self, button, state, x, y):
        if state == 0:
            self.cam_controller.dragging = True
            self.cam_controller.last_screen_coords = [x, y]
        if state == 1:
            self.cam_controller.dragging = False
        if button == 3:
            self.cam_controller.change_dist(1.01)
        if button == 4:
            self.cam_controller.change_dist(0.99)

    def motion(self, x, y):
        self.cam_controller.update_position([x, y])
        view_location = glGetUniformLocation(self.program, 'view')
        glUniformMatrix4fv(view_location, 1, GL_FALSE, glm.value_ptr(self.cam_controller.view))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        mesh_file = 'models/bunny.obj'
    else:
        mesh_file = sys.argv[1]
    viewer = Viewer('models/bunny.obj')
    viewer.show()
