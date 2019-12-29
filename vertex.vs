#version 330 core

layout (location = 0) in vec3 position;
layout (location = 1) in vec3 normal;

uniform mat4 view;
uniform mat4 projection;
uniform mat4 lightView;
uniform mat4 lightProjection;

out vec3 Normal;
out vec3 worldCoords;

out vec4 lightRelPos;

out float dist;

void main()
{
    gl_Position = projection * view * vec4(position, 1.0);
    Normal = normal;
    worldCoords = vec3(gl_Position);
    lightRelPos = lightProjection * lightView * vec4(position, 1.0);
    dist = -lightView[3][2] + 1;
    lightRelPos = lightRelPos / dist;
}