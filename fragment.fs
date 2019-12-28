#version 330 core

in vec3 Normal;
in vec3 worldCoords;
uniform vec3 lightPos;
uniform vec3 initialColor;
uniform float ambientStrength;


out vec4 color;

void main()
{
    float diffuseStrength = max(dot(normalize(lightPos - worldCoords), Normal), 0.0f);
    float strength = min(ambientStrength + 0.9f * diffuseStrength, 1.0f);
    color = vec4(initialColor * strength, 1.0);
}
