#version 330 core

in vec3 Normal;
in vec3 worldCoords;
uniform vec3 lightPos;
uniform vec3 initialColor;
uniform float ambientStrength;

uniform float minThreshold;

out vec4 color;

float rand(vec2 co)
{
    return fract(sin(dot(co.xy ,vec2(12.9898,78.233))) * 43758.5453);
}

void main()
{
    color = vec4(Normal, 1.0f);
    float alpha = 1.0f;

    float distToThreshold = worldCoords.y - minThreshold;

    if (distToThreshold >= 0 && distToThreshold < 0.1f) {
        float randValue = rand(Normal.xy);
        if (randValue * distToThreshold  > 0.05f) {
            discard;
        }
    }
    if (worldCoords.y >= minThreshold + 0.1f) {
        discard;
    }

    float diffuseStrength = max(dot(normalize(lightPos - worldCoords), Normal), 0.0f);
    float strength = min(ambientStrength + 0.9f * diffuseStrength, 1.0f);
    color = vec4(initialColor * strength, alpha);
}
