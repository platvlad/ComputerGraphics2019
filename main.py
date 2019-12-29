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
        self.vertex_array, self.face_array = get_vert_faces(path)
        glutInit()
        glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
        self.width = 640
        self.height = 480
        glutInitWindowSize(self.width, self.height)
        glutCreateWindow(b"Viewer")
        self.VAO = glGenVertexArrays(1)
        self.VBO = glGenBuffers(1)

        self.light_program = glCreateProgram()
        self.link_program_shaders(self.light_program, 'light_vertex.vs', 'light_fragment.fs')

        glBindVertexArray(self.VAO)
        self.set_main_array_object()

        self.configure_shadow_FBO()

        glutDisplayFunc(self.draw)
        glutIdleFunc(self.draw)
        glutMotionFunc(self.motion)
        glutMouseFunc(self.mouse)
        camera_pos = glm.vec3(0, 0, 2)
        self.projection = glm.perspective(45, self.width / self.height, 0.1, 100)
        self.cam_controller = CameraController(camera_pos)
        self.setup_light()
        glBindVertexArray(0)
        self.min_threshold = 1.0
        self.growing = False

    def configure_shadow_FBO(self):
        glUseProgram(self.light_program)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 24, None)
        glEnableVertexAttribArray(0)
        self.shadow_width = 1024
        self.shadow_height = 1024
        self.depth_FBO = glGenFramebuffers(1)
        self.depth_map = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.depth_map)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_DEPTH_COMPONENT, self.shadow_width, self.shadow_height, 0, GL_DEPTH_COMPONENT,
                     GL_FLOAT, None)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
        glBindFramebuffer(GL_FRAMEBUFFER, self.depth_FBO)
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, GL_TEXTURE_2D, self.depth_map, 0)
        glDrawBuffer(GL_NONE)
        glReadBuffer(GL_NONE)
        glEnable(GL_DEPTH_TEST)
        glBindFramebuffer(GL_FRAMEBUFFER, 0)

    def bind_vbo_ebo(self):
        glBindBuffer(GL_ARRAY_BUFFER, self.VBO)
        glBufferData(GL_ARRAY_BUFFER, self.vertex_array.nbytes, self.vertex_array, GL_STATIC_DRAW)

        EBO = glGenBuffers(1)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, EBO)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, self.face_array.nbytes, self.face_array, GL_STATIC_DRAW)

    def link_program_shaders(self, program, vertex_shader_file, fragment_shader_file):
        vertex_shader = Viewer.create_shader(GL_VERTEX_SHADER, vertex_shader_file)
        fragment_shader = Viewer.create_shader(GL_FRAGMENT_SHADER, fragment_shader_file)
        glAttachShader(program, vertex_shader)
        glAttachShader(program, fragment_shader)
        glLinkProgram(program)
        glDeleteShader(vertex_shader)
        glDeleteShader(fragment_shader)

    def set_main_array_object(self):
        self.bind_vbo_ebo()

        self.program = glCreateProgram()
        self.link_program_shaders(self.program, 'vertex.vs', 'fragment.fs')
        glUseProgram(self.program)
        glEnable(GL_DEPTH_TEST)

        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 24, None)
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 24, ctypes.c_void_p(12))
        glEnableVertexAttribArray(1)

    @staticmethod
    def set_var(program, name, var, set_method=glUniform1f):
        location = glGetUniformLocation(program, name)
        set_method(location, var)

    @staticmethod
    def set_matr(program, name, var, set_method=glUniformMatrix4fv):
        location = glGetUniformLocation(program, name)
        set_method(location, 1, GL_FALSE, var)

    @staticmethod
    def set_vector(program, name, var, set_method=glUniform3fv):
        location = glGetUniformLocation(program, name)
        set_method(location, 1, var)

    def setup_light(self):
        near_plane = 0.1
        far_plane = 100
        light_projection = glm.perspective(glm.radians(90), self.shadow_width / self.shadow_height, near_plane,
                                           far_plane)
        light_pos = glm.vec3(-2, 0, 0.2)
        light_view = glm.lookAt(light_pos, glm.vec3(0.0, 0.0, 0.0), glm.vec3(0, 1, 0))

        Viewer.set_matr(self.light_program, 'view', glm.value_ptr(light_view))
        Viewer.set_matr(self.light_program, 'projection', glm.value_ptr(light_projection))

        glUseProgram(self.program)

        Viewer.set_matr(self.program, 'lightView', glm.value_ptr(light_view))
        Viewer.set_matr(self.program, 'lightProjection', glm.value_ptr(light_projection))
        Viewer.set_vector(self.program, 'lightPos', glm.value_ptr(light_pos))

        Viewer.set_var(self.program, 'nearPlane', near_plane)
        Viewer.set_var(self.program, 'farPlane', far_plane)
        Viewer.set_var(self.program, 'depthMap', 0, glUniform1i)

        initial_color = glm.vec3(1.0, 0.5, 0.2)
        Viewer.set_vector(self.program, 'initialColor', glm.value_ptr(initial_color))
        Viewer.set_var(self.program, 'ambientStrength', 0.1)

    def show(self):
        glutMainLoop()

    def draw(self):
        glBindVertexArray(self.VAO)
        glBindFramebuffer(GL_FRAMEBUFFER, self.depth_FBO)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glViewport(0, 0, self.shadow_width, self.shadow_height)
        glUseProgram(self.light_program)
        glActiveTexture(GL_TEXTURE0)

        glDrawElements(GL_TRIANGLES, len(self.face_array), GL_UNSIGNED_INT, None)
        glBindFramebuffer(GL_FRAMEBUFFER, 0)
        glUseProgram(self.program)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glViewport(0, 0, self.width, self.height)

        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, self.depth_map)

        Viewer.set_matr(self.program, 'view', glm.value_ptr(self.cam_controller.view))
        Viewer.set_matr(self.program, 'projection', glm.value_ptr(self.projection))
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
        Viewer.set_matr(self.program, 'view', glm.value_ptr(self.cam_controller.view))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        mesh_file = 'models/bunny_wall.obj'
    else:
        mesh_file = sys.argv[1]
    viewer = Viewer(mesh_file)
    viewer.show()
