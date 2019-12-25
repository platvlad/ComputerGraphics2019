#version 330 core

layout (location = 0) in vec3 position;
layout (location = 1) in vec3 normal;

uniform mat4 view;
uniform mat4 projection;

out vec3 Normal;
out vec3 worldCoords;

void main()
{
    gl_Position = projection * view * vec4(position, 1.0);
    Normal = normal;
    worldCoords = vec3(gl_Position);
}